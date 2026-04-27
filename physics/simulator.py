import json
import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from physics.simulation import run_simulation

_PHASE1_SCENE = {
    "gravity": [0, -9.8],
    "damping": 0.99,
    "duration": 5.0,
    "steps_per_second": 120,
    "objects": [
        {"type": "ball", "name": "ball", "position": [1.0, 6.5], "radius": 0.4, "mass": 1.0},
        {"type": "slope", "name": "slope", "start": [0.0, 6.0], "end": [7.0, 1.5], "friction": 0.3},
        {"type": "block", "name": "block", "position": [7.5, 1.62], "size": [1.2, 1.2], "mass": 3.0},
        {"type": "wall", "name": "floor", "start": [-1.0, 1.0], "end": [12.0, 1.0]},
    ],
}


if __name__ == "__main__":
    result = run_simulation(_PHASE1_SCENE)
    print(json.dumps(result, indent=2))

    ball_block = [c for c in result["collisions"] if set(c["objects"]) == {"ball", "block"}]
    if ball_block:
        first = ball_block[0]
        print(f"\nBall collided with block at t={first['time']}s "
              f"(impulse={first['impact_impulse']} N·s)")
    else:
        print("\nNo ball-block collision detected in the simulation window.")
