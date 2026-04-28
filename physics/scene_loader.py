import pymunk
from physics.objects import add_ball, add_slope, add_block, add_wall


def load_scene(space, scene: dict) -> dict:
    """
    Populates a pymunk Space from a scene dict.
    Returns a mapping of object name → body, for result tracking.
    """
    gx, gy = scene.get("gravity", [0, -9.8])
    space.gravity = (gx, gy)
    space.damping = scene.get("damping", 0.99)

    bodies = {}

    for obj in scene.get("objects", []):
        t = obj["type"]
        name = obj.get("name", t)

        if t == "ball":
            body, _ = add_ball(
                space,
                name=name,
                position=tuple(obj["position"]),
                radius=obj.get("radius", 0.5),
                mass=obj.get("mass", 1.0),
                elasticity=obj.get("elasticity", 0.6),
                friction=obj.get("friction", 0.5),
            )
            bodies[name] = body

        elif t in ("slope", "ramp"):
            add_slope(
                space,
                name=name,
                start=tuple(obj["start"]),
                end=tuple(obj["end"]),
                friction=obj.get("friction", 0.4),
                elasticity=obj.get("elasticity", 0.3),
            )

        elif t == "block":
            body, _ = add_block(
                space,
                name=name,
                position=tuple(obj["position"]),
                size=tuple(obj.get("size", [1.0, 1.0])),
                mass=obj.get("mass", 5.0),
                elasticity=obj.get("elasticity", 0.3),
                friction=obj.get("friction", 0.5),
                static=obj.get("static", False),
            )
            bodies[name] = body

        elif t == "wall":
            add_wall(
                space,
                name=name,
                start=tuple(obj["start"]),
                end=tuple(obj["end"]),
                friction=obj.get("friction", 0.5),
                elasticity=obj.get("elasticity", 0.1),
            )

        else:
            raise ValueError(f"Unknown object type: '{t}'")

    return bodies
