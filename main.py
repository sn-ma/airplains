#!/usr/bin/env python3

import cocos
import cocos.collision_model as cm
import cocos.actions as act
import cocos.euclid as eu
from cocos.director import director
import pyglet
import random

from cocos.text import Label

from plane import Plane, PlaneController, Rocket, Cloud


def color_to_tuple(color: str) -> tuple:
    assert len(color) == 6
    t = (color[i:i + 2] for i in range(0, len(color), 2))
    t = (int(e, base=16) for e in t)
    return tuple(t)


class MainLayer(cocos.layer.ColorLayer):
    initial_pos = (50, 200)
    initial_angle = 20
    ground_level = 150

    def __init__(self):
        super(MainLayer, self).__init__(*color_to_tuple('333333'), 0xff)
        bg = cocos.sprite.Sprite(
            'img/background.png',
            anchor=(0, 0)
        )
        bg.scale_x = self.width / bg.width
        bg.scale_y = self.height / bg.height
        self.add(bg)

        self.actors = []
        self.event_receivers = []

        plane_r = Plane(
            position=(self.width - self.initial_pos[0], self.initial_pos[1]),
            color=color_to_tuple('33ff33'),
            r_to_l=True,
            rotation=self.initial_angle
        )
        self.event_receivers.append(KbPlaneManipulator(
            plane_r.get_controller(),
            k_left=(pyglet.window.key.LEFT, ),
            k_right=(pyglet.window.key.RIGHT, ),
            k_fire=(pyglet.window.key.UP, pyglet.window.key.DOWN),
        ))
        self.actors.append(plane_r)
        self.add(plane_r)

        plane_l = Plane(
            position=self.initial_pos,
            color=color_to_tuple('ff2222'),
            rotation=-self.initial_angle
        )
        self.actors.append(plane_l)
        self.add(plane_l)
        self.event_receivers.append(KbPlaneManipulator(
            plane_l.get_controller(),
            k_left=(pyglet.window.key.A, ),
            k_right=(pyglet.window.key.D, ),
            k_fire=(pyglet.window.key.W, pyglet.window.key.S),
        ))

        self.collman = cm.CollisionManagerGrid(
            0, self.width,
            0, self.height,
            Plane.radius*1.25, Plane.radius * 1.25
        )

        for i in range(random.randrange(4, 11)):
            h = random.random() * 0.6 + 0.4
            self.add(Cloud(
                position=(
                    self.width * random.random(),
                    self.height * h
                ),
                speed=100 * (h**2),
                scale=h*3,
                # r_to_l=False,
                r_to_l=random.randrange(2),
            ))

        self.schedule(self.update)
        self.planes = (plane_l, plane_r)

        self.score = [0, 0]
        self.label = None
        self.place_label()

    def create_rocket(self, plane: Plane) -> None:
        pos = eu.Vector2(*plane.position)
        pos += eu.Vector2(*plane.velocity).normalized() * (plane.radius + Rocket.radius) * 1.4
        rocket = Rocket(
            position=pos,
            rotation=plane.rotation + (180 if plane.r_to_l else 0),
        )
        action = act.Delay(2.) + act.FadeOut(1.) + act.CallFunc(lambda: self.free_rocket(rocket))
        rocket.do(action)
        self.add(rocket)
        self.actors.append(rocket)

    def free_rocket(self, rocket: Rocket):
        assert isinstance(rocket, Rocket)
        if rocket not in self.actors:  # already removed
            return
        self.actors.remove(rocket)
        self.remove(rocket)

    __player_destroy_action = \
        act.CallFuncS(Plane.set_physics, False) | \
        (act.ScaleBy(4, 0.2) | act.FadeOut(0.2)) + \
        act.Delay(0.5) + \
        act.CallFuncS(Plane.respawn) + \
        act.FadeIn(0.2) + \
        act.CallFuncS(Plane.set_physics, True)

    def update(self, dt):
        self.collman.clear()
        for actor in self.actors:
            if actor.physics_on:
                if actor.y < self.ground_level:
                    self.collision_action(actor)
                else:
                    actor.update_cshape()
                    self.collman.add(actor)
        for collided in self.collman.iter_all_collisions():
            # print('Collision:', act1, act2)
            # if all(isinstance(act, Rocket) for act in collided): # rockets don't damage each other
            #     continue
            # act1, act2 = collided
            # center = (eu.Vector2(*act1.position) + eu.Vector2(*act2.position)) / 2
            for actor in collided:
                self.collision_action(actor)

    def collision_action(self, actor):
        if isinstance(actor, Rocket):
            self.free_rocket(actor)
        elif isinstance(actor, Plane):
            actor.do(self.__player_destroy_action)
            idx = 1 if actor == self.planes[0] else 0
            self.score[idx] += 1
            self.place_label()

    def on_enter(self):
        super(MainLayer, self).on_enter()
        for er in self.event_receivers:
            director.window.push_handlers(er)

    def on_exit(self):
        for er in self.event_receivers:
            director.window.remove_handlers(er)
        super(MainLayer, self).on_exit()

    def place_label(self):
        if self.label:
            self.remove(self.label)
        self.label = Label(
            "{}:{}".format(*self.score),
            position = (0, self.height - 50),
            font_size = 40
        )
        self.add(self.label)


class KbPlaneManipulator:
    """Control plane from keyboard"""
    max_angular_acc = 2

    def __init__(self, plane_ctrl: PlaneController, k_left, k_right, k_fire):
        """Keys -- from  pyglet.window.key.*"""
        self.plane_ctrl = plane_ctrl
        self._left_pressed = False
        self._right_pressed = False
        self._k_left = k_left
        self._k_right = k_right
        self._k_fire = k_fire

    def on_key_press(self, key, modifiers):
        if key in self._k_left:
            self._left_pressed = True
        elif key in self._k_right:
            self._right_pressed = True
        elif key in self._k_fire:
            self.plane_ctrl.fire()

    def on_key_release(self, key, modifiers):
        if key in self._k_left:
            self._left_pressed = False
        elif key in self._k_right:
            self._right_pressed = False

    def on_draw(self):
        if self._right_pressed and not self._left_pressed:
            self.plane_ctrl.rotate(self.max_angular_acc)
        elif self._left_pressed and not self._right_pressed:
            self.plane_ctrl.rotate(-self.max_angular_acc)


if __name__ == '__main__':
    director.init(
        width=1200, height=700,
        resizable=True,
        fullscreen=False,
    )
    layer = MainLayer()
    scene = cocos.scene.Scene(layer)
    director.run(scene)
