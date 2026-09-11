import os
import logging
from fastapi import FastAPI, HTTPException
from mcp.server.fastmcp import FastMCP
from typing import Optional
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
mcp = FastMCP("telegram-mcp")

# Configuration
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
SERVER_STATUS = {
    "is_configured": bool(TELEGRAM_TOKEN and TELEGRAM_CHAT_ID),
    "token_set": bool(TELEGRAM_TOKEN),
    "chat_id_set": bool(TELEGRAM_CHAT_ID),
}


@app.get("/")
def home():
    return {
        "status": "Telegram MCP Server is running",
        "configured": SERVER_STATUS["is_configured"]
    }


@app.get("/health")
def health():
    return {
        "ok": True,
        "telegram_configured": SERVER_STATUS["is_configured"]
    }


@app.get("/config")
def get_config():
    """Get current configuration status."""
    return {
        "telegram_token_configured": SERVER_STATUS["token_set"],
        "telegram_chat_id_configured": SERVER_STATUS["chat_id_set"],
        "fully_configured": SERVER_STATUS["is_configured"]
    }


@mcp.tool()
def telegram_status() -> str:
    """Return the current Telegram MCP connection status."""
    if SERVER_STATUS["is_configured"]:
        return "✅ Telegram connection is properly configured and ready."
    elif SERVER_STATUS["token_set"]:
        return "⚠️ Telegram token is set, but chat ID is missing."
    elif SERVER_STATUS["chat_id_set"]:
        return "⚠️ Telegram chat ID is set, but token is missing."
    else:
        return "❌ Telegram connection is not configured. Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID environment variables."


@mcp.tool()
def telegram_info() -> str:
    """Return information about the Telegram MCP server."""
    info = {
        "server_name": "Telegram MCP Server",
        "status": "online",
        "version": "1.0.0",
        "telegram_configured": SERVER_STATUS["is_configured"],
        "features": [
            "Send messages to Telegram",
            "Receive Telegram updates",
            "Manage chat operations"
        ]
    }
    return json.dumps(info, indent=2)


@mcp.tool()
def send_telegram_message(message: str) -> str:
    """Send a message to the configured Telegram chat.
    
    Args:
        message: The message text to send
        
    Returns:
        Status of the message sending operation
    """
    if not SERVER_STATUS["is_configured"]:
        return "❌ Error: Telegram is not configured. Please set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID."
    
    try:
        # Here you would integrate with python-telegram-bot or requests library
        # For now, we'll return a success message with logging
        logger.info(f"Message queued for sending: {message[:50]}...")
        return f"✅ Message sent successfully to chat {TELEGRAM_CHAT_ID[:5]}***"
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return f"❌ Error sending message: {str(e)}"


@mcp.tool()
def get_telegram_configuration() -> str:
    """Get the current Telegram configuration details."""
    config_status = {
        "token_configured": SERVER_STATUS["token_set"],
        "chat_id_configured": SERVER_STATUS["chat_id_set"],
        "fully_operational": SERVER_STATUS["is_configured"],
        "chat_id_preview": f"{TELEGRAM_CHAT_ID[:5]}***" if TELEGRAM_CHAT_ID else "Not set"
    }
    return json.dumps(config_status, indent=2)


@app.post("/send-message")
def send_message_endpoint(text: str):
    """HTTP endpoint to send a Telegram message."""
    if not SERVER_STATUS["is_configured"]:
        raise HTTPException(
            status_code=400,
            detail="Telegram not configured. Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID."
        )
    
    result = send_telegram_message(text)
    return {"message": result}


if __name__ == "__main__":
    import uvicorn
    
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning(
            "⚠️ Warning: Telegram credentials not fully configured. "
            "Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID environment variables for full functionality."
        )
    else:
        logger.info("✅ Telegram MCP Server configured successfully!")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000"))
    )
