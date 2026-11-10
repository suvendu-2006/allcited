#!/usr/bin/env python3
"""
Allcited Swarm Visualizer Telemetry Trigger
Broadcasts real-time events from CLI or test suites to http://localhost:7777.
"""
import json
import sys
import urllib.request

VISUALIZER_URL = "http://127.0.0.1:7777/api/broadcast"

def emit(event_type: str, message: str, file: str = None, goal: str = None):
    """Pushes a live event to the Allcited visualizer graph."""
    try:
        payload = {
            "type": event_type,
            "message": message
        }
        if file:
            payload["file"] = file
        if goal:
            payload["goal"] = goal

        req = urllib.request.Request(
            VISUALIZER_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=0.8)
    except Exception:
        pass

def emit_orchestrator(goal: str, message: str = None):
    emit("DISPATCH", message or f"Orchestrating goal: {goal}", goal=goal)

def emit_planner(message: str, file: str = "PLAN.md", done: bool = False):
    emit("PLANNER_DONE" if done else "PLANNER_ACTIVE", message, file=file)

def emit_coder(message: str, file: str = None, done: bool = False):
    emit("CODER_DONE" if done else "CODER_ACTIVE", message, file=file)

def emit_reviewer(message: str, file: str = None, done: bool = False):
    emit("REVIEWER_DONE" if done else "REVIEWER_ACTIVE", message, file=file)

def emit_tester(message: str, file: str = None, done: bool = False):
    emit("TESTER_DONE" if done else "TESTER_ACTIVE", message, file=file)

def emit_complete(message: str = "Swarm task completed and verified."):
    emit("SWARM_COMPLETE", message)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: trigger.py <role> <message> [file]")
        sys.exit(0)

    role = sys.argv[1].lower()
    msg = sys.argv[2] if len(sys.argv) > 2 else "Active"
    target_file = sys.argv[3] if len(sys.argv) > 3 else None

    if role in ("orchestrator", "dispatch"):
        emit_orchestrator(msg)
    elif role in ("planner", "plan"):
        done = "done" in msg.lower() or "approv" in msg.lower()
        emit_planner(msg, file=target_file or "PLAN.md", done=done)
    elif role in ("coder", "code"):
        done = "done" in msg.lower() or "commit" in msg.lower()
        emit_coder(msg, file=target_file, done=done)
    elif role in ("reviewer", "review", "audit"):
        done = "done" in msg.lower() or "verif" in msg.lower()
        emit_reviewer(msg, file=target_file, done=done)
    elif role in ("tester", "test"):
        done = "done" in msg.lower() or "pass" in msg.lower()
        emit_tester(msg, file=target_file, done=done)
    elif role in ("complete", "done"):
        emit_complete(msg)
    else:
        emit("GENERAL", msg, file=target_file)
