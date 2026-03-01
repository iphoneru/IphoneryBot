import os
import json
import time
import logging
from collections import defaultdict, deque
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Iphonery Jivo Bot")

openai_client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

# ---------- In-memory context storage (max 20 messages per chat) ----------
# Key: chat_id -> deque of {"role": ..., "content": ...}
chat_histories: dict[str, deque] = defaultdict(lambda: deque(maxlen=20))

# ---------- Load system prompt ----------
def load_prompt() -> str:
    prompt_path = os.path.join(os.path.dirname(__file__), "prompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

SYSTEM_PROMPT = load_prompt()

# ---------- OpenAI tools definition ----------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "transfer_to_agent",
            "description": (
                "Transfer the conversation to a human operator. "
                "Call this when: the client explicitly asks for a human agent; "
                "the question is too complex or sensitive; you cannot find the answer; "
                "the client is upset or dissatisfied; the question concerns an ongoing order status "
                "or a specific complaint that requires account access."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Brief reason why the transfer is needed (for internal log)"
                    }
                },
                "required": ["reason"]
            }
        }
    }
]


async def get_ai_response(chat_id: str, user_message: str) -> tuple[str | None, bool]:
    """
    Returns (reply_text, transfer_to_agent).
    If transfer_to_agent is True, reply_text may contain a farewell message.
    """
    history = chat_histories[chat_id]
    history.append({"role": "user", "content": user_message})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + list(history)

    try:
        response = await openai_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=1024,
            temperature=0.4,
        )
    except Exception as e:
        logger.error("OpenAI error: %s", e)
        return None, True  # Transfer to agent on error

    choice = response.choices[0]

    # Check if the model wants to call transfer_to_agent
    if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
        for tool_call in choice.message.tool_calls:
            if tool_call.function.name == "transfer_to_agent":
                try:
                    args = json.loads(tool_call.function.arguments)
                    reason = args.get("reason", "")
                except Exception:
                    reason = ""
                logger.info("Transfer to agent for chat_id=%s, reason: %s", chat_id, reason)
                # Add assistant turn to history so context is preserved if agent re-opens
                history.append({
                    "role": "assistant",
                    "content": "[Transferred to agent]"
                })
                return None, True

    # Normal text reply
    reply = choice.message.content or ""
    history.append({"role": "assistant", "content": reply})
    return reply, False


# ---------- Jivo Bot API webhook ----------
@app.post("/arb66O7Pbq")
async def jivo_webhook(request: Request):
    try:
        body = await request.json()
    except Exception:
        return Response(status_code=400)

    logger.info("Jivo incoming: %s", json.dumps(body, ensure_ascii=False)[:500])

    event_name = body.get("event", "")

    # ---- CLIENT_MESSAGE: main bot logic ----
    if event_name == "CLIENT_MESSAGE":
        chat_id = str(body.get("chat_id", ""))
        message = body.get("message", {})
        msg_type = message.get("type", "TEXT")

        # Only handle text messages
        if msg_type != "TEXT":
            return JSONResponse({"event": "BOT_MESSAGE", "message": {
                "type": "TEXT",
                "text": "Lo siento, solo puedo procesar mensajes de texto. ¿Puedo ayudarte con algo?",
                "timestamp": int(time.time())
            }})

        user_text = message.get("text", "").strip()
        if not user_text:
            return Response(status_code=200)

        reply_text, transfer = await get_ai_response(chat_id, user_text)

        if transfer:
            # Tell Jivo to assign a human agent
            return JSONResponse({"event": "ASSIGN_AGENT"})

        return JSONResponse({
            "event": "BOT_MESSAGE",
            "message": {
                "type": "TEXT",
                "text": reply_text,
                "timestamp": int(time.time())
            }
        })

    # ---- CHAT_CLOSED: clean up history ----
    if event_name in ("CHAT_CLOSED", "CHAT_FINISHED"):
        chat_id = str(body.get("chat_id", ""))
        if chat_id in chat_histories:
            del chat_histories[chat_id]
        return Response(status_code=200)

    # All other events — acknowledge
    return Response(status_code=200)


# ---------- Health check ----------
@app.get("/health")
async def health():
    return {"status": "ok"}
