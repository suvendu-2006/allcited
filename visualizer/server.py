#!/usr/bin/env python3
"""
Allcited Swarm Visualizer Server
Self-contained daemon located in `allcited/visualizer/`.
Restores the rich Allcited Swarm Orchestration Engine design with full multi-agent support:
- Lead Orchestrator (Gold)
- Planner (Cyan/Terracotta)
- Coder (Blue/Violet)
- Bug-Reviewer (Coral)
- Tester (Mint Green)
"""

import json
import os
import queue
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HOST = "0.0.0.0"
PORT = 7777
VISUALIZER_DIR = Path(__file__).resolve().parent
STATIC_DIR = VISUALIZER_DIR / "static"
PROJECT_ROOT = VISUALIZER_DIR.parent

SUBSCRIBERS = set()
SUBSCRIBERS_LOCK = threading.Lock()
EVENT_HISTORY = []
HISTORY_LOCK = threading.Lock()

def broadcast_event(event_dict):
    """Broadcasts a JSON event to all connected browsers and appends to history."""
    if not event_dict or not isinstance(event_dict, dict):
        return

    with HISTORY_LOCK:
        EVENT_HISTORY.append(event_dict)
        if len(EVENT_HISTORY) > 200:
            EVENT_HISTORY.pop(0)

    data = f"data: {json.dumps(event_dict)}\n\n"
    with SUBSCRIBERS_LOCK:
        dead = set()
        for q in list(SUBSCRIBERS):
            try:
                q.put_nowait(data)
            except Exception:
                dead.add(q)
        SUBSCRIBERS.difference_update(dead)

class SwarmHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        # Polling fallback endpoint
        if parsed.path == "/api/events/poll":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            with HISTORY_LOCK:
                history_copy = list(EVENT_HISTORY[-3:])
            self.wfile.write(json.dumps({"events": history_copy}).encode("utf-8"))
            return

        # SSE Stream endpoint
        if parsed.path == "/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache, no-transform")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()

            q = queue.Queue()
            with SUBSCRIBERS_LOCK:
                SUBSCRIBERS.add(q)

            try:
                while True:
                    try:
                        msg = q.get(timeout=8.0)
                        self.wfile.write(msg.encode("utf-8"))
                        self.wfile.flush()
                    except queue.Empty:
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
            except (ConnectionResetError, BrokenPipeError, Exception):
                pass
            finally:
                with SUBSCRIBERS_LOCK:
                    SUBSCRIBERS.discard(q)
            return

        elif parsed.path == "/" or parsed.path == "/index.html":
            self.path = "/index.html"
            return super().do_GET()

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/broadcast":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                event_data = json.loads(body)
                broadcast_event(event_data)
            except Exception:
                pass
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
            return

        elif parsed.path == "/api/access":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
                rel = data.get("file", "main.py")
                action = data.get("action", "inspecting")
                msg = data.get("message", f"Inspecting {rel}...")

                role = "CODER_ACTIVE"
                if rel.endswith(".md") or "doc" in rel:
                    role = "PLANNER_ACTIVE"
                elif "test" in rel or "eval" in rel:
                    role = "TESTER_ACTIVE"
                elif "web" in rel or rel.endswith((".tsx", ".ts", ".css")):
                    role = "REVIEWER_ACTIVE"

                broadcast_event({
                    "type": role,
                    "file": rel,
                    "message": msg,
                    "action": action
                })
            except Exception:
                pass
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
            return

        self.send_error(404, "Endpoint not found")

    def log_message(self, format, *args):
        pass

# =====================================================================
# LIVE AGENT TRANSCRIPT STREAMER
# Watches Antigravity's transcript.jsonl and streams actions to agents
# =====================================================================
def find_latest_transcript():
    """Locates the latest conversation transcript.jsonl file."""
    home = Path.home()
    base_brain = home / ".gemini" / "antigravity" / "brain"
    if not base_brain.exists():
        return None

    matches = list(base_brain.glob("*/.system_generated/logs/transcript.jsonl"))
    if not matches:
        return None
    matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0]

def start_transcript_watcher():
    """Tails transcript.jsonl in real time to stream agent thoughts, tool calls, and actions."""
    def tail_loop():
        transcript_file = find_latest_transcript()
        if not transcript_file:
            time.sleep(2.0)
            transcript_file = find_latest_transcript()
        if not transcript_file:
            return

        print(f"📡 Hooked Live Agent Transcript: {transcript_file}")
        try:
            with open(transcript_file, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(0, os.SEEK_END)
                last_tell = f.tell()

                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.12)
                        curr_size = os.path.getsize(transcript_file)
                        if curr_size < last_tell:
                            f.seek(0, os.SEEK_SET)
                        last_tell = f.tell()
                        continue

                    last_tell = f.tell()
                    try:
                        record = json.loads(line.strip())
                    except Exception:
                        continue

                    tool_calls = record.get("tool_calls")
                    if not tool_calls:
                        continue

                    for call in tool_calls:
                        name = call.get("name", "")
                        args = call.get("args", {})
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except Exception:
                                args = {}

                        # 1. File Reads
                        if name == "read_file":
                            fpath = str(args.get("Path", "")).strip('\"\'')
                            fname = Path(fpath).name.strip('\"\'')
                            if not fname or fname.endswith((".jpg", ".png", ".gif", ".jpeg", ".txt", ".log")):
                                continue
                            if "visualizer" in fpath or "brain" in fpath or "/tmp/" in fpath:
                                continue

                            if fname.endswith(".md") or "doc" in fpath:
                                role = "PLANNER_ACTIVE"
                                msg = f"[PLANNER] Reading {fname}..."
                            elif "test" in fpath or "eval" in fpath:
                                role = "TESTER_ACTIVE"
                                msg = f"[TESTER] Reviewing {fname}..."
                            elif "web" in fpath or fname.endswith((".tsx", ".ts", ".css")):
                                role = "REVIEWER_ACTIVE"
                                msg = f"[BUG-REVIEWER] Auditing {fname}..."
                            else:
                                role = "CODER_ACTIVE"
                                msg = f"[CODER] Inspecting {fname}..."

                            broadcast_event({
                                "type": role,
                                "file": fname,
                                "message": msg,
                                "action": "read"
                            })

                        # 2. File Writes / Edits
                        elif name in ("write_file", "edit_file"):
                            fpath = str(args.get("Path", "")).strip('\"\'')
                            fname = Path(fpath).name.strip('\"\'')
                            if not fname or fname.endswith((".jpg", ".png", ".gif", ".jpeg", ".txt", ".log")):
                                continue
                            if "visualizer" in fpath or "brain" in fpath or "/tmp/" in fpath:
                                continue

                            if fname.endswith(".md") or "doc" in fpath:
                                role = "PLANNER_ACTIVE"
                                msg = f"[PLANNER] Updating {fname}..."
                            elif "test" in fpath or "eval" in fpath:
                                role = "TESTER_ACTIVE"
                                msg = f"[TESTER] Updating {fname}..."
                            elif "web" in fpath or fname.endswith((".tsx", ".ts", ".css")):
                                role = "REVIEWER_ACTIVE"
                                msg = f"[BUG-REVIEWER] Modifying {fname}..."
                            else:
                                role = "CODER_ACTIVE"
                                msg = f"[CODER] Modifying {fname}..."

                            broadcast_event({
                                "type": role,
                                "file": fname,
                                "message": msg,
                                "action": "modify"
                            })

                        # 3. Shell / Pytest / Build Commands
                        elif name == "run_command":
                            cmd = str(args.get("CommandLine", "")).strip('\"\'')
                            summary = str(args.get("toolSummary", "")).strip('\"\'')
                            if "visualizer" in cmd or "verify" in cmd or "brain" in cmd:
                                continue

                            if "pytest" in cmd or "test" in cmd:
                                target_f = "test_rerank.py" if "rerank" in cmd else ("test_retrieve.py" if "retrieve" in cmd else "test_health.py")
                                broadcast_event({
                                    "type": "TESTER_ACTIVE",
                                    "file": target_f,
                                    "message": f"[TESTER] Running {summary or 'pytest suite'}...",
                                    "action": "test"
                                })
                            elif "npm" in cmd or "next" in cmd or "node" in cmd:
                                broadcast_event({
                                    "type": "REVIEWER_ACTIVE",
                                    "file": "SourcePanel.tsx",
                                    "message": f"[BUG-REVIEWER] Running {summary or 'frontend check'}...",
                                    "action": "lint"
                                })
                            elif "git" in cmd:
                                broadcast_event({
                                    "type": "PLANNER_ACTIVE",
                                    "file": "PLAN.md",
                                    "message": f"[PLANNER] Synchronizing git state: {summary or cmd[:40]}...",
                                    "action": "git"
                                })
                            else:
                                broadcast_event({
                                    "type": "CODER_ACTIVE",
                                    "file": "main.py",
                                    "message": f"[CODER] Executing: {summary or cmd[:40]}...",
                                    "action": "run"
                                })
        except Exception:
            time.sleep(2.0)

    t = threading.Thread(target=tail_loop, daemon=True)
    t.start()

# =====================================================================
# LIVE FILE SYSTEM WATCHER
# Detects repo file modifications
# =====================================================================
def start_codebase_watcher():
    """Background daemon that monitors codebase file changes."""
    ignore_dirs = {".git", ".next", "node_modules", "__pycache__", ".venv", "venv", ".pytest_cache", ".gemini", "visualizer", "static", "tmp"}

    def scan_project_mtimes():
        result = {}
        for sub in ("api", "web", "tests", "docs", "eval"):
            dir_path = PROJECT_ROOT / sub
            if not dir_path.exists():
                continue
            for p in dir_path.glob("**/*"):
                if p.is_file():
                    parts = set(p.parts)
                    if not parts.intersection(ignore_dirs) and p.suffix not in (".pyc", ".pyo", ".log", ".tmp"):
                        try:
                            result[str(p)] = p.stat().st_mtime
                        except Exception:
                            pass
        return result

    def watch_loop():
        last_snapshot = scan_project_mtimes()
        while True:
            time.sleep(0.4)
            current_snapshot = scan_project_mtimes()
            for fpath, mtime in current_snapshot.items():
                if fpath not in last_snapshot or mtime > last_snapshot[fpath]:
                    changed_name = Path(fpath).name

                    role = "CODER_ACTIVE"
                    if changed_name.endswith(".md") or "doc" in fpath:
                        role = "PLANNER_ACTIVE"
                    elif "test" in fpath or "eval" in fpath:
                        role = "TESTER_ACTIVE"
                    elif "web" in fpath or changed_name.endswith((".tsx", ".ts", ".css")):
                        role = "REVIEWER_ACTIVE"

                    broadcast_event({
                        "type": role,
                        "file": changed_name,
                        "message": f"Modified {changed_name}",
                        "action": "modify"
                    })
            last_snapshot = current_snapshot

    t = threading.Thread(target=watch_loop, daemon=True)
    t.start()

def main():
    print(f"⚡ Allcited Swarm Visualizer running at: http://{HOST if HOST != '0.0.0.0' else 'localhost'}:{PORT}")
    start_transcript_watcher()
    start_codebase_watcher()
    server = ThreadingHTTPServer((HOST, PORT), SwarmHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
