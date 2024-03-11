import copy

from vectors import *

G = 6.67e-11


class SpaceBall:
    def __init__(self, position, velocity, mass, radius, color=(255, 255, 255), does_drag=False):
        self.v = velocity
        self.pos = position
        self.pos0 = copy.deepcopy(position)
        self.v0 = copy.deepcopy(velocity)
        self.a = Vec()
        self.f = Vec()
        self.r = radius
        self.m = mass
        self.color = color
        self.t = 0
        self.does_drag = does_drag
        self.thrust_force_vec = Vec()
        # self.normal_force = Vec()

    def __repr__(self):
        return f"ball\n\tpos = {self.pos}\n\tvel = {self.v}\n\tacc = {self.a}\n\tm = {self.m}"

    def move(self, dt):
        self.pos += self.v * dt
        self.a = (self.f + self.thrust_force_vec) / self.m
        self.v += self.a * dt

    def distance_to(self, other):
        return mag(other.pos - self.pos)

    def colliding_with(self, other):
        return self.distance_to(other) <= (self.r + other.r)

    def force_from(self, other):
        r = other.pos - self.pos
        # return (G * self.m * other.m / (mag(r) ** 2)) * norm(r)
        return (G * self.m * other.m / (r.x**2+r.y**2+r.z**2)) * norm(r)  # avoids sqrt operation in mag()

    def update(self, dt):
        self.move(dt)
        self.t += dt

    def future_force(self, objects, dt, v, index):
        pos = self.pos + v*dt  # future position based on v and current position
        sb = SpaceBall(pos, v, self.m, 1)  # copy of self at future position to use in future force calculation
        f = sum([sb.force_from(thing2) for thing2 in objects if objects.index(thing2) != index], Vec())  # sum forces
        return f

    def update_rk4(self, dt, list_start, list_mid, list_end, index):
        # index: index of planet in all lists (to skip over in force calculation)
        # v for vel and x for pos in k value var names
        v = self.v  # velocity at start = k1x
        m = self.m

        f = self.future_force(list_start, 0, v, index) + self.thrust_force_vec  # + self.normal_force  # find force to
        # use in finding acc=k1v
        k1v = f / m  # acc estimate initial
        k1x = v  # v estimate initial

        v_mid1 = v + k1v * dt / 2  # uses k1v to find v estimate at midpoint 1
        f = self.future_force(list_mid, dt / 2, v_mid1, index) + self.thrust_force_vec  # + self.normal_force
        k2v = f / m  # acc estimate at midpoint 1
        k2x = v_mid1  # v estimate at midpoint 1

        v_mid2 = v + k2v * dt / 2  # uses k2v to find v estimate at midpoint 2
        f = self.future_force(list_mid, dt / 2, v_mid2, index) + self.thrust_force_vec  # + self.normal_force
        k3v = f / m  # acc estimate at midpoint 2
        k3x = v_mid2  # v estimate at midpoint 2

        v_end = v + k3v * dt  # uses k3v to find v estimate at end
        f = self.future_force(list_end, dt, v_end, index) + self.thrust_force_vec  # + self.normal_force
        k4v = f / m  # acc estimate at end
        k4x = v_end  # v estimate at end

        # rk4 uses 4 slope estimates instead of 1 (euler)
        self.a = (k1v + 2 * k2v + 2 * k3v + k4v) * dt / 6
        self.v += self.a  # update v using weighted avg of all acc estimates
        self.pos += (k1x + 2 * k2x + 2 * k3x + k4x) * dt / 6  # update pos using weighted avg of all v estimates
        self.t += dt


def update_list_rk4(objects, dt):
    list_start = update_list_return(objects, 0)  # list of planets at start of interval
    list_mid = update_list_return(objects, dt / 2)  # list of updated planets at midpoint of interval
    list_end = update_list_return(objects, dt)  # list of updated planets at end of interval
    for i in range(len(objects)):
        objects[i].update_rk4(dt, list_start, list_mid, list_end, i)


def update_list_return(list, dt):
    objects = [SpaceBall(thing.pos, thing.v, thing.m, 1) for thing in list]
    for obj in objects:
        obj.check_orbit = False
    update_pairs(objects, dt)
    return objects


def update_list(objects, dt):
    for thing1 in objects:
        thing1.f = sum((thing1.force_from(thing2) for thing2 in objects if thing2 != thing1), Vec())
    for thing in objects:
        thing.update(dt)


def update_pairs(objects, dt):
    n = len(objects)
    for i in range(n):
        # since everything from 0 to i has already calculated everything, j only needs to be > i
        for j in range(i + 1, n):
            obj_i = objects[i]
            obj_j = objects[j]
            force = obj_i.force_from(obj_j)
            obj_i.f += force
            obj_j.f -= force
    for thing in objects:
        thing.update(dt)
        thing.f = Vec()
