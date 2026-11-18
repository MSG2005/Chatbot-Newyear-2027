import asyncio
import hashlib
import hmac
import logging
import os
import time
from collections import OrderedDict

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

app = FastAPI()
logger = logging.getLogger("uvicorn.error")

VERIFY_TOKEN = os.environ["VERIFY_TOKEN"]
WHATSAPP_TOKEN = os.environ["WHATSAPP_TOKEN"]
PHONE_NUMBER_ID = os.environ["PHONE_NUMBER_ID"].strip()
META_APP_SECRET = os.environ["META_APP_SECRET"]
GRAPH_API_VERSION = os.environ["GRAPH_API_VERSION"].strip()

WELCOME = (
    "🎉 Happy New Year! Welcome to Digital Catalyst’s "
    "New Year AI 2027.\n\n"
    "Create a wish for someone special, roast a friend for fun, "
    "or see what your future self might say.\n\n"
    "1. Personalized New Year Wish\n"
    "2. Roast My Friend\n"
    "3. 2027 Prediction\n"
    "4. Emotional Message\n"
    "5. Message From Future You\n\n"
    "Reply with a number from 1 to 5."
)

QUESTIONS = [
    "🎁 Who is this wish for?\n\n"
    "Enter their first name. Example: Priya",

    "What is your relationship with them?\n\n"
    "Example: Friend, sister, colleague, or partner",

    "Choose the tone:\n\n"
    "1. Warm\n"
    "2. Funny\n"
    "3. Professional\n"
    "4. Emotional",

    "Share one happy memory or something you appreciate "
    "about them.\n\n"
    "Example: You always encourage me.\n\n"
    "Reply SKIP to leave this out.",
]

FOOTER = (
    "\n\nReply ANOTHER to create another wish, "
    "or MENU to return to the main menu."
)

# Test storage only: resets when Render restarts or redeploys.
sessions = {}
seen_messages = OrderedDict()
processing_lock = asyncio.Lock()

SESSION_TTL = 30 * 60
MAX_SESSIONS = 2000


@app.api_route("/", methods=["GET", "HEAD"])
async def health():
    return {
        "status": "ok",
        "service": "WhatsApp personalized wish test",
    }


@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params

    valid = (
        params.get("hub.mode") == "subscribe"
        and hmac.compare_digest(
            params.get("hub.verify_token", ""),
            VERIFY_TOKEN,
        )
    )

    if not valid:
        raise HTTPException(
            status_code=403,
            detail="Verification failed",
        )

    return PlainTextResponse(params.get("hub.challenge", ""))


async def send_text(recipient: str, body: str) -> bool:
    url = (
        f"https://graph.facebook.com/{GRAPH_API_VERSION}/"
        f"{PHONE_NUMBER_ID}/messages"
    )

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                },
                json={
                    "messaging_product": "whatsapp",
                    "to": recipient,
                    "type": "text",
                    "text": {
                        "preview_url": False,
                        "body": body,
                    },
                },
            )

        if response.is_error:
            try:
                error = response.json().get("error", {})
            except ValueError:
                error = {}

            logger.error(
                "WhatsApp send failed: HTTP %s | "
                "code=%s | subcode=%s | message=%s",
                response.status_code,
                error.get("code"),
                error.get("error_subcode"),
                error.get("message", "Non-JSON error response"),
            )
            return False

        logger.info("WhatsApp reply accepted by Meta.")
        return True

    except httpx.HTTPError:
        logger.error(
            "WhatsApp send failed due to a connection error."
        )
        return False


def new_session():
    return {
        "step": "menu",
        "answers": [],
        "updated": time.monotonic(),
    }


def create_wish(answers):
    name, relationship, tone, detail = answers

    openings = {
        "Warm": (
            f"Happy New Year 2027, {name}! 🎉\n\n"
            "Wishing you a year filled with happiness, "
            "good health, and moments worth remembering."
        ),
        "Funny": (
            f"Happy New Year 2027, {name}! 😂\n\n"
            "May your luck be strong, your snacks plentiful, "
            "and your resolutions survive past January!"
        ),
        "Professional": (
            f"Happy New Year 2027, {name}!\n\n"
            "Wishing you good health, meaningful progress, "
            "and rewarding opportunities in the year ahead."
        ),
        "Emotional": (
            f"Happy New Year 2027, {name}! ❤️\n\n"
            "As a new year begins, I want you to know "
            "how much your presence in my life means to me."
        ),
    }

    result = openings[tone]
    result += f"\n\nI’m grateful to have you as my {relationship}."

    if detail:
        result += f"\n\nSomething I appreciate about you:\n{detail}"

    result += "\n\nHere’s to a wonderful 2027!"
    return result


def build_reply(text, current):
    command = text.casefold()

    if command == "stop":
        return (
            "Your current session has been cleared. "
            "Send HI whenever you want to start again.",
            None,
        )

    if command in {"hi", "hello", "menu", "restart"}:
        return WELCOME, new_session()

    if current is None:
        return (
            "Your session has ended or has not started.\n\n"
            + WELCOME,
            new_session(),
        )

    state = {
        **current,
        "answers": list(current["answers"]),
        "updated": time.monotonic(),
    }

    if command == "back":
        if state["step"] == "wish":
            if state["answers"]:
                state["answers"].pop()
                return QUESTIONS[len(state["answers"])], state

            return WELCOME, new_session()

        return WELCOME, new_session()

    if state["step"] == "menu":
        if command == "1":
            state["step"] = "wish"
            state["answers"] = []
            return (
                QUESTIONS[0]
                + "\n\nUse BACK to go back or MENU to restart.",
                state,
            )

        if command in {"2", "3", "4", "5"}:
            return (
                "This option is still being built.\n\n"
                "Reply 1 to test Personalized New Year Wish, "
                "or MENU to see all options.",
                state,
            )

        return "Please reply with a number from 1 to 5.", state

    if state["step"] == "done":
        if command == "another":
            state["step"] = "wish"
            state["answers"] = []
            return QUESTIONS[0], state

        return (
            "Reply ANOTHER to create another wish, "
            "or MENU to return to the main menu.",
            state,
        )

    index = len(state["answers"])

    if index == 0:
        if len(text) > 60:
            return "Please enter a first name under 60 characters.", state
        answer = text

    elif index == 1:
        if len(text) > 80:
            return (
                "Please enter a short relationship, "
                "such as friend or colleague.",
                state,
            )
        answer = text

    elif index == 2:
        tones = {
            "1": "Warm",
            "2": "Funny",
            "3": "Professional",
            "4": "Emotional",
            "warm": "Warm",
            "funny": "Funny",
            "professional": "Professional",
            "emotional": "Emotional",
        }
        answer = tones.get(command)

        if answer is None:
            return QUESTIONS[2], state

    else:
        if len(text) > 500:
            return (
                "Please keep your memory or detail "
                "under 500 characters, or reply SKIP.",
                state,
            )
        answer = "" if command == "skip" else text

    state["answers"].append(answer)

    if len(state["answers"]) < len(QUESTIONS):
        return QUESTIONS[len(state["answers"])], state

    result = create_wish(state["answers"])
    state["step"] = "done"

    return result + FOOTER, state


async def process_messages(messages):
    # Serial processing keeps this single-process test consistent.
    async with processing_lock:
        now = time.monotonic()

        expired = [
            recipient
            for recipient, state in sessions.items()
            if now - state["updated"] > SESSION_TTL
        ]
        for recipient in expired:
            sessions.pop(recipient, None)

        for message in messages:
            message_id = message.get("id")
            recipient = message.get("from")

            if not message_id or not recipient:
                continue

            if message_id in seen_messages:
                continue

            current = sessions.get(recipient)

            if message.get("type") != "text":
                reply = (
                    "Please send a text reply for this test. "
                    "Send MENU to see the options."
                )
                updated = current
            else:
                text = message.get("text", {}).get("body", "").strip()

                if not text:
                    continue

                reply, updated = build_reply(text, current)

            sent = await send_text(recipient, reply)

            if not sent:
                # Preserve the previous question if sending fails.
                continue

            if updated is None:
                sessions.pop(recipient, None)
            else:
                if recipient not in sessions and len(sessions) >= MAX_SESSIONS:
                    oldest = min(
                        sessions,
                        key=lambda key: sessions[key]["updated"],
                    )
                    sessions.pop(oldest, None)

                sessions[recipient] = updated

            seen_messages[message_id] = True

            if len(seen_messages) > 5000:
                seen_messages.popitem(last=False)


@app.post("/webhook")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    raw_body = await request.body()

    expected_signature = "sha256=" + hmac.new(
        META_APP_SECRET.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    received_signature = request.headers.get(
        "x-hub-signature-256",
        "",
    )

    if not hmac.compare_digest(
        received_signature,
        expected_signature,
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid signature",
        )

    try:
        payload = await request.json()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON",
        )

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=400,
            detail="Invalid payload",
        )

    incoming = []

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})

            incoming_phone_id = str(
                value.get("metadata", {}).get("phone_number_id", "")
            )

            if incoming_phone_id != PHONE_NUMBER_ID:
                continue

            incoming.extend(value.get("messages", []))

    if incoming:
        background_tasks.add_task(process_messages, incoming)

    return {"status": "received"}
