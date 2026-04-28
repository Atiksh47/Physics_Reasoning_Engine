# Physics Reasoning Engine

A physics reasoning system that converts natural language scene descriptions into deterministic 2D simulations, then explains what happened and why.

**Core thesis:** LLMs are good at language. Physics simulators are good at physics. Use each for what it's good at — the LLM understands what to simulate and explains the results; pymunk handles the actual computation.

---

## Architecture

```
Natural Language Input
        ↓
   Gemma 4 (Ollama) — scene parser
        ↓
   Scene JSON
        ↓
   pymunk Simulator
        ↓
   Result JSON (collisions, trajectories, velocities)
        ↓
   Gemma 4 (Ollama) — explanation generator    [Phase 5]
        ↓
   Human-readable explanation + visualization  [Phase 4]
```

---

## Project Status

| Phase | Description | Status |
|---|---|---|
| 1 | Core physics simulation | Done |
| 2 | JSON scene format | Done |
| 3 | Natural language scene parsing | Done |
| 4 | pygame visualization | In progress |
| 5 | Explanation layer | Planned |
| 6 | FastAPI backend | Planned |
| 7 | React frontend | Planned |
| 8 | Deployment + polish | Planned |

---

## Setup

**Requirements:** Python 3.11+, [Ollama](https://ollama.com) running locally with `gemma4:latest` pulled.

```bash
# Pull the model
ollama pull gemma4:latest

# Install dependencies
pip install pymunk pygame ollama

# Run a hardcoded physics test (Phase 1)
python physics/simulator.py

# Run a scene from JSON (Phase 2)
python physics/simulation.py scenes/example_basic.json

# Parse natural language to scene JSON (Phase 3)
python -m ai.scene_parser "A ball rolls down a steep ramp and hits a block"
```

---

## Scene JSON Format

Scenes are plain JSON. You can write them by hand or generate them from natural language.

```json
{
  "name": "Ball on slope hits block",
  "gravity": [0, -9.8],
  "damping": 0.99,
  "duration": 5.0,
  "steps_per_second": 120,
  "objects": [
    {"type": "ball",  "name": "ball",  "position": [1.0, 6.5], "radius": 0.4, "mass": 1.0},
    {"type": "slope", "name": "slope", "start": [0.0, 6.0], "end": [7.0, 1.5], "friction": 0.3},
    {"type": "block", "name": "block", "position": [7.5, 1.62], "size": [1.2, 1.2], "mass": 3.0},
    {"type": "wall",  "name": "floor", "start": [-1.0, 1.0], "end": [12.0, 1.0]}
  ]
}
```

Supported object types: `ball`, `slope` / `ramp`, `block`, `wall`.

---

## Result JSON Format

```json
{
  "duration": 5.0,
  "collisions": [
    {"objects": ["ball", "block"], "time": 1.74, "impact_impulse": 7.2}
  ],
  "final_states": {
    "ball": {"position": [7.7, 1.4], "velocity": [0, 0], "peak_velocity": 7.87}
  },
  "trajectories": {
    "ball": [[1.0, 6.5], [1.8, 6.1], "..."]
  }
}
```

---

## File Structure

```
reasoning-engine/
├── physics/
│   ├── simulator.py      # Phase 1 test harness (hardcoded scene)
│   ├── simulation.py     # run_simulation() entry point
│   ├── scene_loader.py   # JSON → pymunk bodies
│   ├── objects.py        # factory functions: ball, slope, block, wall
│   └── events.py         # collision detection and recording
├── ai/
│   ├── scene_parser.py   # parse_scene_from_text() via Gemma 4
│   └── prompts.py        # system prompts
├── scenes/
│   ├── example_basic.json
│   └── example_gentle_ramp.json
└── plan.md
```
