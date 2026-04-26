import pymunk


def add_ball(space, position, radius=0.5, mass=1.0, elasticity=0.6, friction=0.5):
    moment = pymunk.moment_for_circle(mass, 0, radius)
    body = pymunk.Body(mass, moment)
    body.position = position
    shape = pymunk.Circle(body, radius)
    shape.elasticity = elasticity
    shape.friction = friction
    shape.collision_type = 1
    shape.label = "ball"
    space.add(body, shape)
    return body, shape


def add_slope(space, start, end, friction=0.5, elasticity=0.3):
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    shape = pymunk.Segment(body, start, end, radius=0.05)
    shape.friction = friction
    shape.elasticity = elasticity
    shape.collision_type = 2
    shape.label = "slope"
    space.add(body, shape)
    return body, shape


def add_block(space, position, size=(1.0, 1.0), mass=5.0, elasticity=0.3, friction=0.5, static=False):
    w, h = size
    if static:
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
    else:
        moment = pymunk.moment_for_box(mass, (w, h))
        body = pymunk.Body(mass, moment)
    body.position = position
    shape = pymunk.Poly.create_box(body, (w, h))
    shape.elasticity = elasticity
    shape.friction = friction
    shape.collision_type = 3
    shape.label = "block"
    space.add(body, shape)
    return body, shape


def add_wall(space, start, end, friction=0.5, elasticity=0.1):
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    shape = pymunk.Segment(body, start, end, radius=0.05)
    shape.friction = friction
    shape.elasticity = elasticity
    shape.collision_type = 4
    shape.label = "wall"
    space.add(body, shape)
    return body, shape
