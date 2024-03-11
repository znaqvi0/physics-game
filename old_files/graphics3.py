import sys  # most commonly used to turn the interpreter off (shut down your game)
import time
import pygame as p

from enviroment import *

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


def transform_point(point):
    return float(origin[0] + point[0] * scale), float(origin[1] - point[1] * scale)


running = False
t = 0
dt = 0.1  # 500
ticks = 0
score = 0
high_score = 0

player_image = p.image.load("../assets/entities/game_ship.png")
player_moving_image = p.image.load("../assets/entities/game_ship_moving.png")
enemy_image = p.image.load("../assets/entities/enemy.png")


def init():
    planet = SpaceBall(Vec(), Vec(), 6e22, 1.7e6, (0, 0, 255))  # 7e22
    planet.pos.y -= planet.r

    player = Player(Vec(0, 15), Vec(), 2e6, 15, max_fuel=1000, max_health=200, thruster_force=7e6, angle=90)
    player.pos.y = 500

    space_balls = [player, planet]
    current_focus = player

    enemies = []
    projectiles = []

    points = make_terrain(500, 2000)
    points = [(-100000, -10000)] + points + [(100000, -10000)]  # pad list with end points
    return planet, player, space_balls, current_focus, enemies, projectiles, points


planet, player, space_balls, current_focus, enemies, projectiles, points = init()


def make_display(text, top_left, text_color=(255, 255, 255), bg_color=(0, 0, 0)):
    display = font.render(text, True, text_color, bg_color)
    display_rect = display.get_rect()
    display_rect.topleft = top_left
    return display, display_rect


def blit_display(make_display_result):
    display, display_rect = make_display_result
    screen.blit(display, display_rect)


def draw_displays():
    blit_display(make_display("%3.0f fuel left" % player.fuel, (25, 25)))
    blit_display(make_display("%3.0f hp" % player.health, (25, 50)))
    blit_display(make_display("score: %3.0f" % score, (WIDTH - 175, 25)))


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
    current_image = player_image if not player.using_rockets else player_moving_image
    scaled_image = p.transform.scale(current_image, (player.r * scale * 2, player.r * scale * 2))
    image_pos = (WIDTH / 2 - scaled_image.get_width() / 2, HEIGHT / 2 - scaled_image.get_height() / 2)
    blit_rotate_center(screen, scaled_image, image_pos, player.angle - 90)


def draw_enemies():
    global enemy_image
    for enemy in enemies:
        scaled_image = p.transform.scale(enemy_image, (enemy.r*scale*2, enemy.r*scale*2))
        image_pos = ball_xy(enemy)
        screen.blit(scaled_image, scaled_image.get_rect(center=image_pos))


def draw_everything():
    screen.fill((0, 0, 0))
    # draw_ball(spacecraft)
    # p.draw.line(screen, (255, 255, 255), (WIDTH/2, HEIGHT/2), (WIDTH/2+math.cos(math.radians(player.angle))*20, HEIGHT/2-math.sin(math.radians(player.angle))*20))
    # for enemy in enemies:
    #     draw_ball(enemy)

    for projectile in projectiles:
        draw_ball(projectile)

    draw_enemies()
    draw_terrain()
    draw_displays()
    draw_player()

# ideas
# create world boundary
# make mass depend on fuel amount

# lose fuel when hit?
# less accurate shots?
# health powerups on ground? -_-_-_-_-_-
# abilities w/ cooldowns: shotgun, heal (w/ downside), etc
# multiple enemy types? ex. dashing enemies, meteors, ground turrets, bombers
# 2 guns on ship sides instead of 1 in the center? cross player direction w/ <0, 0, +-1> to get sideways direction
# main menu w/ tutorial + play game
# "smart" enemy shooting: uses player vel to adjust shot direction
# game runs at around 100 ticks/sec
# add damage splash next to spacecraft on hit


last_player_shot_tick = 0
shot_cooldown = 40  # ticks
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
                # projectiles.append(player.shoot(40, inaccuracy=3))
                if player.is_dead:
                    planet, player, space_balls, current_focus, enemies, projectiles, points = init()
                    high_score = score
                    score = 0
                    ticks = 0
            if event.key == p.K_p:
                if not player.is_dead:
                    running = not running
            if event.key == p.K_UP:
                scale *= 1.2
                screen.fill((0, 0, 0))
            if event.key == p.K_DOWN:
                scale /= 1.2
                screen.fill((0, 0, 0))
        elif event.type == p.KEYUP:
            player.thrust_force_vec = Vec()
        keys = p.key.get_pressed()

        if player.fuel > 0 and keys[p.K_w]:
            player.using_rockets = True
        else:
            player.using_rockets = False

        if keys[p.K_a] and keys[p.K_d]:
            player.angle_rate = 0
        elif keys[p.K_a]:
            player.angle_rate = 2
        elif keys[p.K_d]:
            player.angle_rate = -2
        else:
            player.angle_rate = 0

        player.shooting = keys[p.K_SPACE]

    if current_focus is not None:
        origin = -current_focus.pos.x * scale + WIDTH / 2, current_focus.pos.y * scale + HEIGHT / 2
    draw_everything()

    if running:
        player.update_angle_thrust()
        # update_list_rk4(space_balls, dt)
        player.update_rk4(dt, space_balls, space_balls, space_balls, 0)
        t += dt
        check_ground(player, projectiles, points, fuel_regen=0.2, health_regen=0.1)
        ticks += 1

        if ticks % update_spawn_rate(ticks) == 0:  # % 10 for "insane mode"?
            create_enemy(player, enemies, points, 15)

        update_enemies(player, enemies, projectiles, dt, enemy_fire_rate=250, enemy_inaccuracy=7)
        score_change = update_projectiles(player, enemies, projectiles, dt)
        score += score_change

        if player.shooting:
            if ticks - last_player_shot_tick >= shot_cooldown:
                projectiles.append(player.shoot(40, inaccuracy=3))
                last_player_shot_tick = ticks

        if player.health == 0:
            player.is_dead = True
    if player.is_dead:
        death_display, death_display_rect = make_display("press space to retry", (0, 0), bg_color=(0, 0, 0))
        death_display_rect.center = (WIDTH/2, HEIGHT/2 - 100)
        screen.blit(death_display, death_display_rect)
        running = False

    p.display.flip()
    p.time.Clock().tick(100)  # caps frame rate at 100
    # if running:
    #     print(1 / ((time.time_ns() - start) / 1e9), "fps")
