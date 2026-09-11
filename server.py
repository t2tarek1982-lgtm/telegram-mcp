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


def telegram_configured():
    return bool(TELEGRAM_TOKEN and TELEGRAM_CHAT_ID)


@app.get("/")
def home():
    return {
        "status": "Telegram MCP Server is running",
        "telegram_configured": telegram_configured()
    }


@app.get("/health")
def health():
    return {
        "ok": True,
        "telegram_configured": telegram_configured()
    }


@app.get("/config")
def config():
    return {
        "token_set": bool(TELEGRAM_TOKEN),
        "chat_id_set": bool(TELEGRAM_CHAT_ID),
        "configured": telegram_configured()
    }


@mcp.tool()
def telegram_status() -> str:
    """Check Telegram bot configuration."""
    if telegram_configured():
        return "✅ Telegram bot is configured."
    return "❌ Telegram bot is not configured."


@mcp.tool()
def send_telegram_message(message: str) -> str:
    """Send a real message through the configured Telegram bot."""

    if not telegram_configured():
        return "❌ TELEGRAM_TOKEN or TELEGRAM_CHAT_ID is missing."

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        response = requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            },
            timeout=15
        )

        data = response.json()

        if response.ok and data.get("ok"):
            logger.info("Telegram message sent successfully.")
            return "✅ Telegram message sent successfully."

        logger.error("Telegram API error: %s", data)
        return f"❌ Telegram API error: {data}"

    except requests.RequestException as e:
        logger.error("Telegram connection error: %s", e)
        return f"❌ Connection error: {e}"


@app.post("/send-message")
def send_message(text: str):
    result = send_telegram_message(text)

    if result.startswith("❌"):
        raise HTTPException(status_code=400, detail=result)

    return {"message": result}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000"))
    )
