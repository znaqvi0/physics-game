from drawer import Animation
from entities import *
from sounds import *

boom_anim_scale = 1.3
boom_frame_time = 6


def region_endpoints(points, x):
    for i in range(len(points)):
        try:
            left, right = points[i], points[i + 1]
            if left[0] < x < right[0]:
                return left, right
        except IndexError:
            return (0, 0), (1, 1)


def make_terrain(max_height, num_points):
    # randomly generate terrain
    x_range = (30, 100)
    avg_x_range = num_points * ((x_range[0] + x_range[1]) / 2)
    y_range = 150
    points = []
    x = -avg_x_range / 2
    y = 50
    prev_y_change = 0
    for i in range(num_points):
        x += random.randint(x_range[0], x_range[1])
        y_change = random.randint(-y_range, y_range)
        new_y = y + (2 * prev_y_change + y_change) / 3  # weighted average of prev and new
        prev_y_change = (2 * prev_y_change + y_change) / 3

        while new_y > max_height or new_y < 0:  # try again until new point is within y range
            y_change = random.randint(-y_range, y_range)
            new_y = y + (2 * prev_y_change + y_change) / 3
            prev_y_change = (2 * prev_y_change + y_change) / 3

        y = new_y
        points.append((x, y))
    return points


def hitting_ground(obj, points):
    x, y = obj.pos.x, obj.pos.y
    left, right = region_endpoints(points, x)
    x1, x2, y1, y2 = left[0], right[0], left[1], right[1]
    slope = (y2 - y1) / (x2 - x1)
    a, b, c = slope, -1, y1 - slope * x1  # ax + by + c = 0
    dist = ((abs(a * x + b * y + c)) /
            math.sqrt(a * a + b * b))  # distance from point to line
    return obj.r >= dist, dist


def check_ground(player, projectiles, points, fuel_regen=0.2, health_regen=0.1):
    left, right = region_endpoints(points, player.pos.x)

    player_in_ground, dist = hitting_ground(player, points)
    if player_in_ground:
        player.collide_with_ground(left, right, dist, fuel_regen, health_regen)

    new_animations = []
    for proj in projectiles:
        if hitting_ground(proj, points)[0]:
            projectiles.remove(proj)

            new_animations.append(
                Animation(6, "explosion", boom_frame_time, proj.pos, random.randint(0, 360), boom_anim_scale))
            play_sound(enemy_hit_file, enemy_hit_volume / 4)

    return new_animations


def create_enemy(player, enemies, points, radius):
    while True:
        angle = math.radians(random.randint(30, 150))
        rand_vec = Vec(math.cos(angle), math.sin(angle))
        enemy_pos = player.pos + rand_vec * random.randint(800, 1200)
        enemy = Enemy(enemy_pos, radius=radius)
        if not hitting_ground(enemy, points)[0]:
            break
    enemies.append(enemy)


def update_enemies(player, enemies, projectiles, points, dt, enemy_fire_rate=200, enemy_inaccuracy=3,
                   smart_enemies=False):
    for enemy in enemies:

        enemy.move(player, dt, smart_enemies)
        if hitting_ground(enemy, points)[0]:
            enemy.pos -= enemy.v * dt

        if enemy.num_ticks % enemy_fire_rate == 0:  # if enemy should fire
            if smart_enemies:
                projectiles.append(enemy.smart_shoot(player, inaccuracy=enemy_inaccuracy*0.2))  # more accurate when smart
            else:
                projectiles.append(enemy.shoot(player, inaccuracy=enemy_inaccuracy))

        if enemy.num_ticks == 5000:
            enemies.remove(enemy)

        if mag(player.pos - enemy.pos) <= player.r + enemy.r:  # player colliding with enemy
            player.health = max(0, player.health - 30)
            if enemy in enemies:
                enemies.remove(enemy)


def update_projectiles(player, enemies, projectiles, dt):
    score_change = 0
    new_animations = []
    for proj in projectiles:
        proj.move(dt)

        if proj.targeting_player:
            if proj.distance_to(player) <= player.r:
                player.health = max(0, player.health - 25)
                projectiles.remove(proj)

                new_animations.append(
                    Animation(6, "explosion", boom_frame_time, proj.pos, random.randint(0, 360), boom_anim_scale))
                play_sound(player_hit_file, player_hit_volume)
                play_sound(enemy_hit_file, enemy_hit_volume / 1.5)

        elif proj.targeting_enemies:
            for enemy in enemies:
                if proj.distance_to(enemy) <= enemy.r:
                    enemies.remove(enemy)
                    player.fuel = min(1000, player.fuel + 150)
                    score_change += 100
                    if proj in projectiles:
                        projectiles.remove(proj)

                    new_animations.append(
                        Animation(6, "explosion", boom_frame_time, proj.pos, random.randint(0, 360), boom_anim_scale))
                    play_sound(enemy_hit_file, enemy_hit_volume)

        if proj.distance_to(player) > 1000:
            projectiles.remove(proj)
        elif proj.num_ticks == 500:  # limit projectile lifetime to reduce lag caused by too many of them
            projectiles.remove(proj)
    return score_change, new_animations


def update_spawn_rate(ticks):
    if ticks >= 24000:
        return 25
    elif ticks >= 22000:
        return 50  # larger jump
    elif ticks >= 20000:
        return 100
    elif ticks >= 18000:
        return 125
    elif ticks >= 16000:
        return 150
    elif ticks >= 14000:
        return 175
    elif ticks >= 12000:
        return 200  # larger jump
    elif ticks >= 10000:
        return 250
    elif ticks >= 8000:
        return 275
    elif ticks >= 6000:
        return 300  # larger jump
    elif ticks >= 4000:
        return 350
    elif ticks >= 2000:
        return 375
    else:
        return 400


def check_boundary(player, left_bound, right_bound, dt):
    if player.pos.x >= right_bound or player.pos.x <= left_bound:
        player.pos -= player.v * dt
        player.v.x *= -1
