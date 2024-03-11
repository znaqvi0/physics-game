import datetime
import random
import time

from vectors import *
import pygame as p
import sys  # most commonly used to turn the interpreter off (shut down your game)
from engine import *

# Initializes pygame - see documentation
p.init()

# Constants - sets the size of the window
WIDTH = 800
HEIGHT = 800

screen = p.display.set_mode((WIDTH, HEIGHT))
screen.fill((0, 0, 0))
p.display.set_caption('window')

font = p.font.SysFont('Monocraft', 20)


origin = x0, y0 = WIDTH / 2, HEIGHT / 2  # This is the new origin
scale = 8e-2/100  # 1e-9 for only inner planets


def ball_xy(ball):
    # print(float(origin[0] + ball.pos.x / scale), float(origin[1] - ball.pos.y / scale))
    return float(origin[0] + ball.pos.x * scale), float(origin[1] - ball.pos.y * scale)


def draw_ball(ball):
    # print(earth.r/scale)
    p.draw.circle(screen, ball.color, ball_xy(ball), max(ball.r * scale, 1))


def time_convert(t):
    days = t/3600/24
    hours = days % 1 * 24
    minutes = hours % 1 * 60
    seconds = minutes % 1 * 60
    return int(days), int(hours), int(minutes), int(seconds)


def draw_arrow_to_asteroid(craft, asteroid, length):
    direction = asteroid.pos - craft.pos
    # print(mag(direction))
    vec = norm(direction)
    if 6*length > mag(direction*scale) - test_planet.r*scale:
        length = (mag(direction*scale) - test_planet.r*scale)/6
    x = WIDTH/2 + 5*vec.x*length
    y = HEIGHT/2 - 5*vec.y*length
    x2 = WIDTH/2 + 6*vec.x*length
    y2 = HEIGHT/2 - 6*vec.y*length
    p.draw.line(screen, (255, 255, 255), (x, y), (x2, y2), 5)


running = False
t = 0
dt = 10/4  # 500
# spacecraft = SpaceBall(Vec(100e2), Vec(), 2.822e6, 50, (255, 255, 255))
spacecraft = SpaceBall(Vec(20e6), Vec(), 2.822e6, 50, (255, 255, 255))
current_focus = spacecraft
# test_planet = SpaceBall(Vec(), Vec(), 1e12, 150e1, (0, 255, 0))
# test_planet.m = 4200*(math.pi*test_planet.r**3)*4/3
test_planet = SpaceBall(Vec(), Vec(), 6e22, 1.7e6, (0, 0, 255))  # 1.7e6
space_balls = [spacecraft, test_planet]
thruster_force = 20e6#5000
while True:
    for event in p.event.get():
        if event.type == p.QUIT:  # this refers to clicking on the "x"-close
            p.quit()
            sys.exit()
        elif event.type == p.KEYDOWN:
            # screen.fill((0, 0, 0))
            if event.key == p.K_SPACE:
                running = True
            if event.key == p.K_UP:
                scale *= 1.2
                screen.fill((0, 0, 0))
            if event.key == p.K_DOWN:
                scale /= 1.2
                screen.fill((0, 0, 0))
        elif event.type == p.KEYUP:
            spacecraft.thrust_force_vec = Vec()
        keys = p.key.get_pressed()
        if keys[p.K_w]:
            spacecraft.thrust_force_vec.y = thruster_force if not keys[p.K_LSHIFT] else thruster_force / 4
        if keys[p.K_s]:
            spacecraft.thrust_force_vec.y = -thruster_force if not keys[p.K_LSHIFT] else -thruster_force / 4
        if keys[p.K_a]:
            spacecraft.thrust_force_vec.x = -thruster_force if not keys[p.K_LSHIFT] else -thruster_force / 4
        if keys[p.K_d]:
            spacecraft.thrust_force_vec.x = thruster_force if not keys[p.K_LSHIFT] else thruster_force / 4
    screen.fill((0, 0, 0))  # comment/uncomment to enable/disable trail

    if current_focus is not None:
        origin = -current_focus.pos.x * scale + WIDTH / 2, current_focus.pos.y * scale + HEIGHT / 2
    for obj in space_balls:
        draw_ball(obj)
    if running:
        for i in range(1):  # steps multiple times every frame
            # scale = 1e2/spacecraft.distance_to(test_planet)
            # print(spacecraft.thrust_force)

            update_list_rk4(space_balls, dt)
            if spacecraft.colliding_with(test_planet):
                running = False
                print(mag(spacecraft.v))
            draw_arrow_to_asteroid(spacecraft, test_planet, 50)
            # print(spacecraft.a)
            # update_pairs(space_balls, dt)
            t += dt
    # print(t)
    p.display.flip()
    p.time.Clock().tick(100)  # caps frame rate at 100
