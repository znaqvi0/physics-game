import pygame as p

master_volume = 0.5

# sounds files + relative volumes
player_hit_file = "assets/sounds/player_hit.wav"
player_hit_volume = 0.5

enemy_hit_file = "assets/sounds/boom1.mp3"
enemy_hit_volume = 1

player_death_file = enemy_hit_file
player_death_volume = 2


def play_sound(file, volume):
    sound = p.mixer.Sound(file)
    sound.set_volume(volume*master_volume)
    p.mixer.Sound.play(sound)
