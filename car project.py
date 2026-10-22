
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import (
    AmbientLight, DirectionalLight, PointLight,
    Vec3, Vec4
)
import math


class CarSimulator(ShowBase):

    def __init__(self):
        super().__init__()

        self.disableMouse()
        self.setBackgroundColor(0.45, 0.72, 1, 1)
        self.isNight = False

        # Driving physics
        self.speed = 0.0
        self.maxSpeed = 22.0
        self.reverseMax = -8.0
        self.acceleration = 9.0
        self.braking = 18.0
        self.steering = 65.0

        self.keys = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
            "space": False
        }

        # ---------- GROUND ----------
        ground = self.loader.loadModel("models/box")
        ground.setScale(40, 100, 0.1)
        ground.setPos(0, 0, -0.6)
        ground.setColor(0.15, 0.42, 0.15, 1)
        ground.reparentTo(self.render)

        # ---------- ROAD ----------
        road = self.loader.loadModel("models/box")
        road.setScale(4, 100, 0.1)
        road.setPos(0, 0, -0.4)
        road.setColor(0.18, 0.18, 0.20, 1)
        road.reparentTo(self.render)

        # Road markings
        for y in range(-95, 100, 5):
            line = self.loader.loadModel("models/box")
            line.setScale(0.06, 1.2, 0.02)
            line.setPos(0, y, -0.27)
            line.setColor(1, 1, 1, 1)
            line.reparentTo(self.render)

        # ---------- CAR ----------
        self.car = self.render.attachNewNode("car")
        self.car.setPos(0, -5, 0.05)

        body = self.loader.loadModel("models/box")
        body.setScale(0.78, 1.5, 0.32)
        body.setPos(0, 0, 0.2)
        body.setColor(0.85, 0.015, 0.025, 1)
        body.reparentTo(self.car)

        cabin = self.loader.loadModel("models/box")
        cabin.setScale(0.53, 0.72, 0.30)
        cabin.setPos(0, 0.12, 0.78)
        cabin.setColor(0.12, 0.32, 0.48, 1)
        cabin.reparentTo(self.car)

        # ---------- WHEELS ----------
        self.wheels = []

        for side in [-1, 1]:
            for pos_y in [-1.0, 1.0]:
                wheel = self.car.attachNewNode("wheel")
                wheel.setPos(side * 0.78, pos_y, -0.05)
                self.wheels.append(wheel)

                tyre = self.loader.loadModel("models/misc/sphere")
                tyre.setScale(0.28, 0.16, 0.28)
                tyre.setColor(0.035, 0.035, 0.04, 1)
                tyre.reparentTo(wheel)

                hub = self.loader.loadModel("models/misc/sphere")
                hub.setScale(0.13, 0.055, 0.13)
                hub.setPos(side * 0.15, 0, 0)
                hub.setColor(0.75, 0.75, 0.8, 1)
                hub.reparentTo(wheel)

        # ---------- HEADLIGHTS ----------
        self.headlights = []

        for side in [-1, 1]:
            bulb = self.loader.loadModel("models/misc/sphere")
            bulb.setScale(0.13, 0.10, 0.10)
            bulb.setPos(side * 0.48, 1.43, 0.32)
            bulb.setColor(1, 1, 0.65, 1)
            bulb.reparentTo(self.car)

            light = PointLight("headlight")
            light.setColor(Vec4(1, 0.9, 0.65, 1))
            light.setAttenuation(Vec3(1, 0, 0.025))

            node = self.car.attachNewNode(light)
            node.setPos(side * 0.48, 1.5, 0.35)
            self.render.setLight(node)
            self.headlights.append(node)

        # ---------- LIGHTING ----------
        self.ambient = AmbientLight("ambient")
        self.ambient.setColor(Vec4(0.75, 0.75, 0.75, 1))
        self.ambient_node = self.render.attachNewNode(self.ambient)
        self.render.setLight(self.ambient_node)

        self.sun = DirectionalLight("sun")
        self.sun.setColor(Vec4(0.8, 0.8, 0.72, 1))
        self.sun_node = self.render.attachNewNode(self.sun)
        self.sun_node.setHpr(-30, -60, 0)
        self.render.setLight(self.sun_node)

        # ---------- HUD / SPEEDOMETER ----------
        self.speed_text = OnscreenText(
            text="SPEED: 0 km/h",
            pos=(-1.18, 0.88),
            scale=0.065,
            fg=(1, 1, 1, 1),
            align=0,
            mayChange=True
        )

        self.mode_text = OnscreenText(
            text="DAY MODE | N: Toggle Night",
            pos=(-1.18, 0.78),
            scale=0.045,
            fg=(1, 1, 0.6, 1),
            align=0,
            mayChange=True
        )

        self.help_text = OnscreenText(
            text="UP: Accelerate | DOWN: Brake/Reverse\n"
                 "LEFT/RIGHT: Steer | SPACE: Brake | N: Day/Night",
            pos=(0, -0.88),
            scale=0.045,
            fg=(1, 1, 1, 1),
            align=0,
            mayChange=True
        )

        # ---------- CONTROLS ----------
        controls = {
            "up": "arrow_up",
            "down": "arrow_down",
            "left": "arrow_left",
            "right": "arrow_right",
            "space": "space"
        }

        for key, panda_key in controls.items():
            self.accept(panda_key, self.setKey, [key, True])
            self.accept(panda_key + "-up", self.setKey, [key, False])

        self.accept("n", self.toggleNight)

        # Camera
        self.camera.setPos(0, -14, 5)
        self.camera.lookAt(0, -5, 0.3)

        self.taskMgr.add(self.updateGame, "updateGame")

    def setKey(self, key, value):
        self.keys[key] = value

    def toggleNight(self):
        self.isNight = not self.isNight

        if self.isNight:
            self.setBackgroundColor(0.015, 0.02, 0.08, 1)
            self.ambient.setColor(Vec4(0.12, 0.12, 0.20, 1))
            self.sun.setColor(Vec4(0.04, 0.04, 0.10, 1))
            self.mode_text.setText("NIGHT MODE | N: Toggle Day")

            for light in self.headlights:
                self.render.setLight(light)
        else:
            self.setBackgroundColor(0.45, 0.72, 1, 1)
            self.ambient.setColor(Vec4(0.75, 0.75, 0.75, 1))
            self.sun.setColor(Vec4(0.8, 0.8, 0.72, 1))
            self.mode_text.setText("DAY MODE | N: Toggle Night")

            for light in self.headlights:
                self.render.clearLight(light)

    def updateGame(self, task):
        dt = min(globalClock.getDt(), 0.05)

        # Accelerate
        if self.keys["up"]:
            self.speed = min(
                self.maxSpeed,
                self.speed + self.acceleration * dt
            )

        # Brake and reverse
        elif self.keys["down"]:
            if self.speed > 0:
                self.speed = max(
                    0, self.speed - self.braking * dt
                )
            else:
                self.speed = max(
                    self.reverseMax,
                    self.speed - self.acceleration * dt
                )

        # Space = stronger braking
        elif self.keys["space"]:
            if self.speed > 0:
                self.speed = max(0, self.speed - 25 * dt)
            elif self.speed < 0:
                self.speed = min(0, self.speed + 25 * dt)

        # Natural slowing when no pedal is pressed
        else:
            if self.speed > 0:
                self.speed = max(0, self.speed - 2 * dt)
            elif self.speed < 0:
                self.speed = min(0, self.speed + 2 * dt)

        # Steering works more at higher speeds
        if abs(self.speed) > 0.1:
            turn = 0

            if self.keys["left"]:
                turn = 1
            elif self.keys["right"]:
                turn = -1

            self.car.setH(
                self.car.getH()
                + turn * self.steering * dt
                * min(1, abs(self.speed) / 4)
                * (1 if self.speed > 0 else -1)
            )

        # Move forward in the direction the car faces
        if abs(self.speed) > 0.001:
            heading = math.radians(self.car.getH())

            dx = math.sin(heading) * self.speed * dt
            dy = math.cos(heading) * self.speed * dt

            self.car.setX(self.car.getX() + dx)
            self.car.setY(self.car.getY() + dy)

            rotation = self.speed * dt * 180 / (math.pi * 0.28)

            for wheel in self.wheels:
                wheel.setP(wheel.getP() + rotation)

        # Speed display in km/h (game speed scale)
        kmh = int(abs(self.speed) * 5)
        self.speed_text.setText("SPEED: " + str(kmh) + " km/h")

        # Follow camera
        car_pos = self.car.getPos(self.render)
        heading = math.radians(self.car.getH())

        distance = 8
        target_x = car_pos.x - math.sin(heading) * distance
        target_y = car_pos.y - math.cos(heading) * distance
        target_z = car_pos.z + 3.5

        current = self.camera.getPos(self.render)
        blend = min(1.0, 4 * dt)

        self.camera.setPos(
            current.x + (target_x - current.x) * blend,
            current.y + (target_y - current.y) * blend,
            current.z + (target_z - current.z) * blend
        )

        self.camera.lookAt(
            car_pos.x, car_pos.y, car_pos.z + 0.4
        )

        return Task.cont


game = CarSimulator()
game.run()
