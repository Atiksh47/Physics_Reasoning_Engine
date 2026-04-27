import json
import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymunk
from physics.scene_loader import load_scene
from physics.events import attach_collision_handlers


def run_simulation(scene: dict) -> dict:
    space = pymunk.Space()
    collision_log = []
    current_time = {"t": 0.0}

    bodies = load_scene(space, scene)
    attach_collision_handlers(space, collision_log, current_time)

    duration = scene.get("duration", 5.0)
    steps_per_second = scene.get("steps_per_second", 120)
    dt = 1.0 / steps_per_second
    total_steps = int(duration * steps_per_second)
    sample_every = max(1, steps_per_second // 10)

    trajectories = {name: [] for name in bodies}
    peak_velocities = {name: 0.0 for name in bodies}

    for i in range(total_steps):
        current_time["t"] = i * dt
        space.step(dt)
        for name, body in bodies.items():
            speed = body.velocity.length
            if speed > peak_velocities[name]:
                peak_velocities[name] = speed
        if i % sample_every == 0:
            for name, body in bodies.items():
                trajectories[name].append([
                    round(body.position.x, 3),
                    round(body.position.y, 3),
                ])

    final_states = {}
    for name, body in bodies.items():
        final_states[name] = {
            "position": [round(body.position.x, 3), round(body.position.y, 3)],
            "velocity": [round(body.velocity.x, 3), round(body.velocity.y, 3)],
            "peak_velocity": round(peak_velocities[name], 4),
        }

    result = {
        "duration": duration,
        "collisions": collision_log,
        "final_states": final_states,
        "trajectories": trajectories,
    }
    if "queries" in scene:
        result["queries"] = scene["queries"]
    return result


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "scenes/example_basic.json"
    with open(path) as f:
        scene = json.load(f)

    result = run_simulation(scene)
    print(json.dumps(result, indent=2))

    ball_block = [c for c in result["collisions"]
                  if set(c["objects"]) == {"ball", "block"}]
    if ball_block:
        first = ball_block[0]
        print(f"\nBall collided with block at t={first['time']}s "
              f"(impulse={first['impact_impulse']} N·s)")
    else:
        print("\nNo ball-block collision in this simulation.")
