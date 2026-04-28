import pymunk


def attach_collision_handlers(space, collision_log, current_time):
    seen = set()

    def post_solve(arbiter, space, data):
        shapes = arbiter.shapes
        label_a = getattr(shapes[0], "label", None)
        label_b = getattr(shapes[1], "label", None)
        if label_a is None or label_b is None:
            return
        key = tuple(sorted((label_a, label_b)))
        if key not in seen and current_time["t"] > 0.05:
            seen.add(key)
            collision_log.append({
                "objects": list(key),
                "time": round(current_time["t"], 4),
                "impact_impulse": round(arbiter.total_impulse.length, 4),
            })

    space.on_collision(post_solve=post_solve)
