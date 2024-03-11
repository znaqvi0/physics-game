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
# t = 0
# dt = 0.1  # 500
# ticks = 0
# score = 0
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


# planet, player, space_balls, current_focus, enemies, projectiles, points = init()

class Game:
    def __init__(self, difficulty, mode):
        self.difficulty = difficulty
        self.mode = mode

        self.t = 0
        self.dt = 0.1
        self.ticks = 0
        self.score = 0
        self.last_player_shot_tick = 0
        self.planet = None
        self.player = None
        self.space_balls = None
        self.current_focus = None
        self.enemies = []
        self.projectiles = []
        self.points = None
        if mode == "normal":
            if difficulty == "normal":
                self.normal_init()
            elif difficulty == "hard":
                self.normal_init()
            elif difficulty == "tutorial":
                self.normal_init()

    def normal_init(self):
        self.planet = SpaceBall(Vec(), Vec(), 6e22, 1.7e6, (0, 0, 255))  # 7e22
        self.planet.pos.y -= self.planet.r

        self.player = Player(Vec(0, 15), Vec(), 2e6, 15, max_fuel=1000, max_health=200, thruster_force=7e6, angle=90)
        self.player.pos.y = 500
        self.player.shot_cooldown = 40

        self.space_balls = [self.player, self.planet]
        self.current_focus = self.player

        self.enemies = []
        self.projectiles = []

        self.points = make_terrain(500, 2000)
        self.points = [(-100000, -10000)] + self.points + [(100000, -10000)]  # pad list with end points
        self.score = 0
        self.ticks = 0
        self.t = 0
        self.last_player_shot_tick = 0
        # return planet, player, space_balls, current_focus, enemies, projectiles, points

    def normal_update(self, smart_enemies):
        self.player.update_angle_thrust()
        # update_list_rk4(space_balls, dt)
        self.player.update_rk4(self.dt, self.space_balls, self.space_balls, self.space_balls, 0)
        self.t += self.dt
        check_ground(self.player, self.projectiles, self.points, fuel_regen=0.2, health_regen=0.1)
        self.ticks += 1

        if self.ticks % update_spawn_rate(self.ticks) == 0:  # % 10 for "insane mode"?
            create_enemy(self.player, self.enemies, self.points, 15)
        if smart_enemies:
            update_enemies(self.player, self.enemies, self.projectiles, self.dt, enemy_fire_rate=250, enemy_inaccuracy=5, smart_enemies=True)
        else:
            update_enemies(self.player, self.enemies, self.projectiles, self.dt, enemy_fire_rate=250, enemy_inaccuracy=7)
        score_change = update_projectiles(self.player, self.enemies, self.projectiles, self.dt)
        self.score += score_change

        if self.player.shooting:
            if self.ticks - self.last_player_shot_tick >= self.player.shot_cooldown:
                self.projectiles.append(self.player.shoot(40, inaccuracy=3))
                self.last_player_shot_tick = self.ticks

        if self.player.health == 0:
            self.player.is_dead = True
            self.player.shooting = False


def make_display(text, top_left, text_color=(255, 255, 255), bg_color=(0, 0, 0)):
    display = font.render(text, True, text_color, bg_color)
    display_rect = display.get_rect()
    display_rect.topleft = top_left
    return display, display_rect


def blit_display(make_display_result):
    display, display_rect = make_display_result
    screen.blit(display, display_rect)


def blit_display_centered(text, y, text_color=(255, 255, 255)):
    display, display_rect = make_display(text, (0, 0), text_color=text_color, bg_color=(0, 0, 0))
    display_rect.center = (WIDTH / 2, y)
    screen.blit(display, display_rect)


def draw_displays():
    blit_display(make_display("%3.0f fuel left" % game.player.fuel, (25, 25)))
    blit_display(make_display("%3.0f hp" % game.player.health, (25, 50)))
    blit_display(make_display("score: %3.0f" % game.score, (WIDTH - 175, 25)))


def draw_terrain():
    visible_points = [transform_point(point) for point in game.points if -100 <= transform_point(point)[0] <= WIDTH + 100]
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
    current_image = player_image if not game.player.using_rockets else player_moving_image
    scaled_image = p.transform.scale(current_image, (game.player.r * scale * 2, game.player.r * scale * 2))
    image_pos = (WIDTH / 2 - scaled_image.get_width() / 2, HEIGHT / 2 - scaled_image.get_height() / 2)
    blit_rotate_center(screen, scaled_image, image_pos, game.player.angle - 90)


def draw_enemies():
    global enemy_image
    for enemy in game.enemies:
        scaled_image = p.transform.scale(enemy_image, (enemy.r*scale*2, enemy.r*scale*2))
        image_pos = ball_xy(enemy)
        screen.blit(scaled_image, scaled_image.get_rect(center=image_pos))


def draw_everything():
    screen.fill((0, 0, 0))

    for projectile in game.projectiles:
        draw_ball(projectile)

    draw_enemies()
    draw_terrain()
    draw_displays()
    draw_player()

# ideas
# create world boundary

# lose fuel when hit?
# health powerups on ground?
# abilities w/ cooldowns: shotgun, heal (w/ downside), etc
# multiple enemy types? ex. dashing enemies, meteors, ground turrets, bombers
# reformat tutorial screen
# spawn player on ground
# game runs at around 100 ticks/sec
# add damage splash next to spacecraft on hit
# last_player_shot_tick = 0
# shot_cooldown = 40  # ticks


difficulties = ["tutorial", "normal", "hard"]
difficulty_index = 0
difficulty = difficulties[difficulty_index]
mode = "normal"
game = Game(difficulty, mode)
on_main_menu = True
paused = False

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
                if game.player.is_dead:
                    high_score = game.score
                    game.normal_init()
            if event.key == p.K_p:
                if not game.player.is_dead and not on_main_menu:
                    running = not running
                    paused = not paused
            if event.key == p.K_UP:
                scale *= 1.2
                screen.fill((0, 0, 0))
            if event.key == p.K_DOWN:
                scale /= 1.2
                screen.fill((0, 0, 0))
            # main menu controls:
            if on_main_menu:
                if event.key == p.K_RIGHT:
                    difficulty_index = (difficulty_index + 1) % len(difficulties)
                    difficulty = difficulties[difficulty_index]
            if event.key == p.K_ESCAPE:
                if not on_main_menu:
                    on_main_menu = True
                    game.normal_init()
                    running = False
        elif event.type == p.KEYUP:
            game.player.thrust_force_vec = Vec()
        keys = p.key.get_pressed()

        if game.player.fuel > 0 and keys[p.K_w]:
            game.player.using_rockets = True
        else:
            game.player.using_rockets = False

        if keys[p.K_a] and keys[p.K_d]:
            game.player.angle_rate = 0
        elif keys[p.K_a]:
            game.player.angle_rate = 2
        elif keys[p.K_d]:
            game.player.angle_rate = -2
        else:
            game.player.angle_rate = 0

        game.player.shooting = keys[p.K_SPACE]

    if game.current_focus is not None:
        origin = -game.current_focus.pos.x * scale + WIDTH / 2, game.current_focus.pos.y * scale + HEIGHT / 2

    on_main_menu = not running and not game.player.is_dead and not paused
    draw_everything()
    if on_main_menu:
        if difficulty == "normal":
            padded_difficulty = "  normal"
        elif difficulty == "hard":
            padded_difficulty = "    hard"
        elif difficulty == "tutorial":
            padded_difficulty = "tutorial"
        blit_display_centered("difficulty: " + padded_difficulty, HEIGHT / 2 - 200)
        blit_display_centered("press <right arrow> to change difficulty", HEIGHT/2 - 250)
        blit_display_centered("press space to start", HEIGHT/2 - 100)
    if paused:
        blit_display_centered("paused (press p to resume)", HEIGHT/2-100)

    if running:
        if difficulty == "normal":
            game.normal_update(smart_enemies=False)
        elif difficulty == "hard":
            game.normal_update(smart_enemies=True)
        elif difficulty == "tutorial":
            offset1 = 200
            blit_display_centered("objective: destroy your enemies", offset1-100, text_color=(0, 200, 100))
            blit_display_centered("the ground regenerates your health and fuel", offset1-50, text_color=(0, 200, 100))
            blit_display_centered("don't hit the ground too hard or get shot", offset1-25, text_color=(200, 50, 0))
            offset2 = 250
            blit_display_centered("w: engage thrusters", offset2)
            blit_display_centered("a: turn counterclockwise", offset2 + 25)
            blit_display_centered("d: turn clockwise", offset2 + 50)
            blit_display_centered("space bar: shoot", offset2 + 75)
            blit_display_centered("p: pause/resume game", offset2 + 100)
            blit_display_centered("esc: main menu", offset2 + 125)
        # print(game.player.v)
        # print(game.player.a)
    if game.player.is_dead:
        blit_display_centered("press space to retry", HEIGHT/2 - 100)
        running = False

    p.display.flip()
    p.time.Clock().tick(100)  # caps frame rate at 100
    # if running:
    #     print(1 / ((time.time_ns() - start) / 1e9), "fps")
