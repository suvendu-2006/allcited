# Allcited Swarm Visualizer

A standalone, real-time multi-agent orchestration visualizer for the Allcited project.

## Architecture
- **Star Topology**: All specialist agents (`Planner`, `Coder`, `Bug-Reviewer`, `Tester`) communicate strictly through the central `Lead Orchestrator`. Direct peer-to-peer agent links are prevented.
- **Real-Time Telemetry Bridge**:
  - Live Agent Transcript Streamer: tails Antigravity's `transcript.jsonl` to visualize tool calls, file reads, and shell commands in real time.
  - Codebase Watcher: monitors file writes in `api/`, `web/`, `docs/`, `eval/`, and `tests/`.
- **Zero Clutter**: Clean monospace typography, anti-collision layout, and automatic 3.2-second active glow dissipation (no permanent glowing boxes).

## Quick Start
```bash
python3 visualizer/server.py
```
Open [http://localhost:7777](http://localhost:7777) in your browser.
