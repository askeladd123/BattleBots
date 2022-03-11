import pygame
import random
from sys import exit
from copy import copy
from copy import deepcopy

from common import get_neighbours
from common import get_unit_vector
from common import Animation
from common import AnimationTrail
from common import random_legal_position
from player import Player
from tiles import Tiles

speed = 1000
functions = []
players = []
bullet_positions = []


def register_ai(function):
    functions.append(function)


class Input:
    def __init__(self, player):
        self._player = player
        self.position = deepcopy(player.position)
        self.game_state = deepcopy(player.tiles.array)
        self.ammo = deepcopy(player.ammo)
        self.bullet_positions = deepcopy(bullet_positions)

        self.enemy_positions = []
        global players
        for player in players:
            self.enemy_positions.append(deepcopy(player.position))
        self.enemy_positions.remove(player.position)

        self.enemies = len(self.enemy_positions)
        self.bullets = len(self.bullet_positions)

    def is_legal(self, direction):
        """
        :param direction: "up", "down", "right", "left"
        :return: True if the given direction has an empty tile
        """
        if direction == "up":
            return self._player.tiles.is_empty(self._player.position[0], self._player.position[1] - 1)

        if direction == "down":
            return self._player.tiles.is_empty(self._player.position[0], self._player.position[1] + 1)

        if direction == "right":
            return self._player.tiles.is_empty(self._player.position[0] + 1, self._player.position[1])

        if direction == "left":
            return self._player.tiles.is_empty(self._player.position[0] - 1, self._player.position[1])

        return False


def start(real_players=0):
    if len(functions) == 0:
        exit("You need at least one ai to play... Make one by overriding this function:\n"
             "@BattleBots.register_ai\n"
             "def super_ai(input, output):")

    if len(functions) < real_players:
        real_players = len(functions)

    if 2 < real_players:
        print("Can't have more than 2 real players, btw")
        real_players = 2

    pygame.init()
    pygame.display.set_caption("BattleBots")
    pygame.time.set_timer(pygame.USEREVENT, speed)

    # create a surface on screen that has the size of 240 x 180
    HEIGHT = 640
    WIDTH = HEIGHT * 2
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    # ok
    tiles = Tiles(WIDTH, HEIGHT)
    animations = []

    global players
    for function in functions:
        players.append(Player(function, tiles))

    for player in players:
        player.position = random_legal_position(tiles)
        tiles.register(player.position)
        player.font = pygame.font.SysFont(None, 24).render(str(players.index(player) + 1), True,
                                                           pygame.Color(190, 200, 180))

    pang_image_sequence = [pygame.image.load("res/pang/0000.png"),
                           pygame.image.load("res/pang/0000.png"),
                           pygame.image.load("res/pang/0001.png"),
                           pygame.image.load("res/pang/0002.png"),
                           pygame.image.load("res/pang/0003.png"),
                           pygame.image.load("res/pang/0004.png")
                           ]

    bullet_image = pygame.transform.scale(pygame.image.load("res/kule.png"), (tiles.TILE_WIDTH, tiles.TILE_HEIGHT))
    global bullet_positions
    bullet_positions = [random_legal_position(tiles)]
    counter = 0

    # main loop
    running = True
    while running:
        # event handling, gets all event from the event queue
        for event in pygame.event.get():
            # only do something if the event is of type QUIT
            if event.type == pygame.QUIT:
                # change the value to False, to exit the main loop
                running = False

            if event.type == pygame.USEREVENT:
                if 8 < counter:
                    counter = 0
                    if len(bullet_positions) < len(players):
                        bullet_positions.append(random_legal_position(tiles))
                else:
                    counter += 1
                for player in players:

                    command = None
                    if 1 < len(players):
                        command = player.function(Input(player))

                    if command is None:
                        continue
                    command = command.lower()

                    if command in ["up", "down", "right", "left"]:
                        player.move(command)

                    if "shoot" in command:
                        for direction in ["up", "down", "right", "left", "straight"]:
                            if direction == "straight":
                                player.shoot()
                            if direction in command:
                                player.shoot(direction)
                                break

            if event.type == pygame.KEYDOWN:
                if 0 < len(players) and (real_players == 1 or real_players == 2):
                    if event.key == pygame.K_UP:
                        players[0].move("up")
                    if event.key == pygame.K_DOWN:
                        players[0].move("down")
                    if event.key == pygame.K_LEFT:
                        players[0].move("left")
                    if event.key == pygame.K_RIGHT:
                        players[0].move("right")
                    if event.key == pygame.K_SPACE:
                        players[0].shoot()

                if real_players == 2 and 1 < len(players):
                    if event.key == pygame.K_w:
                        players[1].move("up")
                    if event.key == pygame.K_s:
                        players[1].move("down")
                    if event.key == pygame.K_a:
                        players[1].move("left")
                    if event.key == pygame.K_d:
                        players[1].move("right")
                    if event.key == pygame.K_h:
                        players[1].shoot()

        impact_locations = []

        for player in players:
            if player.ammo < player.ammo_max and player.position in bullet_positions:
                player.ammo += 1
                bullet_positions.remove(player.position)

            if player.has_shot:
                impact = player.extract_impact_location()

                impact_locations.append(impact)

                animations.append(AnimationTrail(
                    (
                        tiles.world_position_x(player.position[0]) + int(tiles.TILE_WIDTH / 2),
                        tiles.world_position_y(player.position[1]) + int(tiles.TILE_HEIGHT / 2)
                    ),
                    (
                        tiles.world_position_x(impact[0]) + int(tiles.TILE_WIDTH / 2),
                        tiles.world_position_y(impact[1]) + int(tiles.TILE_HEIGHT / 2)
                    ), 0.5))
                animations.append(Animation(pang_image_sequence,
                                            tiles.world_position(impact),
                                            (tiles.TILE_WIDTH, tiles.TILE_HEIGHT),
                                            player.rotation - 90,
                                            0.05
                                            ))

        for location in impact_locations:
            neighbours = get_neighbours(location)
            neighbours.append(list(location))
            new_players = []
            for player in players:
                if player.position in neighbours:
                    tiles.unregister(player.position)
                else:
                    new_players.append(player)
            players = new_players
        # DRAW = = =
        screen.fill((30, 20, 20))

        for position in bullet_positions:
            screen.blit(bullet_image, tiles.world_position(position))

        for animation in animations:
            animation.draw(screen)
            animation.current_frame += animation.speed
            if animation.is_done:
                animations.remove(animation)

        tiles.draw(screen)

        for player in players:
            player.draw(screen)

        pygame.display.update()
