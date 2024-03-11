import math


def mag(vec):
    return (vec.x ** 2 + vec.y ** 2 + vec.z ** 2) ** 0.5


def norm(vec):
    if mag(vec) != 0:
        return vec / mag(vec)
    # raise ZeroDivisionError("cannot normalize a zero vector")
    return Vec(0, 0, 0)


class Vec:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __add__(self, other):
        if isinstance(other, Vec):
            return Vec(self.x + other.x, self.y + other.y, self.z + other.z)
        raise TypeError(f"cannot add/subtract vector and {type(other)}")

    def __neg__(self):
        return Vec(-self.x, -self.y, -self.z)

    def __sub__(self, other):
        return self + -other

    def __mul__(self, scalar):
        if isinstance(scalar, (float, int)):
            return Vec(self.x * scalar, self.y * scalar, self.z * scalar)
        raise TypeError(f"cannot multiply vector and {type(scalar)}")

    def __rmul__(self, scalar):
        return self * scalar

    def __truediv__(self, scalar):
        if scalar == 0:
            raise ZeroDivisionError("")
        elif isinstance(scalar, (float, int)):
            return self * (1.0 / scalar)
        raise TypeError(f"cannot divide vector and {type(scalar)}")

    def __repr__(self):
        return f"<{self.x} {self.y} {self.z}>"

    def dot(self, other):
        if isinstance(other, Vec):
            return self.x * other.x + self.y * other.y + self.z * other.z
        raise TypeError(f"cannot compute dot product of vector and {type(other)}")

    def cross(self, other):
        if isinstance(other, Vec):
            return Vec(
                self.y * other.z - self.z * other.y,
                self.z * other.x - self.x * other.z,
                self.x * other.y - self.y * other.x)
        raise TypeError(f"cannot compute cross product of vector and {type(other)})")
