import sys  # most commonly used to turn the interpreter off (shut down your game)

from drawer import *
from enviroment import *

# Initializes pygame - see documentation
p.init()

# Constants - sets the size of the window
WIDTH = 1000
HEIGHT = 800

screen = p.display.set_mode((WIDTH, HEIGHT), p.RESIZABLE)
screen.fill((0, 0, 0))
p.display.set_caption('window')

font = p.font.SysFont('Monocraft', 20)

origin = x0, y0 = WIDTH / 2, HEIGHT / 2  # This is the new origin
scale = 1

high_score = 0


class Game:
    def __init__(self, difficulty):
        self.difficulty = difficulty

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
        if difficulty == "normal":
            self.init()
        elif difficulty == "hard":
            self.init()
        elif difficulty == "tutorial":
            self.init()

    def init(self):
        self.planet = SpaceBall(Vec(), Vec(), 6e22, 1.7e6, (0, 0, 255))
        self.planet.pos.y -= self.planet.r

        self.player = Player(Vec(0, 15), Vec(), 2e6, 15, max_fuel=1000, max_health=200, thruster_force=7e6, angle=90)
        self.player.pos.y = 600  # 500

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

        while True:  # spawn player on the ground by bringing it down until it hits the ground
            self.player.pos.y -= 0.1
            if hitting_ground(self.player, self.points)[0]:
                break

    def normal_update(self, smart_enemies, animations):
        # animations variable is the list to which new animations will be added
        self.player.update_angle_thrust()
        self.player.update_rk4(self.dt, self.space_balls, self.space_balls, self.space_balls, 0)
        self.t += self.dt
        ground_anims = check_ground(self.player, self.projectiles, self.points, fuel_regen=0.2, health_regen=0.1)
        self.ticks += 1

        # create enemy every [spawn rate] ticks (rate increases over time)
        if self.ticks % update_spawn_rate(self.ticks) == 0:
            create_enemy(self.player, self.enemies, self.points, radius=15)

        update_enemies(self.player, self.enemies, self.projectiles, self.points, self.dt, enemy_fire_rate=250,
                       enemy_inaccuracy=7, smart_enemies=smart_enemies)

        score_change, hit_anims = update_projectiles(self.player, self.enemies, self.projectiles, self.dt)
        self.score += score_change

        # add animations to be drawn later
        for anim in hit_anims:
            animations.append(anim)
        for anim in ground_anims:
            animations.append(anim)

        if self.player.shooting:
            if self.ticks - self.last_player_shot_tick >= self.player.shot_cooldown:  # shoot if cooldown is done
                self.projectiles.append(self.player.shoot(40, inaccuracy=3))
                self.last_player_shot_tick = self.ticks

        if self.player.health <= 0:  # death
            self.player.is_dead = True
            self.player.shooting = False


# background found at https://deep-fold.itch.io/space-background-generator

# game runs at around 100 ticks/sec
difficulties = ["tutorial", "normal", "hard"]
difficulty_index = 0  # can be cycled using left/right arrow keys
difficulty = difficulties[difficulty_index]  # initialize difficulty

game = Game(difficulty)
drawer = Drawer(screen, font, origin, scale, WIDTH, HEIGHT, game, bg_filename="space_tile_1000x800_0.png")

running = False
on_main_menu = True
paused = False

# world boundaries
left_bound = game.points[1][0]
right_bound = game.points[-2][0]

p.mixer.music.load("assets/sounds/password-infinity.mp3")
p.mixer.music.set_volume(0.5 * master_volume)
p.mixer.music.play(-1)  # (-1) = repeat music indefinitely


while True:
    for event in p.event.get():
        if event.type == p.QUIT:  # this refers to clicking on the "x"-close
            p.quit()
            sys.exit()

        elif event.type == p.VIDEORESIZE:
            # allow window resizing
            drawer.screen = p.display.set_mode((event.w, event.h), p.RESIZABLE)
            drawer.width, drawer.height = event.w, event.h
            drawer.draw_game()

        elif event.type == p.KEYDOWN:

            if event.key == p.K_SPACE:
                if not paused:
                    running = True
                if game.player.is_dead:
                    high_score = game.score
                    game.init()  # restart game by resetting variables

            if event.key == p.K_p:
                # pause game
                if not game.player.is_dead and not on_main_menu:
                    running = not running
                    paused = not paused
                    drawer.blit_display_centered("paused (press p to resume)", HEIGHT / 2 - 100)

            # main menu controls:
            if on_main_menu:
                if event.key == p.K_RIGHT:
                    difficulty_index = (difficulty_index + 1) % len(difficulties)  # cycle difficulty
                elif event.key == p.K_LEFT:
                    difficulty_index = (difficulty_index - 1) % len(difficulties)  # cycle difficulty
                game.difficulty = difficulties[difficulty_index]

            if event.key == p.K_ESCAPE:
                # go to main menu & reset game
                if not on_main_menu:
                    on_main_menu = True
                    paused = False
                    game.init()
                    running = False

        keys = p.key.get_pressed()

        game.player.using_rockets = game.player.fuel > 0 and keys[p.K_w]

        # check a & d keys and set player rotation rate accordingly
        if keys[p.K_a] and not keys[p.K_d]:
            game.player.angle_rate = 2
        elif keys[p.K_d] and not keys[p.K_a]:
            game.player.angle_rate = -2
        else:
            game.player.angle_rate = 0  # no change if both or neither are pressed

        game.player.shooting = keys[p.K_SPACE]

    drawer.set_origin()

    on_main_menu = not running and not game.player.is_dead and not paused

    if not paused:
        if game.ticks % 2 == 0:  # draw most things every other iteration
            drawer.draw_tiles()
            drawer.draw_game()
        drawer.draw_projectiles()  # projectiles are choppy if drawn every other iteration

    if on_main_menu:
        drawer.draw_main_menu()

    if running:
        if game.difficulty == "normal":
            game.normal_update(smart_enemies=False, animations=drawer.animations)
            check_boundary(game.player, left_bound, right_bound, game.dt)

        elif game.difficulty == "hard":
            game.normal_update(smart_enemies=True, animations=drawer.animations)
            check_boundary(game.player, left_bound, right_bound, game.dt)

        elif game.difficulty == "tutorial":
            # same as normal mode but shows game controls
            drawer.draw_tutorial()
            game.normal_update(smart_enemies=False, animations=drawer.animations)
            check_boundary(game.player, left_bound, right_bound, game.dt)

    drawer.draw_animations()

    if game.player.is_dead:
        drawer.blit_display_centered("press space to retry", HEIGHT / 2 - 100)
        drawer.blit_display_centered("esc for main menu", HEIGHT / 2 - 75)
        if running:
            drawer.animations.append(Animation(6, "explosion", 10, game.player.pos, 0, 3))  # death animation
            play_sound("assets/sounds/boom1.mp3", volume=player_death_volume)  # death sound
        running = False

    p.display.flip()
    p.time.Clock().tick(100)  # caps frame rate at 100
