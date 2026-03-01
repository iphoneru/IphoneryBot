import os
import json
import time
import uuid
import logging
from collections import defaultdict, deque

import httpx
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import Response
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Iphonery Jivo Bot")
client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

JIVO_BOT_ENDPOINT = os.getenv(
    "JIVO_BOT_ENDPOINT",
    "https://bot.jivosite.com/webhooks/4xMrS387N2hl2fF/arb66O7Pbq"
)

MAIN_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")

chat_histories: dict[str, deque] = defaultdict(lambda: deque(maxlen=20))


def load_prompt() -> str:
    path = os.path.join(os.path.dirname(__file__), "prompt.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

SYSTEM_PROMPT = load_prompt()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "transfer_to_agent",
            "description": (
                "Transfer the conversation to a human operator. "
                "Call this ONLY when the client explicitly asks to speak with a human, "
                "operator, manager or agent. Example phrases: "
                "'connect me to an operator', 'I want to talk to a person', "
                "'speak with support', 'human please'. "
                "Do NOT call this for any question — always try to answer first."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string"}
                },
                "required": ["reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": (
                "Search iphonery.com for information when the answer is not in your knowledge base. "
                "Use for specific product specs, current prices, stock, or anything you are unsure about."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question or topic to search for"
                    }
                },
                "required": ["query"]
            }
        }
    }
]


async def do_site_search(query: str) -> str:
    """Search iphonery.com using the built-in web_search tool in Responses API."""
    try:
        response = await client.responses.create(
            model=MAIN_MODEL,
            tools=[{"type": "web_search"}],
            input=f"Ищи инфу на сайте https://iphonery.com/ Вопрос: {query}",
        )
        return response.output_text or "No results found."
    except Exception as e:
        logger.error("Site search error: %s", e)
        return "Search failed."


async def get_ai_response(chat_id: str, user_message: str) -> tuple[str | None, bool]:
    history = chat_histories[chat_id]
    history.append({"role": "user", "content": user_message})

    for _ in range(3):
        messages = list(history)

        try:
            response = await client.responses.create(
                model=MAIN_MODEL,
                instructions=SYSTEM_PROMPT,
                input=messages,
                tools=TOOLS,
                tool_choice="auto",
                max_output_tokens=1024,
            )
        except Exception as e:
            logger.error("OpenAI error: %s", e)
            return None, True

        # Check output items for tool calls
        tool_calls_found = False
        for item in response.output:
            if item.type == "function_call":
                tool_calls_found = True
                fn = item.name

                if fn == "transfer_to_agent":
                    try:
                        reason = json.loads(item.arguments).get("reason", "n/a")
                    except Exception:
                        reason = "n/a"
                    logger.info("INVITE_AGENT chat_id=%s reason=%s", chat_id, reason)
                    history.append({"role": "assistant", "content": "[transferred to agent]"})
                    return None, True

                if fn == "search_web":
                    try:
                        query = json.loads(item.arguments).get("query", user_message)
                    except Exception:
                        query = user_message
                    logger.info("SEARCH chat_id=%s query=%s", chat_id, query)
                    search_result = await do_site_search(query)

                    # Add assistant tool call + tool result to history for next iteration
                    history.append({"role": "assistant", "content": f"[search: {query}]"})
                    history.append({"role": "user", "content": f"Search result: {search_result}"})

        if tool_calls_found:
            continue

        # Normal text reply
        reply = (response.output_text or "").strip()
        if not reply:
            return None, True

        history.append({"role": "assistant", "content": reply})
        return reply, False

    return None, True


async def process_and_reply(chat_id: str, client_id: str, user_text: str) -> None:
    reply_text, should_transfer = await get_ai_response(chat_id, user_text)
    if should_transfer:
        await jivo_invite_agent(chat_id, client_id)
    else:
        await jivo_send_message(chat_id, client_id, reply_text)


async def send_to_jivo(payload: dict) -> None:
    async with httpx.AsyncClient(timeout=10) as http:
        try:
            r = await http.post(
                JIVO_BOT_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            logger.info("Jivo response: %s | %s", r.status_code, r.text[:300])
        except Exception as e:
            logger.error("Error sending to Jivo: %s", e)


async def jivo_send_message(chat_id: str, client_id: str, text: str) -> None:
    payload = {
        "id": str(uuid.uuid4()),
        "client_id": str(client_id),
        "chat_id": str(chat_id),
        "event": "BOT_MESSAGE",
        "message": {
            "type": "TEXT",
            "text": text,
            "timestamp": int(time.time())
        }
    }
    logger.info("BOT_MESSAGE chat_id=%s | %s", chat_id, text[:100])
    await send_to_jivo(payload)


async def jivo_invite_agent(chat_id: str, client_id: str) -> None:
    payload = {
        "id": str(uuid.uuid4()),
        "client_id": str(client_id),
        "chat_id": str(chat_id),
        "event": "INVITE_AGENT"
    }
    logger.info("INVITE_AGENT sent chat_id=%s", chat_id)
    await send_to_jivo(payload)


@app.post("/4xMrS387N2hl2fF")
async def jivo_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
    except Exception:
        return Response(status_code=400)

    event = body.get("event", "")
    chat_id = str(body.get("chat_id", ""))
    client_id = str(body.get("client_id", ""))

    logger.info("Jivo event=%s chat_id=%s client_id=%s", event, chat_id, client_id)

    if event == "CLIENT_MESSAGE":
        message = body.get("message", {})
        user_text = message.get("text", "").strip()
        if message.get("type") != "TEXT" or not user_text:
            return Response(status_code=200)
        background_tasks.add_task(process_and_reply, chat_id, client_id, user_text)
        return Response(status_code=200)

    if event in ("AGENT_JOINED", "CHAT_CLOSED"):
        chat_histories.pop(chat_id, None)
        logger.info("History cleared chat_id=%s", chat_id)
        return Response(status_code=200)

    return Response(status_code=200)


@app.get("/health")
async def health():
    return {"status": "ok"}
