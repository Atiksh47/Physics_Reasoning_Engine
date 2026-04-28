import itertools
import pymunk

_id_counter = itertools.count(1)


def _next_id():
    return next(_id_counter)


def add_ball(space, name, position, radius=0.5, mass=1.0, elasticity=0.6, friction=0.5):
    moment = pymunk.moment_for_circle(mass, 0, radius)
    body = pymunk.Body(mass, moment)
    body.position = position
    shape = pymunk.Circle(body, radius)
    shape.elasticity = elasticity
    shape.friction = friction
    shape.collision_type = _next_id()
    shape.label = name
    space.add(body, shape)
    return body, shape


def add_slope(space, name, start, end, friction=0.5, elasticity=0.3):
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    shape = pymunk.Segment(body, start, end, radius=0.05)
    shape.friction = friction
    shape.elasticity = elasticity
    shape.collision_type = _next_id()
    shape.label = name
    space.add(body, shape)
    return body, shape


def add_block(space, name, position, size=(1.0, 1.0), mass=5.0, elasticity=0.3, friction=0.5, static=False):
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
    shape.collision_type = _next_id()
    shape.label = name
    space.add(body, shape)
    return body, shape


def add_wall(space, name, start, end, friction=0.5, elasticity=0.1):
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    shape = pymunk.Segment(body, start, end, radius=0.05)
    shape.friction = friction
    shape.elasticity = elasticity
    shape.collision_type = _next_id()
    shape.label = name
    space.add(body, shape)
    return body, shape
