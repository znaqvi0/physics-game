import math
import pygame as p


class Animation:
    def __init__(self, n_frames, name, frame_time_ticks, pos, rotation, scale):
        self.n_frames = n_frames
        self.name = name
        self.frame_time = frame_time_ticks
        self.frames = []
        self.ticks = 0
        self.frame_index = 0
        self.pos = pos
        self.rotation = rotation
        self.scale = scale

        for i in range(self.n_frames):
            self.frames.append(p.image.load("assets/animations/" + name + str(i) + ".png").convert_alpha())

    def update(self):
        if self.ticks % self.frame_time == 0:
            if self.frame_index < self.n_frames:
                self.frame_index += 1
        self.ticks += 1
        if self.frame_index < self.n_frames:
            return self.frames[self.frame_index]
        else:
            return None


class Drawer:
    def __init__(self, screen, font, origin, scale, width, height, game, bg_filename):
        self.screen = screen
        self.font = font
        self.origin = origin
        self.scale = scale
        self.width = width
        self.height = height
        self.game = game

        # convert_alpha() improves game performance significantly
        self.player_image = p.image.load("assets/entities/game_ship.png").convert_alpha()
        self.player_moving_image = p.image.load("assets/entities/game_ship_moving.png").convert_alpha()
        self.player_dead_image = p.image.load("assets/entities/game_ship_destroyed2.png")
        self.enemy_image = p.image.load("assets/entities/enemy.png").convert_alpha()

        # background variables
        self.bg = p.image.load("assets/backgrounds/" + bg_filename).convert_alpha()
        self.scroll_x = 0
        self.scroll_y = 0
        self.bg_tiles_x = math.ceil(self.width / self.bg.get_width()) + 1  # 1 is the constant for removing buffering
        self.bg_tiles_y = math.ceil(self.height / self.bg.get_height()) + 1

        self.animations = []

    def transform_point(self, point):
        return float(self.origin[0] + point[0] * self.scale), float(self.origin[1] - point[1] * self.scale)

    def ball_xy(self, ball):
        return float(self.origin[0] + ball.pos.x * self.scale), float(self.origin[1] - ball.pos.y * self.scale)

    def draw_ball(self, ball):
        # print(earth.r/scale)
        p.draw.circle(self.screen, ball.color, self.ball_xy(ball), max(ball.r * self.scale, 1))

    def make_display(self, text, top_left, text_color=(255, 255, 255), bg_color=None):
        display = self.font.render(text, True, text_color, bg_color)
        display_rect = display.get_rect()
        display_rect.topleft = top_left
        return display, display_rect

    def make_display_top_right(self, text, top_right, text_color=(255, 255, 255), bg_color=(0, 0, 0)):
        display = self.font.render(text, True, text_color, bg_color)
        display_rect = display.get_rect()
        display_rect.topright = top_right
        return display, display_rect

    def blit_display_top_right(self, text, top_right, text_color=(255, 255, 255)):
        display, display_rect = self.make_display(text, (0, 0), text_color=text_color, bg_color=None)
        display_rect.topright = top_right
        self.screen.blit(display, display_rect)

    def blit_display_top_left(self, text, top_left, text_color=(255, 255, 255)):
        display, display_rect = self.make_display(text, (0, 0), text_color=text_color, bg_color=None)
        display_rect.topleft = top_left
        self.screen.blit(display, display_rect)

    def blit_display(self, make_display_result):
        display, display_rect = make_display_result
        self.screen.blit(display, display_rect)

    def blit_display_centered(self, text, y, text_color=(255, 255, 255)):
        display, display_rect = self.make_display(text, (0, 0), text_color=text_color, bg_color=None)
        display_rect.center = (self.width / 2, y)
        self.screen.blit(display, display_rect)

    def blit_display_center(self, text, center, text_color=(255, 255, 255)):
        display, display_rect = self.make_display(text, (0, 0), text_color=text_color, bg_color=None)
        display_rect.center = center
        self.screen.blit(display, display_rect)

    def draw_displays(self):
        self.blit_display(self.make_display("%3.0f fuel left" % self.game.player.fuel, (25, 25)))
        self.blit_display(self.make_display("%3.0f hp" % self.game.player.health, (25, 50)))
        self.blit_display(self.make_display("score: %3.0f" % self.game.score, (self.width - 175, 25)))

    def draw_terrain(self):
        visible_points = [self.transform_point(point) for point in self.game.points if
                          -100 <= self.transform_point(point)[0] <= self.width + 100]
        visible_points = [self.transform_point((-100000, -1000))] + visible_points + [self.transform_point((100000, -1000))]

        try:
            p.draw.polygon(self.screen, (70, 70, 110), visible_points, 0)
        except ValueError:
            pass

    def blit_rotate_center(self, image, topleft, angle):
        rotated_image = p.transform.rotate(image, angle)
        new_rect = rotated_image.get_rect(center=image.get_rect(topleft=topleft).center)
        self.screen.blit(rotated_image, new_rect)

    def draw_player(self):
        if not self.game.player.is_dead:
            current_image = self.player_image if not self.game.player.using_rockets else self.player_moving_image
        else:
            current_image = self.player_dead_image
        scaled_image = p.transform.scale(current_image, (self.game.player.r * self.scale * 2, self.game.player.r * self.scale * 2))
        image_pos = (self.width / 2 - scaled_image.get_width() / 2, self.height / 2 - scaled_image.get_height() / 2)
        self.blit_rotate_center(scaled_image, image_pos, self.game.player.angle - 90)

    def draw_enemies(self):
        for enemy in self.game.enemies:
            scaled_image = p.transform.scale(self.enemy_image, (enemy.r * self.scale * 2, enemy.r * self.scale * 2))
            image_pos = self.ball_xy(enemy)
            self.screen.blit(scaled_image, scaled_image.get_rect(center=image_pos))

    def draw_projectiles(self):
        for projectile in self.game.projectiles:
            p.draw.rect(self.screen, projectile.color, p.Rect(self.ball_xy(projectile), (projectile.r*2, projectile.r*2)))

    def draw_game(self):
        self.draw_enemies()
        self.draw_terrain()
        self.draw_displays()
        self.draw_player()

    def set_origin(self):
        if self.game.current_focus is not None:
            self.origin = -self.game.current_focus.pos.x * self.scale + self.width / 2, self.game.current_focus.pos.y * self.scale + self.height / 2

    def draw_main_menu(self):
        padded_difficulty = self.game.difficulty
        if padded_difficulty == "normal":
            padded_difficulty = "  normal"
        elif padded_difficulty == "hard":
            padded_difficulty = "    hard"
        elif padded_difficulty == "tutorial":
            padded_difficulty = "tutorial"

        self.blit_display_centered("difficulty: " + padded_difficulty, self.height / 4)  # height/2 - 200
        self.blit_display_centered("press left/right arrow to change difficulty", self.height * 0.1875)  # height/2-250
        self.blit_display_centered("press space to start", self.height * 0.375)  # height / 2 - 100

    def draw_tutorial(self):
        spacing = 275
        offset1 = 200

        self.blit_display_centered("objective: destroy your enemies", offset1 - 100, text_color=(0, 200, 100))
        self.blit_display_centered("the ground regenerates your health and fuel", offset1 - 50,
                                   text_color=(0, 200, 100))
        self.blit_display_centered("don't hit the ground too hard or get shot", offset1 - 25, text_color=(200, 50, 0))

        offset2 = 250
        self.blit_display_top_left("w", (self.width / 2 - spacing, offset2))
        self.blit_display_top_left("a/d", (self.width / 2 - spacing, offset2 + 25))
        self.blit_display_top_left("space", (self.width / 2 - spacing, offset2 + 50))
        self.blit_display_top_left("p", (self.width / 2 - spacing, offset2 + 75))
        self.blit_display_top_left("esc", (self.width / 2 - spacing, offset2 + 100))

        self.blit_display_top_right("use thrusters", (self.width / 2 + spacing, offset2))
        self.blit_display_top_right("rotate", (self.width / 2 + spacing, offset2 + 25))
        self.blit_display_top_right("shoot", (self.width / 2 + spacing, offset2 + 50))
        self.blit_display_top_right("pause/resume", (self.width / 2 + spacing, offset2 + 75))
        self.blit_display_top_right("main menu", (self.width / 2 + spacing, offset2 + 100))

    def draw_tiles(self):
        # source: https://www.geeksforgeeks.org/creating-a-scrolling-background-in-pygame/#
        # modified source to work in both x and y dimensions and changed how scroll amount is calculated
        i = -1
        while i < self.bg_tiles_x:
            j = -1
            while j < self.bg_tiles_y:
                self.screen.blit(self.bg,
                                 (self.bg.get_width() * i + self.scroll_x, self.bg.get_height() * j + self.scroll_y))
                j += 1
            i += 1
        # calculate scroll amount
        self.scroll_x = -((self.game.player.pos - self.game.player.pos0).x*self.scale // 5) % self.bg.get_width()
        self.scroll_y = ((self.game.player.pos - self.game.player.pos0).y*self.scale // 5) % self.bg.get_height()

    def draw_tiles_x_scroll(self):
        i = -1
        while i < self.bg_tiles_x:
            self.screen.blit(self.bg, (self.bg.get_width() * i + self.scroll_x, 0))
            i += 1
        # FRAME FOR SCROLLING
        self.scroll_x -= self.game.player.v.x / 100 if not self.game.player.is_dead else 0

        # RESET THE SCROLL FRAME
        if abs(self.scroll_x) > self.bg.get_width():
            self.scroll_x = 0

    def draw_animations(self):
        for animation in self.animations:
            frame = animation.update()
            if frame is not None:
                frame_scaled = p.transform.scale(frame, (frame.get_width()*animation.scale, frame.get_height()*animation.scale))
                # image_pos = (animation.x - frame_scaled.get_width() / 2, animation.y - frame_scaled.get_height() / 2)
                x, y = self.ball_xy(animation)
                image_pos = (x - frame_scaled.get_width()/2, y - frame_scaled.get_height()/2)
                self.blit_rotate_center(frame_scaled, image_pos, animation.rotation)
        self.animations = [anim for anim in self.animations if anim is not None]
