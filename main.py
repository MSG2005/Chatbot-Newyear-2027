import asyncio
import hashlib
import hmac
import logging
import os
from collections import OrderedDict

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

app = FastAPI()
logger = logging.getLogger("uvicorn.error")

VERIFY_TOKEN = os.environ["VERIFY_TOKEN"]
WHATSAPP_TOKEN = os.environ["WHATSAPP_TOKEN"]
PHONE_NUMBER_ID = os.environ["PHONE_NUMBER_ID"]
META_APP_SECRET = os.environ["META_APP_SECRET"]
GRAPH_API_VERSION = os.environ["GRAPH_API_VERSION"]

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

# Temporary duplicate protection for this single-process test.
seen_messages = OrderedDict()
message_lock = asyncio.Lock()


@app.get("/")
async def health():
    return {"status": "ok", "service": "WhatsApp welcome test"}


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
        raise HTTPException(status_code=403, detail="Verification failed")

    return PlainTextResponse(params.get("hub.challenge", ""))


async def send_welcome(recipient: str):
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
                    "text": {"body": WELCOME},
                },
            )

        if response.is_error:
            error = response.json().get("error", {})
            logger.error(
                "WhatsApp send failed: HTTP %s | code=%s | subcode=%s | message=%s",
                response.status_code,
                error.get("code"),
                error.get("error_subcode"),
                error.get("message"),
            )
        else:
            logger.info("WhatsApp welcome accepted by Meta.")

    except httpx.HTTPError:
        logger.error("WhatsApp send failed due to a connection error.")


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

    received_signature = request.headers.get("x-hub-signature-256", "")

    if not hmac.compare_digest(
        received_signature,
        expected_signature,
    ):
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        payload = await request.json()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})

            if str(value.get("metadata", {}).get("phone_number_id")) != PHONE_NUMBER_ID:
                continue

            for message in value.get("messages", []):
                if message.get("type") != "text":
                    continue

                text = message.get("text", {}).get("body", "").strip().lower()

                if text not in {"hi", "hello", "menu", "restart"}:
                    continue

                message_id = message.get("id")
                recipient = message.get("from")

                if not message_id or not recipient:
                    continue

                async with message_lock:
                    if message_id in seen_messages:
                        continue

                    seen_messages[message_id] = True

                    if len(seen_messages) > 2000:
                        seen_messages.popitem(last=False)

                background_tasks.add_task(send_welcome, recipient)

    return {"status": "received"}
