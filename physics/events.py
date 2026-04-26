import pymunk


def attach_collision_handlers(space, collision_log, current_time):
    """
    Registers first-contact collision handlers using pymunk 7.x on_collision API.
    """
    seen = set()

    def make_post_solve(label_a, label_b):
        key = (label_a, label_b)
        def post_solve(arbiter, space, data):
            if key not in seen:
                seen.add(key)
                collision_log.append({
                    "objects": list(key),
                    "time": round(current_time["t"], 4),
                    # total_impulse is populated after the solver resolves forces
                    "impact_impulse": round(arbiter.total_impulse.length, 4),
                })
        return post_solve

    space.on_collision(1, 3, post_solve=make_post_solve("ball", "block"))   # ball ↔ block
    space.on_collision(1, 2, post_solve=make_post_solve("ball", "slope"))   # ball ↔ slope
    space.on_collision(1, 4, post_solve=make_post_solve("ball", "wall"))    # ball ↔ wall
    space.on_collision(3, 4, post_solve=make_post_solve("block", "wall"))   # block ↔ wall
