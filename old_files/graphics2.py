import datetime
import random
import time

from vectors import *
import pygame as p
import sys  # most commonly used to turn the interpreter off (shut down your game)
from engine import *
from entities import *

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
scale = 1


def ball_xy(ball):
    # print(float(origin[0] + ball.pos.x / scale), float(origin[1] - ball.pos.y / scale))
    return float(origin[0] + ball.pos.x * scale), float(origin[1] - ball.pos.y * scale)


def draw_ball(ball):
    # print(earth.r/scale)
    p.draw.circle(screen, ball.color, ball_xy(ball), max(ball.r * scale, 1))


def time_convert(t):
    days = t / 3600 / 24
    hours = days % 1 * 24
    minutes = hours % 1 * 60
    seconds = minutes % 1 * 60
    return int(days), int(hours), int(minutes), int(seconds)


def draw_arrow_to_asteroid(craft, asteroid, length):
    direction = asteroid.pos - craft.pos
    # print(mag(direction))
    vec = norm(direction)
    if 6 * length > mag(direction * scale) - planet.r * scale:
        length = (mag(direction * scale) - planet.r * scale) / 6
    x = WIDTH / 2 + 5 * vec.x * length
    y = HEIGHT / 2 - 5 * vec.y * length
    x2 = WIDTH / 2 + 6 * vec.x * length
    y2 = HEIGHT / 2 - 6 * vec.y * length
    p.draw.line(screen, (255, 255, 255), (x, y), (x2, y2), 5)


def transform_point(point):
    return float(origin[0] + point[0] * scale), float(origin[1] - point[1] * scale)


running = False
t = 0
dt = 0.1  # 500

planet = SpaceBall(Vec(), Vec(), 6e22, 1.7e6, (0, 0, 255))  # 7e22
planet.pos.y -= planet.r

player = SpaceBall(Vec(0, 15), Vec(), 2.822e6, 15, (255, 255, 255))
player.pos.y = 500

space_balls = [player, planet]
current_focus = player


def make_terrain(max_height, num_points):
    avg_x_range = num_points * (30 + 150 / 2)
    y_range = 150
    points = []
    x = -avg_x_range / 2
    y = 50
    prev_y_change = 0
    for i in range(num_points):
        x += random.randint(30, 100)
        y_change = random.randint(-y_range, y_range)
        new_y = y + (2 * prev_y_change + y_change) / 3  # weighted average
        prev_y_change = (2 * prev_y_change + y_change) / 3
        while new_y > max_height or new_y < 0:
            y_change = random.randint(-y_range, y_range)
            new_y = y + (2 * prev_y_change + y_change) / 3
            prev_y_change = (2 * prev_y_change + y_change) / 3
        y = new_y
        points.append((x, y))
    return points


points = make_terrain(500, 1000)
points = [(-100000, -10000)] + points + [(100000, -10000)]  # pad list with end points

player_image = p.image.load("../assets/entities/game_ship.png")
player_moving_image = p.image.load("../assets/entities/game_ship_moving.png")


def region_endpoints(visible_points, x):
    for i in range(len(visible_points)):
        try:
            left, right = visible_points[i], visible_points[i + 1]
            if left[0] < x < right[0]:
                return left, right
        except IndexError:
            return (0, 0), (1, 1)


def hitting_ground(obj):
    x, y = obj.pos.x, obj.pos.y
    left, right = region_endpoints(points, x)
    x1, x2, y1, y2 = left[0], right[0], left[1], right[1]
    slope = (y2 - y1) / (x2 - x1)
    # under_line = y - y1 < slope * (x - x1) + buffer
    a, b, c = slope, -1, y1 - slope * x1  # ax + by + c = 0
    dist = ((abs(a * x + b * y + c)) /
            math.sqrt(a * a + b * b))
    return obj.r >= dist, dist


def collide_with_ground(left, right, dist):
    global player_health, player_fuel
    x1, x2, y1, y2 = left[0], right[0], left[1], right[1]
    vec = Vec(x2 - x1, y2 - y1)
    normal = norm(vec.cross(Vec(0, 0, 1)))
    v_in_norm_direction = player.v.dot(normal) * normal
    player.pos -= (player.r - dist) * normal  # subtract intersection vector from position
    # spacecraft.v -= 2 * v_in_norm_direction
    # spacecraft.v *= 0.5
    v_in_plane_direction = player.v - v_in_norm_direction
    player.v = -0.5 * v_in_norm_direction + 0.3 * v_in_plane_direction
    if mag(v_in_norm_direction) >= 5:
        player_health -= mag(v_in_norm_direction) ** 1.5  # abs(spacecraft.v.y)*3
        if player_health <= 0:
            player_health = 0
            # running = False
            print("you died")

    # spacecraft.v *= 0.8
    # running = False
    player_fuel = min(1000, player_fuel + 0.2)


def check_ground():
    left, right = region_endpoints(points, player.pos.x)

    player_in_ground, dist = hitting_ground(player)
    if player_in_ground:
        collide_with_ground(left, right, dist)

    for proj in projectiles:
        if hitting_ground(proj)[0]:
            projectiles.remove(proj)


def make_display(text, top_left, text_color=(255, 255, 255), bg_color=(0, 0, 0)):
    display = font.render(text, True, text_color, bg_color)
    display_rect = display.get_rect()
    display_rect.topleft = top_left
    return display, display_rect


def draw_displays():
    fuel_display, fuel_display_rect = make_display("%3.0f fuel left" % player_fuel, (25, 25))
    screen.blit(fuel_display, fuel_display_rect)
    health_display, health_display_rect = make_display("%3.0f hp" % player_health, (25, 50))
    screen.blit(health_display, health_display_rect)


def draw_terrain():
    visible_points = [transform_point(point) for point in points if -100 <= transform_point(point)[0] <= WIDTH + 100]
    visible_points = [transform_point((-100000, -1000))] + visible_points + [transform_point((100000, -1000))]

    try:
        p.draw.polygon(screen, (100, 100, 100), visible_points, 0)
    except ValueError:
        pass


def blit_rotate_center(surf, image, topleft, angle):
    rotated_image = p.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft=topleft).center)
    surf.blit(rotated_image, new_rect)


def draw_player():
    global player_image, player_moving_image
    current_image = player_image if not using_rockets else player_moving_image
    scaled_image = p.transform.scale(current_image, (player.r * scale * 2, player.r * scale * 2))
    image_pos = (WIDTH / 2 - scaled_image.get_width() / 2, HEIGHT / 2 - scaled_image.get_height() / 2)
    blit_rotate_center(screen, scaled_image, image_pos, player_angle - 90)


def draw_everything():
    screen.fill((0, 0, 0))
    # draw_ball(spacecraft)
    # p.draw.line(screen, (255, 255, 255), (WIDTH/2, HEIGHT/2), (WIDTH/2+math.cos(math.radians(player_angle))*20, HEIGHT/2-math.sin(math.radians(player_angle))*20))
    for enemy in enemies:
        draw_ball(enemy)

    for projectile in projectiles:
        draw_ball(projectile)

    draw_terrain()
    draw_displays()
    draw_player()


def player_shoot():
    return Projectile(player.pos, 15*norm(Vec(math.cos(math.radians(player_angle)), math.sin(math.radians(player_angle)))), targeting_enemies=True)


enemies = []
projectiles = []
# enemies.append(Enemy(player.pos + Vec(300), 20))
# enemies.append(Enemy(player.pos - Vec(300, 100), 20))
# projectiles.append(enemies[0].shoot(spacecraft))

player_fuel = 1000
player_health = 200
thruster_force = 10e6  # 7.5e6?
player_angle = 90
angle_rate = 0
using_rockets = False

# floating fuel power ups + enemies that drop fuel. goal: get the highest score before being destroyed
# add damage splash next to spacecraft on hit
ticks = 0

while True:
    start = time.time_ns()
    for event in p.event.get():
        if event.type == p.QUIT:  # this refers to clicking on the "x"-close
            p.quit()
            sys.exit()
        elif event.type == p.KEYDOWN:
            # screen.fill((0, 0, 0))
            if event.key == p.K_SPACE:
                running = True
                projectiles.append(player_shoot())
            if event.key == p.K_UP:
                scale *= 1.2
                screen.fill((0, 0, 0))
            if event.key == p.K_DOWN:
                scale /= 1.2
                screen.fill((0, 0, 0))
        elif event.type == p.KEYUP:
            player.thrust_force_vec = Vec()
        keys = p.key.get_pressed()
        if player_fuel > 0:
            # if keys[p.K_w]:
            #     spacecraft.thrust_force.y = thruster_force if not keys[p.K_LSHIFT] else thruster_force / 2
            # if keys[p.K_s]:
            #     spacecraft.thrust_force.y = -thruster_force if not keys[p.K_LSHIFT] else -thruster_force / 2
            # if keys[p.K_a]:
            #     spacecraft.thrust_force.x = -thruster_force if not keys[p.K_LSHIFT] else -thruster_force / 2
            # if keys[p.K_d]:
            #     spacecraft.thrust_force.x = thruster_force if not keys[p.K_LSHIFT] else thruster_force / 2
            if keys[p.K_w]:
                player.thrust_force_vec = Vec(math.cos(math.radians(player_angle)),
                                              math.sin(math.radians(player_angle))) * thruster_force
            if keys[p.K_a] and keys[p.K_d]:
                angle_rate = 0
            elif keys[p.K_a]:
                angle_rate = 2
            elif keys[p.K_d]:
                angle_rate = -2
            else:
                angle_rate = 0
                using_rockets = False

    # if round(t % 0.3) == 0:
    if current_focus is not None:
        origin = -current_focus.pos.x * scale + WIDTH / 2, current_focus.pos.y * scale + HEIGHT / 2
    draw_everything()

    if running:
        update_list_rk4(space_balls, dt)
        t += dt
        check_ground()
        ticks += 1

        if ticks % 500 == 0:
            enemy_pos = player.pos + Vec(random.choice([-1, 1])*600, random.randint(0, 400))
            enemy = Enemy(enemy_pos, radius=20)
            while hitting_ground(enemy)[0]:
                enemy_pos = player.pos + Vec(random.choice([-1, 1]) * 600, random.randint(0, 400))
                enemy = Enemy(enemy_pos, radius=20)
            enemies.append(enemy)
        # if len(enemies) >= 1:
        #     print(enemies[0].num_ticks)
        for enemy in enemies:
            enemy.move(dt)
            if enemy.num_ticks % 400 == 0:
                projectiles.append(enemy.shoot(player))
            if enemy.num_ticks == 5000:
                enemies.remove(enemy)

        for proj in projectiles:
            proj.move(dt)
            if proj.targeting_player:
                if proj.distance_to(player) <= player.r:
                    player_health = max(0, player_health - 25)
                    projectiles.remove(proj)
            elif proj.targeting_enemies:
                for enemy in enemies:
                    if proj.distance_to(enemy) <= enemy.r:
                        enemies.remove(enemy)
                        player_fuel = min(1000, player_fuel + 300)
                        if proj in projectiles:
                            projectiles.remove(proj)

            if proj.distance_to(player) > 1000:
                projectiles.remove(proj)

        if mag(player.thrust_force_vec) != 0:
            player_fuel = max(0, player_fuel - 1)
            using_rockets = True
        else:
            using_rockets = False

        player_angle += angle_rate
    p.display.flip()
    p.time.Clock().tick(100)  # caps frame rate at 100
    # if running:
    #     print(1 / ((time.time_ns() - start) / 1e9), "fps")
