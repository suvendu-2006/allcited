#!/usr/bin/env python3
"""
Telegram Webhook Setup Utility.
Configures the Telegram Bot API webhook to point to the production API deployment
with secret token verification header (X-Telegram-Bot-Api-Secret-Token).
"""

import argparse
import os
import sys
from typing import Any, Dict, Optional
import httpx


def configure_telegram_webhook(
    bot_token: str,
    api_base_url: str,
    secret_token: Optional[str] = None,
    client: Optional[httpx.Client] = None,
) -> Dict[str, Any]:
    """
    Register the /v1/telegram/webhook endpoint with the Telegram Bot API.
    """
    clean_api_url = api_base_url.rstrip("/")
    webhook_url = f"{clean_api_url}/v1/telegram/webhook"
    telegram_endpoint = f"https://api.telegram.org/bot{bot_token}/setWebhook"

    payload: Dict[str, Any] = {
        "url": webhook_url,
        "allowed_updates": ["message", "edited_message"],
    }
    if secret_token:
        payload["secret_token"] = secret_token

    should_close = False
    if client is None:
        client = httpx.Client(timeout=15.0)
        should_close = True

    try:
        resp = client.post(telegram_endpoint, json=payload)
        data = resp.json()
        return {
            "status_code": resp.status_code,
            "webhook_url": webhook_url,
            "telegram_response": data,
            "success": data.get("ok", False),
        }
    finally:
        if should_close:
            client.close()


def main():
    parser = argparse.ArgumentParser(description="Configure Telegram Bot Webhook for Allcited")
    parser.add_argument(
        "--token",
        default=os.getenv("TELEGRAM_BOT_TOKEN"),
        help="Telegram Bot API token",
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("API_URL", "https://your-space.hf.space"),
        help="Production API base URL (e.g. Hugging Face Space URL)",
    )
    parser.add_argument(
        "--secret",
        default=os.getenv("TELEGRAM_WEBHOOK_SECRET"),
        help="Telegram webhook verification secret token",
    )
    args = parser.parse_args()

    if not args.token:
        print("Error: TELEGRAM_BOT_TOKEN must be provided via --token or environment variable.", file=sys.stderr)
        sys.exit(1)

    print(f"Setting webhook to: {args.api_url}/v1/telegram/webhook...")
    res = configure_telegram_webhook(
        bot_token=args.token,
        api_base_url=args.api_url,
        secret_token=args.secret,
    )
    print(f"Result: {res}")
    sys.exit(0 if res["success"] else 1)


if __name__ == "__main__":
    main()
