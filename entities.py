import random

from engine import *


class Player(SpaceBall):
    def __init__(self, position, velocity, mass, radius, max_fuel, max_health, thruster_force, angle):
        super().__init__(position, velocity, mass, radius)
        self.fuel = self.max_fuel = max_fuel
        self.health = self.max_health = max_health
        self.thruster_force = thruster_force
        self.angle = angle
        self.angle_rate = 0
        self.using_rockets = False
        self.is_dead = False
        self.shooting = False
        self.shot_cooldown = 40

    def shoot(self, speed, inaccuracy):
        angle = self.angle + random.randint(-inaccuracy, inaccuracy)
        pos = self.pos + self.r*norm(Vec(math.cos(math.radians(self.angle)), math.sin(math.radians(self.angle))))
        vel = self.v + speed * norm(Vec(math.cos(math.radians(angle)), math.sin(math.radians(angle))))
        return Projectile(pos, vel, targeting_enemies=True)

    def update_angle_thrust(self):
        if self.using_rockets:
            self.thrust_force_vec = Vec(math.cos(math.radians(self.angle)),
                                        math.sin(math.radians(self.angle))) * self.thruster_force
            self.fuel = max(0, self.fuel - 1)
        else:
            self.thrust_force_vec = Vec()
        self.angle += self.angle_rate

    def collide_with_ground(self, left, right, dist, fuel_regen, health_regen):
        x1, x2, y1, y2 = left[0], right[0], left[1], right[1]
        vec = Vec(x2 - x1, y2 - y1)
        normal = norm(vec.cross(Vec(0, 0, 1)))
        v_in_norm_direction = self.v.dot(normal) * normal
        self.pos -= (self.r - dist) * normal  # subtract intersection vector from position
        v_in_plane_direction = self.v - v_in_norm_direction
        self.v = -0.5 * v_in_norm_direction + 0.3 * v_in_plane_direction
        if mag(v_in_norm_direction) >= 10:
            self.health -= mag(v_in_norm_direction) ** 1.3  # **1.5
            if self.health <= 0:
                self.health = 0

        self.fuel = min(self.max_fuel, self.fuel + fuel_regen)
        if self.health > 0:
            self.health = min(self.max_health, self.health + health_regen)


class Projectile:
    def __init__(self, pos, vel, targeting_player=False, targeting_enemies=False, radius=2, color=(255, 0, 150)):
        self.pos = pos
        self.v = vel
        self.r = radius
        self.color = color
        self.targeting_player = targeting_player
        self.targeting_enemies = targeting_enemies
        self.num_ticks = 0

    def move(self, dt):
        self.pos += self.v * dt
        self.num_ticks += 1

    def distance_to(self, other):
        return mag(other.pos - self.pos)


class Enemy:
    def __init__(self, pos, radius=10, color=(255, 255, 255)):
        self.pos = pos
        self.v = Vec()
        self.r = radius
        self.color = color
        self.t = 0
        self.num_ticks = 0

    def move(self, target, dt, smart=False):
        self.v = norm(target.pos - self.pos) * (0 + mag(target.pos - self.pos)/30)
        if smart:
            # move in a zigzag pattern
            self.v += 10*norm(self.v).cross(Vec(0, 0, math.copysign(1, math.sin(math.radians(self.num_ticks)))))
        self.pos += self.v * dt
        self.num_ticks += 1

    def shoot(self, target, inaccuracy):
        speed = min(35, 30 + mag(self.v))
        direction = norm(target.pos - self.pos)

        inaccuracy_rad = math.radians(inaccuracy)
        inn = random.uniform(-inaccuracy_rad, inaccuracy_rad)
        angle = math.atan2(direction.y, direction.x) + inn

        vel = speed * norm(Vec(math.cos(angle), math.sin(angle)))  # in target direction
        return Projectile(self.pos, vel, targeting_player=True, targeting_enemies=False)

    def smart_shoot(self, target, inaccuracy):
        speed = min(35, 30 + mag(self.v))
        target_future_pos = target.pos

        # calculate target future position
        for i in range(20):  # if target moves far away time keeps increasing -> overflow if too many loops
            distance = mag(target_future_pos - self.pos)
            time_to_hit = distance/speed
            if time_to_hit > 2048:  # prevent overflow + too far away for calculation to matter
                break
            # time to hit and target future position are related; I couldn't find a more efficient method than this loop
            # it seems to work well enough
            target_future_pos = target.pos + target.v*time_to_hit + 0.5*target.a*time_to_hit**2

        direction = norm(target_future_pos - self.pos)

        inaccuracy_rad = math.radians(inaccuracy)
        inn = random.uniform(-inaccuracy_rad, inaccuracy_rad)
        angle = math.atan2(direction.y, direction.x) + inn

        vel = speed * norm(Vec(math.cos(angle), math.sin(angle)))

        return Projectile(self.pos, vel, targeting_player=True, targeting_enemies=False)
