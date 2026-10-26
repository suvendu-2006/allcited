import datetime
import logging
import os
import threading
import uuid
from typing import Any, Dict, Optional, Set

import httpx
import stripe
from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from app.config import get_settings

logger = logging.getLogger(__name__)


class CheckoutRequest(BaseModel):
    price_id: Optional[str] = Field(default=None, description="Stripe price ID for Pro subscription")
    success_url: Optional[str] = Field(default=None, description="Redirect URL upon successful payment")
    cancel_url: Optional[str] = Field(default=None, description="Redirect URL if checkout is canceled")


class CheckoutResponse(BaseModel):
    checkout_url: str = Field(..., description="Stripe hosted checkout session URL")
    session_id: str = Field(..., description="Stripe checkout session ID")
    mode: str = Field(default="live", description="Stripe mode: live or test")


class SubscriptionInfo(BaseModel):
    user_id: str
    plan: str = Field(default="free", description="Current plan tier: free or pro")
    customer_id: Optional[str] = None
    subscription_id: Optional[str] = None
    status: str = Field(default="active")
    updated_at: str


def _sync_subscription_to_supabase(
    user_id: str,
    plan: str,
    customer_id: Optional[str],
    subscription_id: Optional[str],
    status: str,
):
    settings = get_settings()
    if not (settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY):
        return
    try:
        base_url = settings.SUPABASE_URL.rstrip("/")
        headers = {
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        }
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        payload = {
            "user_id": user_id,
            "plan": plan,
            "stripe_customer_id": customer_id,
            "stripe_subscription_id": subscription_id,
            "status": status,
            "updated_at": now_str,
        }
        with httpx.Client(timeout=5.0) as client:
            client.post(
                f"{base_url}/rest/v1/subscriptions?on_conflict=user_id",
                headers=headers,
                json=payload,
            )
    except Exception as e:
        logger.warning("Supabase subscription sync failed: %s", e)


class SubscriptionStore:
    """Thread-safe store for subscriptions with idempotent webhook event replay protection."""

    def __init__(self):
        self._lock = threading.Lock()
        # user_id -> SubscriptionInfo
        self._subscriptions: Dict[str, SubscriptionInfo] = {}
        # Set of processed Stripe event IDs for replay idempotency
        self._processed_events: Set[str] = set()

    def get_plan(self, user_id: str) -> str:
        with self._lock:
            info = self._subscriptions.get(user_id)
            if info:
                return info.plan

        # On in-memory miss, query Supabase outside lock
        settings = get_settings()
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            try:
                base_url = settings.SUPABASE_URL.rstrip("/")
                headers = {
                    "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                }
                with httpx.Client(timeout=3.0) as client:
                    resp = client.get(
                        f"{base_url}/rest/v1/subscriptions?user_id=eq.{user_id}",
                        headers=headers,
                    )
                    if resp.status_code == 200:
                        rows = resp.json()
                        if rows:
                            row = rows[0]
                            sub = SubscriptionInfo(
                                user_id=user_id,
                                plan=row.get("plan", "free"),
                                customer_id=row.get("stripe_customer_id"),
                                subscription_id=row.get("stripe_subscription_id"),
                                status=row.get("status", "active"),
                                updated_at=row.get("updated_at", ""),
                            )
                            with self._lock:
                                self._subscriptions[user_id] = sub
                            return sub.plan
            except Exception as e:
                logger.warning("Supabase get_plan lookup failed: %s", e)

        return "free"

    def get_subscription(self, user_id: str) -> SubscriptionInfo:
        with self._lock:
            if user_id not in self._subscriptions:
                now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
                self._subscriptions[user_id] = SubscriptionInfo(
                    user_id=user_id,
                    plan="free",
                    updated_at=now_str,
                )
            return self._subscriptions[user_id]

    def update_plan(
        self,
        user_id: str,
        plan: str,
        customer_id: Optional[str] = None,
        subscription_id: Optional[str] = None,
        status: str = "active",
    ) -> SubscriptionInfo:
        with self._lock:
            now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
            sub = SubscriptionInfo(
                user_id=user_id,
                plan=plan,
                customer_id=customer_id,
                subscription_id=subscription_id,
                status=status,
                updated_at=now_str,
            )
            self._subscriptions[user_id] = sub

        # Persist to Supabase asynchronously outside lock
        threading.Thread(
            target=_sync_subscription_to_supabase,
            args=(user_id, plan, customer_id, subscription_id, status),
            daemon=True,
        ).start()

        return sub

    def is_event_processed(self, event_id: str) -> bool:
        with self._lock:
            return event_id in self._processed_events

    def mark_event_processed(self, event_id: str) -> None:
        with self._lock:
            self._processed_events.add(event_id)

    def reset_for_tests(self) -> None:
        with self._lock:
            self._subscriptions.clear()
            self._processed_events.clear()


_subscription_store: Optional[SubscriptionStore] = None


def get_subscription_store() -> SubscriptionStore:
    global _subscription_store
    if _subscription_store is None:
        _subscription_store = SubscriptionStore()
    return _subscription_store


async def create_checkout_session(
    user_id: str,
    price_id: Optional[str] = None,
    success_url: Optional[str] = None,
    cancel_url: Optional[str] = None,
) -> CheckoutResponse:
    """Create a Stripe checkout session for the Pro subscription tier."""
    settings = get_settings()
    active_price_id = price_id or settings.STRIPE_PRICE_ID_PRO
    s_url = success_url or settings.STRIPE_SUCCESS_URL
    c_url = cancel_url or settings.STRIPE_CANCEL_URL

    # If secret key is provided and not test placeholder
    if (
        settings.STRIPE_SECRET_KEY
        and not settings.STRIPE_SECRET_KEY.startswith("mock_")
        and "mock" not in settings.STRIPE_SECRET_KEY.lower()
    ):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{"price": active_price_id, "quantity": 1}],
                mode="subscription",
                client_reference_id=user_id,
                metadata={"user_id": user_id},
                success_url=s_url,
                cancel_url=c_url,
            )
            return CheckoutResponse(
                checkout_url=session.url,
                session_id=session.id,
                mode="live",
            )
        except Exception as e:
            logger.error(f"Stripe session creation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"error": {"code": "stripe_error", "message": str(e)}},
            )

    # Deterministic test mode fallback
    test_session_id = f"cs_test_{uuid.uuid4().hex[:16]}"
    test_checkout_url = f"https://checkout.stripe.com/c/pay/{test_session_id}"
    return CheckoutResponse(
        checkout_url=test_checkout_url,
        session_id=test_session_id,
        mode="test",
    )


async def handle_stripe_webhook(payload: bytes, sig_header: Optional[str]) -> Dict[str, Any]:
    """
    Verify Stripe webhook signature, process subscription events, and enforce replay idempotency.
    """
    settings = get_settings()
    store = get_subscription_store()
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    if not webhook_secret:
        if os.getenv("ENVIRONMENT") == "test":
            webhook_secret = "whsec_test_secret_allcited"
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": {"code": "stripe_unconfigured", "message": "STRIPE_WEBHOOK_SECRET is not configured."}},
            )

    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "missing_signature", "message": "Missing Stripe-Signature header"}},
        )

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=webhook_secret,
        )
    except stripe.SignatureVerificationError as e:
        logger.warning(f"Stripe signature verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "invalid_signature", "message": "Invalid Stripe webhook signature"}},
        )
    except Exception as e:
        logger.error(f"Error parsing Stripe webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "invalid_payload", "message": str(e)}},
        )

    event_id = event["id"]
    event_type = event["type"]

    # Replay protection: if event already processed, exit idempotently without double-applying
    if store.is_event_processed(event_id):
        logger.info(f"Replayed Stripe event {event_id} already processed — skipping duplicate application.")
        return {
            "status": "ignored",
            "reason": "duplicate_event",
            "event_id": event_id,
            "replayed": True,
        }

    # Handle subscription update events
    if event_type in ("checkout.session.completed", "customer.subscription.created", "customer.subscription.updated"):
        raw_obj = event["data"]["object"]
        obj = raw_obj.to_dict() if hasattr(raw_obj, "to_dict") else dict(raw_obj)
        user_id = obj.get("client_reference_id") or obj.get("metadata", {}).get("user_id")
        customer_id = obj.get("customer")
        subscription_id = obj.get("subscription") or obj.get("id")

        if user_id:
            store.update_plan(
                user_id=user_id,
                plan="pro",
                customer_id=customer_id,
                subscription_id=subscription_id,
                status="active",
            )
            logger.info(f"Upgraded user {user_id} to Pro via Stripe event {event_id}")
            from app.audit import get_audit_store
            get_audit_store().record_action(
                user_id=user_id,
                action="subscription_updated",
                details={
                    "event_id": event_id,
                    "event_type": event_type,
                    "plan": "pro",
                    "customer_id": customer_id,
                },
            )

    elif event_type == "customer.subscription.deleted":
        raw_obj = event["data"]["object"]
        obj = raw_obj.to_dict() if hasattr(raw_obj, "to_dict") else dict(raw_obj)
        user_id = obj.get("metadata", {}).get("user_id")
        if user_id:
            store.update_plan(
                user_id=user_id,
                plan="free",
                status="canceled",
            )
            logger.info(f"Downgraded user {user_id} to Free via Stripe event {event_id}")
            from app.audit import get_audit_store
            get_audit_store().record_action(
                user_id=user_id,
                action="subscription_updated",
                details={
                    "event_id": event_id,
                    "event_type": event_type,
                    "plan": "free",
                },
            )

    # Mark event as processed to prevent double-application on future retries
    store.mark_event_processed(event_id)

    return {
        "status": "success",
        "event_id": event_id,
        "event_type": event_type,
        "replayed": False,
    }
