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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Iphonery Jivo Bot")

openai_client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

JIVO_BOT_ENDPOINT = os.getenv(
    "JIVO_BOT_ENDPOINT",
    "https://bot.jivosite.com/webhooks/4xMrS387N2hl2fF/arb66O7Pbq"
)

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
                "Call this when: the client explicitly asks for a human; "
                "the question is about a specific ongoing order; "
                "the client is upset or dissatisfied; "
                "the question is outside your knowledge base; "
                "there is a complaint about a received product; "
                "bulk/B2B inquiry; "
                "you cannot find a satisfactory answer after 2-3 attempts."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Brief reason for the transfer (internal log only)"
                    }
                },
                "required": ["reason"]
            }
        }
    }
]


async def send_to_jivo(payload: dict) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.post(
                JIVO_BOT_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            logger.info("Jivo response: %s %s", r.status_code, r.text[:200])
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
    logger.info("Sending BOT_MESSAGE to Jivo: chat_id=%s", chat_id)
    await send_to_jivo(payload)


async def jivo_invite_agent(chat_id: str, client_id: str) -> None:
    payload = {
        "id": str(uuid.uuid4()),
        "client_id": str(client_id),
        "chat_id": str(chat_id),
        "event": "INVITE_AGENT"
    }
    logger.info("Sending INVITE_AGENT to Jivo: chat_id=%s", chat_id)
    await send_to_jivo(payload)


async def get_ai_response(chat_id: str, user_message: str) -> tuple[str | None, bool]:

    history = chat_histories[chat_id]
    history.append({"role": "user", "content": user_message})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + list(history)

    try:
        response = await openai_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=1024,
            temperature=0.4,
        )
    except Exception as e:
        logger.error("OpenAI API error: %s", e)
        return None, True  # On error → transfer to agent

    choice = response.choices[0]

    if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
        for tool_call in choice.message.tool_calls:
            if tool_call.function.name == "transfer_to_agent":
                try:
                    args = json.loads(tool_call.function.arguments)
                    reason = args.get("reason", "n/a")
                except Exception:
                    reason = "n/a"
                logger.info("AI requested INVITE_AGENT. chat_id=%s reason=%s", chat_id, reason)
                history.append({"role": "assistant", "content": "[transferred to agent]"})
                return None, True

    reply = choice.message.content or ""
    history.append({"role": "assistant", "content": reply})
    return reply, False


async def process_and_reply(chat_id: str, client_id: str, user_text: str) -> None:
    reply_text, should_transfer = await get_ai_response(chat_id, user_text)

    if should_transfer:
        await jivo_invite_agent(chat_id, client_id)
    else:
        await jivo_send_message(chat_id, client_id, reply_text)


@app.post("/4xMrS387N2hl2fF")
async def jivo_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
    except Exception:
        return Response(status_code=400)

    event = body.get("event", "")
    chat_id = str(body.get("chat_id", ""))
    client_id = str(body.get("client_id", ""))

    logger.info(
        "Jivo event=%s chat_id=%s client_id=%s",
        event, chat_id, client_id
    )

    if event == "CLIENT_MESSAGE":
        message = body.get("message", {})
        msg_type = message.get("type", "TEXT")
        user_text = message.get("text", "").strip()

        if msg_type != "TEXT" or not user_text:
            return Response(status_code=200)

        background_tasks.add_task(process_and_reply, chat_id, client_id, user_text)

        return Response(status_code=200)

    if event in ("AGENT_JOINED", "CHAT_CLOSED"):
        if chat_id in chat_histories:
            del chat_histories[chat_id]
            logger.info("Cleared history for chat_id=%s (event=%s)", chat_id, event)
        return Response(status_code=200)

    if event == "AGENT_UNAVAILABLE":
        # Bot takes over and asks client to leave contacts
        await jivo_send_message(
            chat_id, client_id,
            "Unfortunately, all agents are currently busy. "
            "Please email us at info@iphonery.com "
            "or WhatsApp/call +34 602 040 012 — we will reply as soon as possible. 🙏"
        )
        return Response(status_code=200)

    return Response(status_code=200)


# ── Health check ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}
