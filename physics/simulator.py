import pymunk
import json
from physics.objects import add_ball, add_slope, add_block, add_wall
from physics.events import attach_collision_handlers


def run_simulation(duration=5.0, steps_per_second=120):
    space = pymunk.Space()
    space.gravity = (0, -9.8)
    space.damping = 0.99

    # Hardcoded Phase 1 scene: ball on slope, block at bottom
    ball_body, _ = add_ball(space, position=(1.0, 8.0), radius=0.4, mass=1.0)
    add_slope(space, start=(0.0, 6.0), end=(7.0, 1.5), friction=0.3)
    block_body, _ = add_block(space, position=(7.5, 2.5), size=(1.2, 1.2), mass=3.0)
    # Floor so nothing falls forever
    add_wall(space, start=(-1.0, 1.0), end=(12.0, 1.0))

    collision_log = []
    current_time = {"t": 0.0}
    attach_collision_handlers(space, collision_log, current_time)

    dt = 1.0 / steps_per_second
    total_steps = int(duration * steps_per_second)
    trajectory = []
    sample_every = steps_per_second // 10  # 10 samples per second

    for i in range(total_steps):
        current_time["t"] = i * dt
        space.step(dt)
        if i % sample_every == 0:
            trajectory.append([round(ball_body.position.x, 3),
                                round(ball_body.position.y, 3)])

    result = {
        "duration": duration,
        "collisions": collision_log,
        "final_states": {
            "ball": {
                "position": [round(ball_body.position.x, 3), round(ball_body.position.y, 3)],
                "velocity": [round(ball_body.velocity.x, 3), round(ball_body.velocity.y, 3)],
            },
            "block": {
                "position": [round(block_body.position.x, 3), round(block_body.position.y, 3)],
                "velocity": [round(block_body.velocity.x, 3), round(block_body.velocity.y, 3)],
            },
        },
        "trajectory": {"ball": trajectory},
    }
    return result


if __name__ == "__main__":
    result = run_simulation()
    print(json.dumps(result, indent=2))

    collisions = result["collisions"]
    ball_block = [c for c in collisions if set(c["objects"]) == {"ball", "block"}]
    if ball_block:
        first = ball_block[0]
        print(f"\nBall collided with block at t={first['time']}s "
              f"(impulse={first['impact_impulse']} N·s)")
    else:
        print("\nNo ball-block collision detected in the simulation window.")
