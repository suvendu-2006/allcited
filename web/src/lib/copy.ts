/**
 * ALLCITED.md §4 Copy Freeze Constants
 * Source of truth for all human-voiced strings across the frontend.
 */

export const ERROR_MESSAGES: Record<string, string> = {
  doc_unreadable: "Couldn't read that file — corrupt or password-protected. Nothing was saved.",
  doc_too_large: "That's past the size limit for your plan. (Free: 10 MB · Pro: 100 MB.)",
  free_tier_busy: "Our free brain is swamped right now. Try again in a minute — or plug in your own key in Settings and skip the line.",
  ollama_unreachable: "Can't reach your local Ollama. Is it running? (ollama serve)",
  url_blocked: "That link points somewhere private — we don't fetch those. Safety thing.",
  injection_flagged: "Heads up: this document contains text trying to give me instructions. I've treated it as data. The answer stands.",
  plan_limit_reached: "That's a Pro move. Upgrade to keep going.",
  session_expired: "This conversation's gone cold. Re-upload the document and we're back.",
  offline: "You're offline. Your last conversation is still here — ask away when you're back.",
  generic: "Something broke on our side. It's noted — try again, and if it repeats, the trace ID below helps us find it.",
};

export const SAMPLE_QUESTIONS = [
  "What can I carry forward?",
  "What does rule 63.7.4 actually say?",
  "Summarize section 4 like I'm new",
];

export const SEARCHING_VARIANTS = [
  "reading the shelves…",
  "flipping pages…",
  "hunting for citations…",
];

export const REFUSAL_NOT_IN_DOC = {
  title: "Honestly? This document doesn't say.",
  body: "I answer only from what you've given me, and it isn't in here. Try rephrasing — or check you've uploaded the full version.",
};

export const REFUSAL_OFF_TOPIC = {
  title: "I only answer from your document.",
  body: "That's what keeps me honest. Want code, though? Upload a Python book and I'll write it — cited line by line.",
};

export const PRICING_COPY = {
  free: {
    name: "Free",
    price: "₹0",
    badge: "for everyone",
    description: "Unlimited questions · documents up to 10 MB · all 6 formats · every citation, every trace.",
  },
  pro: {
    name: "Pro",
    price: "₹299",
    cycle: "/ month · cancel anytime",
    description: "Everything in Free, plus: documents up to 100 MB · Precision mode (reads 50 passages before answering, not 25) · unlimited shelf · priority when we're busy.",
    ghostNote: "test-mode checkout during beta — no real charges",
    limitToast: "That's a Pro move. Upgrade to keep going — your work stays put.",
    success: "Pro unlocked. Go read something enormous.",
  },
};
