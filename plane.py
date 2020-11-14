import cocos.actions as act
import cocos.collision_model as cm
import cocos.euclid as eu
from cocos.sprite import Sprite

import math
import random


class ActorDriver(act.Move):
    def step(self, dt):
        super(ActorDriver, self).step(dt)
        x, y = self.target.position
        w, h = abs(self.target.width), self.target.height
        width, height = self.target.parent.width, self.target.parent.height

        # Horizontal wrapping
        if self.target.velocity[0] < 0 and x < -0.3 * w:
            x = width + 0.4 * w
        elif self.target.velocity[0] > 0 and x > width + 0.3 * w:
            x = -0.4 * w

        # Vertical bound
        if y > height - h / 2:
            y = height - h / 2
            # self.target.do(act.MoveBy((0, -h/10), 0.05))
        elif y < h / 2:
            y = h / 2

        self.target.position = (x, y)


class Actor(Sprite):
    radius = 20
    speed = 20

    def __init__(self, img, speed:float=None, r_to_l: bool = False, **kwargs):
        super(Actor, self).__init__(img, **kwargs)

        self.r_to_l = r_to_l
        self.scale *= 0.1
        if r_to_l:
            self.scale_x = -1

        if speed:
            self.speed = speed
        self.velocity = (0, 0)

        self.physics_on = True

        self.update_velocity()
        self.do(ActorDriver())

    def update_velocity(self):
        angle = self.rotation
        if self.r_to_l:
            angle += 180
        angle = math.radians(angle)
        self.velocity = (math.cos(angle) * self.speed,
                         -math.sin(angle) * self.speed)

    def update_cshape(self):
        '''Update a collision shape'''
        self.cshape = cm.CircleShape(eu.Vector2(self.x, self.y), self.radius)

    def set_physics(self, state:bool):
        self.physics_on = state


class Plane(Actor):
    radius = 40
    speed = 100

    def __init__(self, **kwargs):
        super(Plane, self).__init__(
            img='img/plane3.png',
            scale=2,
            **kwargs)
        # self._initial_pos = kwargs.get('position', (0, 0))
        # self._initial_rot = kwargs.get('rotation', 0)
        self._initial_pos = self.position
        self._initial_rot = self.rotation
        self._initial_scale = self.scale

    def get_controller(self):
        return PlaneController(self)

    def respawn(self):
        self.position = self._initial_pos
        self.rotation = self._initial_rot
        self.scale = self._initial_scale
        self.update_velocity()


class PlaneController:
    '''Interface for player to manipulate plane'''
    # TODO: restrictions (plane can't shoot too often)
    def __init__(self, plane:Plane):
        self.plane = plane

    def rotate(self, dAngle):
        self.plane.rotation += dAngle
        self.plane.update_velocity()

    def fire(self):
        if self.plane.physics_on:
            self.plane.parent.create_rocket(self.plane)


class Rocket(Actor):
    radius = 10
    speed = Plane.speed * 4

    def __init__(self, **kwargs):
        super(Rocket, self).__init__(
            img='img/rocket2.png',
            scale=2.,
            **kwargs)


class Cloud(Actor):
    def __init__(self, **kwargs):
        super(Cloud, self).__init__(
            img='img/cloud%i.png' % random.randrange(3, 5+1),
            **kwargs
        )
        self.set_physics(False)