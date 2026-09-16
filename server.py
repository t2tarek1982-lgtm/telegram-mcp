import os
import logging
import requests
from fastapi import FastAPI, HTTPException
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
mcp = FastMCP("telegram-mcp")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

def telegram_configured():
    return bool(TELEGRAM_TOKEN and TELEGRAM_CHAT_ID)

@app.get("/")
def home():
    return {
        "status": "Telegram MCP Server is running",
        "telegram_configured": telegram_configured(),
        "gemini_configured": bool(GEMINI_API_KEY)
    }

@app.get("/health")
def health():
    return {
        "ok": True,
        "telegram_configured": telegram_configured(),
        "gemini_configured": bool(GEMINI_API_KEY)
    }

@app.get("/config")
def config():
    return {
        "token_set": bool(TELEGRAM_TOKEN),
        "chat_id_set": bool(TELEGRAM_CHAT_ID),
        "gemini_set": bool(GEMINI_API_KEY),
        "configured": telegram_configured()
    }

@mcp.tool()
def telegram_status() -> str:
    if telegram_configured():
        return "Telegram bot is configured."
    return "Telegram bot is not configured."

@mcp.tool()
def send_telegram_message(message: str) -> str:
    if not telegram_configured():
        return "TELEGRAM_TOKEN or TELEGRAM_CHAT_ID is missing."

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        response = requests.post(
            url,
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message},
            timeout=15
        )

        data = response.json()

        if response.ok and data.get("ok"):
            return "Telegram message sent successfully."

        return f"Telegram API error: {data}"

    except requests.RequestException as e:
        return f"Connection error: {e}"

@app.post("/telegram/webhook")
async def telegram_webhook(update: dict):
    message = update.get("message", {})
    text = message.get("text", "")
    chat = message.get("chat", {})
    chat_id = chat.get("id")

    if not text or not chat_id:
        return {"ok": True}

    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent",
            headers={
                "Content-Type": "application/json",
                "X-goog-api-key": GEMINI_API_KEY
            },
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": text}
                        ]
                    }
                ]
            },
            timeout=30
        )

        data = response.json()
        reply = data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        logger.error("Gemini error: %s", e)
        reply = "حصلت مشكلة مؤقتة مع Gemini."

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": reply
        },
        timeout=15
    )

    return {"ok": True}

@app.post("/send-message")
def send_message(text: str):
    result = send_telegram_message(text)

    return {"message": result}
app.mount("/mcp", mcp.streamable_http_app())
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000"))
        )


