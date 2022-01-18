import os
import pygame
import random
import sys


class myRect(pygame.Rect):
    def __init__(self, left, top, width, height, type):
        pygame.Rect.__init__(self, left, top, width, height)
        self.type = type

class Timer(object):
    def __init__(self):
        self.timers = []

    def add(self, interval, f, repeat = -1):
        options = {
            "interval" : interval,
            "callback" : f,
            "repeat" : repeat,
            "times" : 0,
            "time" : 0,
        }
        self.timers.append(options)

    def update(self, time_passed):
        for timer in self.timers:
            timer["time"] += time_passed
            if timer["time"] > timer["interval"]:
                timer["time"] -= timer["interval"]
                timer["times"] += 1
                if timer["repeat"] > -1 and timer["times"] == timer["repeat"]:
                    self.timers.remove(timer)
                try:
                    timer["callback"]()
                except:
                    try:
                        self.timers.remove(timer)
                    except:
                        pass


class Castle():
    (STATE_STANDING, STATE_DESTROYED, STATE_EXPLODING) = range(3)
    def __init__(self):
        global sprites
        self.img_undamaged = sprites.subsurface(0, 15*2, 16*2, 16*2)
        self.img_destroyed = sprites.subsurface(16*2, 15*2, 16*2, 16*2)

        self.rect = pygame.Rect(12*16, 24*16, 32, 32)
        self.rebuild()

    def draw(self):
        global screen

        screen.blit(self.image, self.rect.topleft)

        if self.state == self.STATE_EXPLODING:
            if not self.explosion.active:
                self.state = self.STATE_DESTROYED
                del self.explosion
            else:
                self.explosion.draw()

    def rebuild(self):
        self.state = self.STATE_STANDING
        self.image = self.img_undamaged
        self.active = True

    def destroy(self):
        self.state = self.STATE_EXPLODING
        self.explosion = Explosion(self.rect.topleft)
        self.image = self.img_destroyed
        self.active = False

class Bonus():
    # граната - уничтожает врагов
    # шлем - щит
    # лопата - рандомная сила + 500 очков
    # танк - доп жизнь
    # часы - заморозка времени  
    (BONUS_GRENADE, BONUS_HELMET, BONUS_SHOVEL, BONUS_STAR, BONUS_TANK, BONUS_TIMER) = range(6)

    def __init__(self, level):

        global sprites
        self.level = level
        self.active = True
        self.visible = True
        self.rect = pygame.Rect(random.randint(0, 384), random.randint(0, 384), 32, 32)

        self.bonus = random.choice([
            self.BONUS_GRENADE,
            self.BONUS_HELMET,
            self.BONUS_SHOVEL,
            self.BONUS_STAR,
            self.BONUS_TANK,
            self.BONUS_TIMER
        ])

        self.image = sprites.subsurface(16 * 2 * self.bonus, 32 * 2, 16 * 2, 15 * 2)

    def draw(self):
        global screen
        if self.visible:
            screen.blit(self.image, self.rect.topleft)

    def toggleVisibility(self):
        self.visible = not self.visible


class Bullet():
    # константы для передвижения
    (DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT) = range(4)

    # для пуль
    (STATE_REMOVED, STATE_ACTIVE, STATE_EXPLODING) = range(3)

    (OWNER_PLAYER, OWNER_ENEMY) = range(2)

    def __init__(self, level, position, direction, damage = 100, speed = 5):
        global sprites

        self.level = level
        self.direction = direction
        self.damage = damage
        self.owner = None
        self.owner_class = None

        # 1-нормальная
        # 2-уничтожать сталь
        self.power = 1
        self.image = sprites.subsurface(75*2, 74*2, 3*2, 4*2)

        # повороты пуль относительно движения
        if direction == self.DIR_UP:
            self.rect = pygame.Rect(position[0] + 11, position[1] - 8, 6, 8)
        elif direction == self.DIR_RIGHT:
            self.image = pygame.transform.rotate(self.image, 270)
            self.rect = pygame.Rect(position[0] + 26, position[1] + 11, 8, 6)
        elif direction == self.DIR_DOWN:
            self.image = pygame.transform.rotate(self.image, 180)
            self.rect = pygame.Rect(position[0] + 11, position[1] + 26, 6, 8)
        elif direction == self.DIR_LEFT:
            self.image = pygame.transform.rotate(self.image, 90)
            self.rect = pygame.Rect(position[0] - 8 , position[1] + 11, 8, 6)

        self.explosion_images = [
            sprites.subsurface(0, 80 * 2, 32 * 2, 32 * 2),
            sprites.subsurface(32 * 2, 80 * 2, 32 * 2, 32 * 2),
        ]
        self.speed = speed
        self.state = self.STATE_ACTIVE

    def draw(self):
        global screen
        if self.state == self.STATE_ACTIVE:
            screen.blit(self.image, self.rect.topleft)
        elif self.state == self.STATE_EXPLODING:
            self.explosion.draw()

    def update(self):
        global castle, players, enemies, bullets

        if self.state == self.STATE_EXPLODING:
            if not self.explosion.active:
                self.destroy()
                del self.explosion

        if self.state != self.STATE_ACTIVE:
            return

        # передвижение
        if self.direction == self.DIR_UP:
            self.rect.topleft = [self.rect.left, self.rect.top - self.speed]
            if self.rect.top < 0:
                if play_sounds and self.owner == self.OWNER_PLAYER:
                    sounds["steel"].play()
                self.explode()
                return
        elif self.direction == self.DIR_RIGHT:
            self.rect.topleft = [self.rect.left + self.speed, self.rect.top]
            if self.rect.left > (416 - self.rect.width):
                if play_sounds and self.owner == self.OWNER_PLAYER:
                    sounds["steel"].play()
                self.explode()
                return
        elif self.direction == self.DIR_DOWN:
            self.rect.topleft = [self.rect.left, self.rect.top + self.speed]
            if self.rect.top > (416 - self.rect.height):
                if play_sounds and self.owner == self.OWNER_PLAYER:
                    sounds["steel"].play()
                self.explode()
                return
        elif self.direction == self.DIR_LEFT:
            self.rect.topleft = [self.rect.left - self.speed, self.rect.top]
            if self.rect.left < 0:
                if play_sounds and self.owner == self.OWNER_PLAYER:
                    sounds["steel"].play()
                self.explode()
                return

        has_collided = False
        # проверка столкновений пуль со стеной
        rects = self.level.obstacle_rects
        collisions = self.rect.collidelistall(rects)
        if collisions != []:
            for i in collisions:
                if self.level.hitTile(rects[i].topleft, self.power, self.owner == self.OWNER_PLAYER):
                    has_collided = True
        if has_collided:
            self.explode()
            return

        # с другими пулями
        for bullet in bullets:
            if self.state == self.STATE_ACTIVE and bullet.owner != self.owner and bullet != self and self.rect.colliderect(bullet.rect):
                self.destroy()
                self.explode()
                return

        # с игроками
        for player in players:
            if player.state == player.STATE_ALIVE and self.rect.colliderect(player.rect):
                if player.bulletImpact(self.owner == self.OWNER_PLAYER, self.damage, self.owner_class):
                    self.destroy()
                    return

        # с врагами
        for enemy in enemies:
            if enemy.state == enemy.STATE_ALIVE and self.rect.colliderect(enemy.rect):
                if enemy.bulletImpact(self.owner == self.OWNER_ENEMY, self.damage, self.owner_class):
                    self.destroy()
                    return

        # с троном
        if castle.active and self.rect.colliderect(castle.rect):
            castle.destroy()
            self.destroy()
            return

    def explode(self):
        # ВЗРЫВЫ
        global screen
        if self.state != self.STATE_REMOVED:
            self.state = self.STATE_EXPLODING
            self.explosion = Explosion([self.rect.left-13, self.rect.top-13], None, self.explosion_images)

    def destroy(self):
        self.state = self.STATE_REMOVED


class Label():  #надпись
    def __init__(self, position, text = "", duration = None):
        self.position = position
        self.active = True
        self.text = text
        self.font = pygame.font.SysFont("Arial", 13)
        if duration != None:
            gtimer.add(duration, lambda :self.destroy(), 1)

    def draw(self):
        global screen
        screen.blit(self.font.render(self.text, False, (200,200,200)), [self.position[0]+4, self.position[1]+8])

    def destroy(self):
        self.active = False


class Explosion():  # еще взрывы, только теперь анимации
    def __init__(self, position, interval = None, images = None):
        global sprites
        self.position = [position[0]-16, position[1]-16]
        self.active = True

        if interval == None:
            interval = 100

        if images == None:
            images = [
                sprites.subsurface(0, 80*2, 32*2, 32*2),
                sprites.subsurface(32*2, 80*2, 32*2, 32*2),
                sprites.subsurface(64*2, 80*2, 32*2, 32*2)
            ]
        images.reverse()
        self.images = [] + images
        self.image = self.images.pop()
        gtimer.add(interval, lambda :self.update(), len(self.images) + 1)

    def draw(self):
        global screen
        screen.blit(self.image, self.position)

    def update(self):
        if len(self.images) > 0:
            self.image = self.images.pop()
        else:
            self.active = False

class Level():
    # константы для класса
    (TILE_EMPTY, TILE_BRICK, TILE_STEEL, TILE_WATER, TILE_GRASS, TILE_FROZE) = range(6)
    TILE_SIZE = 16
    def __init__(self, level_nr = None):
        global sprites
        # число врагов max
        self.max_active_enemies = 4
        # cпрайты
        tile_images = [
            pygame.Surface((8*2, 8*2)),
            sprites.subsurface(48*2, 64*2, 8*2, 8*2),
            sprites.subsurface(48*2, 72*2, 8*2, 8*2),
            sprites.subsurface(56*2, 72*2, 8*2, 8*2),
            sprites.subsurface(64*2, 64*2, 8*2, 8*2),
            sprites.subsurface(64*2, 64*2, 8*2, 8*2),
            sprites.subsurface(72*2, 64*2, 8*2, 8*2),
            sprites.subsurface(64*2, 72*2, 8*2, 8*2)
        ]
        self.tile_empty = tile_images[0]
        self.tile_brick = tile_images[1]
        self.tile_steel = tile_images[2]
        self.tile_grass = tile_images[3]
        self.tile_water = tile_images[4]
        self.tile_water1= tile_images[4]
        self.tile_water2= tile_images[5]
        self.tile_froze = tile_images[6]

        self.obstacle_rects = []

        level_nr = 1 if level_nr == None else level_nr % 35
        if level_nr == 0:
            level_nr = 35

        self.loadLevel(level_nr)
        self.obstacle_rects = []
        self.updateObstacleRects()

        gtimer.add(400, lambda :self.toggleWaves())

    def hitTile(self, pos, power = 1, sound = False):  
        # столкновение со спрайтами
        global play_sounds, sounds
        for tile in self.mapr:
            if tile.topleft == pos:
                if tile.type == self.TILE_BRICK:
                    if play_sounds and sound:
                        sounds["brick"].play()
                    self.mapr.remove(tile)
                    self.updateObstacleRects()
                    return True
                elif tile.type == self.TILE_STEEL:
                    if play_sounds and sound:
                        sounds["steel"].play()
                    if power == 2:
                        self.mapr.remove(tile)
                        self.updateObstacleRects()
                    return True
                else:
                    return False

    def toggleWaves(self):  # а зачем это добавили? волны
        if self.tile_water == self.tile_water1:
            self.tile_water = self.tile_water2
        else:
            self.tile_water = self.tile_water1


    def loadLevel(self, level_nr=1):
        # загрузка уровня
        filename = "levels/"+str(level_nr)
        if (not os.path.isfile(filename)):
            return False
        f = open(filename, "r")
        data = f.read().split("\n")
        self.mapr = []
        x, y = 0, 0
        for row in data:
            for ch in row:
                if ch == "#":
                    self.mapr.append(myRect(x, y, self.TILE_SIZE, self.TILE_SIZE, self.TILE_BRICK))
                elif ch == "@":
                    self.mapr.append(myRect(x, y, self.TILE_SIZE, self.TILE_SIZE, self.TILE_STEEL))
                elif ch == "~":
                    self.mapr.append(myRect(x, y, self.TILE_SIZE, self.TILE_SIZE, self.TILE_WATER))
                elif ch == "%":
                    self.mapr.append(myRect(x, y, self.TILE_SIZE, self.TILE_SIZE, self.TILE_GRASS))
                elif ch == "-":
                    self.mapr.append(myRect(x, y, self.TILE_SIZE, self.TILE_SIZE, self.TILE_FROZE))
                x += self.TILE_SIZE
            x = 0
            y += self.TILE_SIZE
        return True


    def draw(self, tiles = None):
        # рисуем карту
        global screen

        if tiles == None:
            tiles = [TILE_BRICK, TILE_STEEL, TILE_WATER, TILE_GRASS, TILE_FROZE]

        for tile in self.mapr:
            if tile.type in tiles:
                if tile.type == self.TILE_BRICK:
                    screen.blit(self.tile_brick, tile.topleft)
                elif tile.type == self.TILE_STEEL:
                    screen.blit(self.tile_steel, tile.topleft)
                elif tile.type == self.TILE_WATER:
                    screen.blit(self.tile_water, tile.topleft)
                elif tile.type == self.TILE_FROZE:
                    screen.blit(self.tile_froze, tile.topleft)
                elif tile.type == self.TILE_GRASS:
                    screen.blit(self.tile_grass, tile.topleft)

    def updateObstacleRects(self):
        # типа проверяем столкновения блоков и трона        
        global castle
        self.obstacle_rects = [castle.rect]
        for tile in self.mapr:
            if tile.type in (self.TILE_BRICK, self.TILE_STEEL, self.TILE_WATER):
                self.obstacle_rects.append(tile)

    def buildFortress(self, tile):
        # стены вокруг трона
        positions = [
            (11 * self.TILE_SIZE, 23 * self.TILE_SIZE),
            (11 * self.TILE_SIZE, 24 * self.TILE_SIZE),
            (11 * self.TILE_SIZE, 25 * self.TILE_SIZE),
            (14 * self.TILE_SIZE, 23 * self.TILE_SIZE),
            (14 * self.TILE_SIZE, 24 * self.TILE_SIZE),
            (14 * self.TILE_SIZE, 25 * self.TILE_SIZE),
            (12 * self.TILE_SIZE, 23 * self.TILE_SIZE),
            (13 * self.TILE_SIZE, 23 * self.TILE_SIZE)
        ]

        obsolete = []

        for i, rect in enumerate(self.mapr):
            if rect.topleft in positions:
                obsolete.append(rect)
        for rect in obsolete:
            self.mapr.remove(rect)

        for pos in positions:
            self.mapr.append(myRect(pos[0], pos[1], self.TILE_SIZE, self.TILE_SIZE, tile))

        self.updateObstacleRects()

class Tank():
    # константы для танков
    (DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT) = range(4)
    (STATE_SPAWNING, STATE_DEAD, STATE_ALIVE, STATE_EXPLODING) = range(4)
    (SIDE_PLAYER, SIDE_ENEMY) = range(2)

    def __init__(self, level, side, position = None, direction = None, filename = None):
        global sprites
        self.health = 100
        # если какой-то даун по своим стреляет
        self.paralised = False
        # пауза
        self.paused = False
        # бонус-щит
        self.shielded = False
        self.speed = 2
        self.max_active_bullets = 1

        # friend or foe
        self.side = side

        # flashing state. 0-off, 1-on
        self.flash = 0

        # 0 - ничего
        # 1 - быстро стреляет
        # 2 - 2 пули одновременно
        # 3 - бить сталь
        self.superpowers = 0  # не доделал
        self.bonus = None
        self.controls = [pygame.K_SPACE, pygame.K_UP, pygame.K_RIGHT, pygame.K_DOWN, pygame.K_LEFT]
        self.pressed = [False] * 4

        self.shield_images = [
            sprites.subsurface(0, 48*2, 16*2, 16*2),
            sprites.subsurface(16*2, 48*2, 16*2, 16*2)
        ]

        self.shield_image = self.shield_images[0]
        self.shield_index = 0

        self.spawn_images = [
            sprites.subsurface(32*2, 48*2, 16*2, 16*2),
            sprites.subsurface(48*2, 48*2, 16*2, 16*2)
        ]
        self.spawn_image = self.spawn_images[0]
        self.spawn_index = 0

        self.level = level

        if position != None:
            self.rect = pygame.Rect(position, (26, 26))
        else:
            self.rect = pygame.Rect(0, 0, 26, 26)

        if direction == None:
            self.direction = random.choice([self.DIR_RIGHT, self.DIR_DOWN, self.DIR_LEFT])
        else:
            self.direction = direction

        self.state = self.STATE_SPAWNING

        # появление начало
        self.timer_uuid_spawn = gtimer.add(100, lambda :self.toggleSpawnImage())

        # появления конец
        self.timer_uuid_spawn_end = gtimer.add(1000, lambda :self.endSpawning())

    def endSpawning(self):
        self.state = self.STATE_ALIVE
        gtimer.destroy(self.timer_uuid_spawn_end)


    def toggleSpawnImage(self):
        if self.state != self.STATE_SPAWNING:
            gtimer.destroy(self.timer_uuid_spawn)
            return
        self.spawn_index += 1
        if self.spawn_index >= len(self.spawn_images):
            self.spawn_index = 0
        self.spawn_image = self.spawn_images[self.spawn_index]

    def toggleShieldImage(self):
        if self.state != self.STATE_ALIVE:
            gtimer.destroy(self.timer_uuid_shield)
            return
        if self.shielded:
            self.shield_index += 1
            if self.shield_index >= len(self.shield_images):
                self.shield_index = 0
            self.shield_image = self.shield_images[self.shield_index]


    def draw(self):
        # рисуем танки
        global screen
        if self.state == self.STATE_ALIVE:
            screen.blit(self.image, self.rect.topleft)
            if self.shielded:
                screen.blit(self.shield_image, [self.rect.left-3, self.rect.top-3])
        elif self.state == self.STATE_EXPLODING:
            self.explosion.draw()
        elif self.state == self.STATE_SPAWNING:
            screen.blit(self.spawn_image, self.rect.topleft)

    def explode(self):
        # взрываем танки
        if self.state != self.STATE_DEAD:
            self.state = self.STATE_EXPLODING
            self.explosion = Explosion(self.rect.topleft)

            if self.bonus:
                self.spawnBonus()

    def fire(self, forced = False):
        # стреляем танками
        global bullets, labels

        if self.state != self.STATE_ALIVE:
            gtimer.destroy(self.timer_uuid_fire)
            return False
        if self.paused:
            return False
        if not forced:
            active_bullets = 0
            for bullet in bullets:
                if bullet.owner_class == self and bullet.state == bullet.STATE_ACTIVE:
                    active_bullets += 1
            if active_bullets >= self.max_active_bullets:
                return False

        bullet = Bullet(self.level, self.rect.topleft, self.direction)

        if self.superpowers > 0:
            bullet.speed = 8
        if self.superpowers > 2:
            bullet.power = 2
        if self.side == self.SIDE_PLAYER:
            bullet.owner = self.SIDE_PLAYER
        else:
            bullet.owner = self.SIDE_ENEMY
            self.bullet_queued = False

        bullet.owner_class = self
        bullets.append(bullet)
        return True

    def rotate(self, direction, fix_position = True):
        # повороты танка
        self.direction = direction
        if direction == self.DIR_UP:
            self.image = self.image_up
        elif direction == self.DIR_RIGHT:
            self.image = self.image_right
        elif direction == self.DIR_DOWN:
            self.image = self.image_down
        elif direction == self.DIR_LEFT:
            self.image = self.image_left

        if fix_position:
            new_x = self.nearest(self.rect.left, 8) + 3
            new_y = self.nearest(self.rect.top, 8) + 3
            if (abs(self.rect.left - new_x) < 5):
                self.rect.left = new_x
            if (abs(self.rect.top - new_y) < 5):
                self.rect.top = new_y

    def turnAround(self):
        # повороты по противоположным сторонам
        if self.direction in (self.DIR_UP, self.DIR_RIGHT):
            self.rotate(self.direction + 2, False)
        else:
            self.rotate(self.direction - 2, False)

    def update(self, time_passed):
        # обновления таймеров при проигрыше
        if self.state == self.STATE_EXPLODING:
            if not self.explosion.active:
                self.state = self.STATE_DEAD
                del self.explosion

    def nearest(self, num, base):
        return int(round(num / (base * 1.0)) * base)


    def bulletImpact(self, friendly_fire = False, damage = 100, tank = None):
        # true - пуля уничтожает
        global play_sounds, sounds

        if self.shielded:
            return True

        if not friendly_fire:
            self.health -= damage
            if self.health < 1:
                if self.side == self.SIDE_ENEMY:
                    tank.trophies["enemy"+str(self.type)] += 1
                    points = (self.type+1) * 100
                    tank.score += points
                    if play_sounds:
                        sounds["explosion"].play()

                    labels.append(Label(self.rect.topleft, str(points), 500))

                self.explode()
            return True
        # событие при поподании по союзнику
        if self.side == self.SIDE_ENEMY:  # если враг - ничего не происходит, потому что они постоянно это делаеют
            return False  # тупые боты
        elif self.side == self.SIDE_PLAYER:
            if not self.paralised:
                self.setParalised(True)  # если друг выстрелил в тебя
                self.timer_uuid_paralise = gtimer.add(10000, lambda :self.setParalised(False), 1)
            return True

    def setParalised(self, paralised = True):
        if self.state != self.STATE_ALIVE:
            gtimer.destroy(self.timer_uuid_paralise)
            return
        self.paralised = paralised

class Enemy(Tank):
    (TYPE_BASIC, TYPE_FAST, TYPE_POWER, TYPE_ARMOR) = range(4)
    def __init__(self, level, type, position = None, direction = None, filename = None):
        Tank.__init__(self, level, type, position = None, direction = None, filename = None)
        global enemies, sprites
        # могут ли стрелять, false - могут
        self.bullet_queued = False

        # выбопр такнка
        if len(level.enemies_left) > 0:
            self.type = level.enemies_left.pop()
        else:
            self.state = self.STATE_DEAD
            return

        if self.type == self.TYPE_BASIC:
            self.speed = 1
        elif self.type == self.TYPE_FAST:
            self.speed = 3
        elif self.type == self.TYPE_POWER:
            self.superpowers = 1
        elif self.type == self.TYPE_ARMOR:
            self.health = 400

        # бонус на быструю атаку врагу 1 к 5
        if random.randint(1, 5) == 1:
            self.bonus = True
            for enemy in enemies:
                if enemy.bonus:
                    self.bonus = False
                    break

        images = [
            sprites.subsurface(32 * 2, 0, 13 * 2, 15 * 2),
            sprites.subsurface(48 * 2, 0, 13 * 2, 15 * 2),
            sprites.subsurface(64 * 2, 0, 13 * 2, 15 * 2),
            sprites.subsurface(80 * 2, 0, 13 * 2, 15 * 2),
            sprites.subsurface(32 * 2, 16 * 2, 13 * 2, 15 * 2),
            sprites.subsurface(48 * 2, 16 * 2, 13 * 2, 15 * 2),
            sprites.subsurface(64 * 2, 16 * 2, 13 * 2, 15 * 2),
            sprites.subsurface(80 * 2, 16 * 2, 13 * 2, 15 * 2)
        ]

        self.image = images[self.type+0]

        self.image_up = self.image
        self.image_left = pygame.transform.rotate(self.image, 90)
        self.image_down = pygame.transform.rotate(self.image, 180)
        self.image_right = pygame.transform.rotate(self.image, 270)

        if self.bonus:
            self.image1_up = self.image_up;
            self.image1_left = self.image_left
            self.image1_down = self.image_down
            self.image1_right = self.image_right

            self.image2 = images[self.type+4]
            self.image2_up = self.image2;
            self.image2_left = pygame.transform.rotate(self.image2, 90)
            self.image2_down = pygame.transform.rotate(self.image2, 180)
            self.image2_right = pygame.transform.rotate(self.image2, 270)

        self.rotate(self.direction, False)

        if position == None:
            self.rect.topleft = self.getFreeSpawningPosition()
            if not self.rect.topleft:
                self.state = self.STATE_DEAD
                return

        # путь танка, почти рандомный
        self.path = self.generatePath(self.direction)

        # задержка перед выстрелом
        self.timer_uuid_fire = gtimer.add(1000, lambda :self.fire())
        if self.bonus:
            self.timer_uuid_flash = gtimer.add(200, lambda :self.toggleFlash())

    def toggleFlash(self):
        # взорвался
        if self.state not in (self.STATE_ALIVE, self.STATE_SPAWNING):
            gtimer.destroy(self.timer_uuid_flash)
            return
        self.flash = not self.flash
        if self.flash:
            self.image_up = self.image2_up
            self.image_right = self.image2_right
            self.image_down = self.image2_down
            self.image_left = self.image2_left
        else:
            self.image_up = self.image1_up
            self.image_right = self.image1_right
            self.image_down = self.image1_down
            self.image_left = self.image1_left
        self.rotate(self.direction, False)

    def spawnBonus(self):
        global bonuses

        if len(bonuses) > 0:
            return
        bonus = Bonus(self.level)
        bonuses.append(bonus)
        gtimer.add(500, lambda :bonus.toggleVisibility())
        gtimer.add(10000, lambda :bonuses.remove(bonus), 1)


    def getFreeSpawningPosition(self):
        global players, enemies

        available_positions = [[(self.level.TILE_SIZE * 2 - self.rect.width) / 2, (self.level.TILE_SIZE * 2 - self.rect.height) / 2],
            [12 * self.level.TILE_SIZE + (self.level.TILE_SIZE * 2 - self.rect.width) / 2, (self.level.TILE_SIZE * 2 - self.rect.height) / 2],
            [24 * self.level.TILE_SIZE + (self.level.TILE_SIZE * 2 - self.rect.width) / 2,  (self.level.TILE_SIZE * 2 - self.rect.height) / 2]]
        random.shuffle(available_positions)
        for pos in available_positions:
            enemy_rect = pygame.Rect(pos, [26, 26])
            # колизия с другими врагами
            collision = False
            for enemy in enemies:
                if enemy_rect.colliderect(enemy.rect):
                    collision = True
                    continue
            if collision:
                continue
            # колизия с игроками
            collision = False
            for player in players:
                if enemy_rect.colliderect(player.rect):
                    collision = True
                    continue
            if collision:
                continue
            return pos
        return False

    def move(self):
        global players, enemies, bonuses
        if self.state != self.STATE_ALIVE or self.paused or self.paralised:
            return
        if self.path == []:
            self.path = self.generatePath(None, True)
        new_position = self.path.pop(0)
        # передвижение
        if self.direction == self.DIR_UP:
            if new_position[1] < 0:
                self.path = self.generatePath(self.direction, True)
                return
        elif self.direction == self.DIR_RIGHT:
            if new_position[0] > (416 - 26):
                self.path = self.generatePath(self.direction, True)
                return
        elif self.direction == self.DIR_DOWN:
            if new_position[1] > (416 - 26):
                self.path = self.generatePath(self.direction, True)
                return
        elif self.direction == self.DIR_LEFT:
            if new_position[0] < 0:
                self.path = self.generatePath(self.direction, True)
                return

        new_rect = pygame.Rect(new_position, [26, 26])

        # колизия с блоками
        if new_rect.collidelist(self.level.obstacle_rects) != -1:
            self.path = self.generatePath(self.direction, True)
            return
        # колизия с врагами
        for enemy in enemies:
            if enemy != self and new_rect.colliderect(enemy.rect):
                self.turnAround()
                self.path = self.generatePath(self.direction)
                return
        # колизия с игроками
        for player in players:
            if new_rect.colliderect(player.rect):
                self.turnAround()
                self.path = self.generatePath(self.direction)
                return
        # колизия с бонусом
        for bonus in bonuses:
            if new_rect.colliderect(bonus.rect):
                bonuses.remove(bonus)
        # если все нормально, то двигаемся
        self.rect.topleft = new_rect.topleft


    def update(self, time_passed):
        Tank.update(self, time_passed)
        if self.state == self.STATE_ALIVE and not self.paused:
            self.move()
    def generatePath(self, direction = None, fix_direction = False):
        # создаем путь танку
        all_directions = [self.DIR_UP, self.DIR_RIGHT, self.DIR_DOWN, self.DIR_LEFT]

        if direction == None:
            if self.direction in [self.DIR_UP, self.DIR_RIGHT]:
                opposite_direction = self.direction + 2
            else:
                opposite_direction = self.direction - 2
            directions = all_directions
            random.shuffle(directions)
            directions.remove(opposite_direction)
            directions.append(opposite_direction)
        else:
            if direction in [self.DIR_UP, self.DIR_RIGHT]:
                opposite_direction = direction + 2
            else:
                opposite_direction = direction - 2

            if direction in [self.DIR_UP, self.DIR_RIGHT]:
                opposite_direction = direction + 2
            else:
                opposite_direction = direction - 2
            directions = all_directions
            random.shuffle(directions)
            directions.remove(opposite_direction)
            directions.remove(direction)
            directions.insert(0, direction)
            directions.append(opposite_direction)

        # шаг врага
        x = int(round(self.rect.left / 16))
        y = int(round(self.rect.top / 16))
        new_direction = None
        for direction in directions:
            if direction == self.DIR_UP and y > 1:
                new_pos_rect = self.rect.move(0, -8)
                if new_pos_rect.collidelist(self.level.obstacle_rects) == -1:
                    new_direction = direction
                    break
            elif direction == self.DIR_RIGHT and x < 24:
                new_pos_rect = self.rect.move(8, 0)
                if new_pos_rect.collidelist(self.level.obstacle_rects) == -1:
                    new_direction = direction
                    break
            elif direction == self.DIR_DOWN and y < 24:
                new_pos_rect = self.rect.move(0, 8)
                if new_pos_rect.collidelist(self.level.obstacle_rects) == -1:
                    new_direction = direction
                    break
            elif direction == self.DIR_LEFT and x > 1:
                new_pos_rect = self.rect.move(-8, 0)
                if new_pos_rect.collidelist(self.level.obstacle_rects) == -1:
                    new_direction = direction
                    break

        # разворачиваемся назад если никуда не можем пойти
        if new_direction == None:
            new_direction = opposite_direction
        # если нормально двигается
        if fix_direction and new_direction == self.direction:
            fix_direction = False
        self.rotate(new_direction, fix_direction)
        positions = []
        x = self.rect.left
        y = self.rect.top
        if new_direction in (self.DIR_RIGHT, self.DIR_LEFT):
            axis_fix = self.nearest(y, 16) - y
        else:
            axis_fix = self.nearest(x, 16) - x
        axis_fix = 0
        pixels = self.nearest(random.randint(1, 12) * 32, 32) + axis_fix + 3
        if new_direction == self.DIR_UP:
            for px in range(0, pixels, self.speed):
                positions.append([x, y - px])
        elif new_direction == self.DIR_RIGHT:
            for px in range(0, pixels, self.speed):
                positions.append([x + px, y])
        elif new_direction == self.DIR_DOWN:
            for px in range(0, pixels, self.speed):
                positions.append([x, y + px])
        elif new_direction == self.DIR_LEFT:
            for px in range(0, pixels, self.speed):
                positions.append([x - px, y])

        return positions



class Player(Tank):
    def __init__(self, level, type, position = None, direction = None, filename = None):
        Tank.__init__(self, level, type, position = None, direction = None, filename = None)
        global sprites
        if filename == None:
            filename = (0, 0, 16*2, 16*2)
        self.start_position = position
        self.start_direction = direction
        # кол-во жизней
        self.lives = 5
        # очки
        self.score = 0

        # для подсчета резульатов
        self.trophies = {
            "bonus" : 0,
            "enemy0" : 0,
            "enemy1" : 0,
            "enemy2" : 0,
            "enemy3" : 0
        }

        self.image = sprites.subsurface(filename)
        self.image_up = self.image
        self.image_left = pygame.transform.rotate(self.image, 90)
        self.image_down = pygame.transform.rotate(self.image, 180)
        self.image_right = pygame.transform.rotate(self.image, 270)

        if direction == None:
            self.rotate(self.DIR_UP, False)
        else:
            self.rotate(direction, False)

    def move(self, direction):
        global players, enemies, bonuses

        if self.state == self.STATE_EXPLODING:
            if not self.explosion.active:
                self.state = self.STATE_DEAD
                del self.explosion
        if self.state != self.STATE_ALIVE:
            return
        # крутимся
        if self.direction != direction:
            self.rotate(direction)
        if self.paralised:
            return
        # двигаемся
        if direction == self.DIR_UP:
            new_position = [self.rect.left, self.rect.top - self.speed]
            if new_position[1] < 0:
                return
        elif direction == self.DIR_RIGHT:
            new_position = [self.rect.left + self.speed, self.rect.top]
            if new_position[0] > (416 - 26):
                return
        elif direction == self.DIR_DOWN:
            new_position = [self.rect.left, self.rect.top + self.speed]
            if new_position[1] > (416 - 26):
                return
        elif direction == self.DIR_LEFT:
            new_position = [self.rect.left - self.speed, self.rect.top]
            if new_position[0] < 0:
                return
        player_rect = pygame.Rect(new_position, [26, 26])

        # колизия с блоками
        if player_rect.collidelist(self.level.obstacle_rects) != -1:
            return
        # колизия с игроками
        for player in players:
            if player != self and player.state == player.STATE_ALIVE and player_rect.colliderect(player.rect) == True:
                return
        # колизия с врагами
        for enemy in enemies:
            if player_rect.colliderect(enemy.rect) == True:
                return
        # колизия с бонусами
        for bonus in bonuses:
            if player_rect.colliderect(bonus.rect) == True:
                self.bonus = bonus
        # если ни с чем не встретились, то продолжаем двигаться
        self.rect.topleft = (new_position[0], new_position[1])

    def reset(self):
        # возрождение
        self.rotate(self.start_direction, False)
        self.rect.topleft = self.start_position
        self.superpowers = 0
        self.max_active_bullets = 1
        self.health = 100
        self.paralised = False
        self.paused = False
        self.pressed = [False] * 4
        self.state = self.STATE_ALIVE

class Game():  # 
    (DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT) = range(4)
    TILE_SIZE = 16
    def __init__(self):
        global screen, sprites, play_sounds, sounds
        # позиция окна
        os.environ['SDL_VIDEO_WINDOW_POS'] = 'center'
        if play_sounds:
            pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption("Battle City")
        size = width, height = 480, 416
        if "-f" in sys.argv[1:]:
            screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        else:
            screen = pygame.display.set_mode(size)
        self.clock = pygame.time.Clock()
        sprites = pygame.transform.scale(pygame.image.load("images/sprites.gif"), [192, 224])

        pygame.display.set_icon(sprites.subsurface(0, 0, 26, 26))
        if play_sounds:
            pygame.mixer.init(44100, -16, 1, 512)
            sounds["start"] = pygame.mixer.Sound("sounds/gamestart.ogg")
            sounds["end"] = pygame.mixer.Sound("sounds/gameover.ogg")
            sounds["score"] = pygame.mixer.Sound("sounds/score.ogg")
            sounds["fire"] = pygame.mixer.Sound("sounds/fire.ogg")
            sounds["bonus"] = pygame.mixer.Sound("sounds/bonus.ogg")
            sounds["explosion"] = pygame.mixer.Sound("sounds/explosion.ogg")
            sounds["brick"] = pygame.mixer.Sound("sounds/brick.ogg")
            sounds["steel"] = pygame.mixer.Sound("sounds/steel.ogg")

        self.enemy_life_image = sprites.subsurface(162, 57 * 2, 7 * 2, 7 * 2)
        self.player_life_image = sprites.subsurface(89 * 2, 56 * 2, 7 * 2, 8 * 2)
        self.flag_image = sprites.subsurface(64 * 2, 49 * 2, 16 * 2, 15 * 2)

        self.player_image = pygame.transform.rotate(sprites.subsurface(0, 0, 26, 26), 270)

        self.timefreeze = False

        # шрифт классный
        self.font = pygame.font.Font("fonts/prstart.ttf", 16)

        # загружаем надпись
        self.im_game_over = pygame.Surface((64, 40))
        self.im_game_over.set_colorkey((0,0,0))
        self.im_game_over.blit(self.font.render("GAME", False, (127, 64, 64)), [0, 0])
        self.im_game_over.blit(self.font.render("OVER", False, (127, 64, 64)), [0, 20])
        self.game_over_y = 416+40

        # число игроков
        self.nr_of_players = 1

        del players[:]
        del bullets[:]
        del enemies[:]
        del bonuses[:]


    def triggerBonus(self, bonus, player):
        global enemies, labels, play_sounds, sounds
        if play_sounds:
            sounds["bonus"].play()
        player.trophies["bonus"] += 1
        player.score += 500
        if bonus.bonus == bonus.BONUS_GRENADE:
            for enemy in enemies:
                enemy.explode()
        elif bonus.bonus == bonus.BONUS_HELMET:
            self.shieldPlayer(player, True, 10000)
        elif bonus.bonus == bonus.BONUS_SHOVEL:
            self.level.buildFortress(self.level.TILE_STEEL)
            gtimer.add(10000, lambda :self.level.buildFortress(self.level.TILE_BRICK), 1)
        elif bonus.bonus == bonus.BONUS_STAR:
            player.superpowers += 1
            if player.superpowers == 2:
                player.max_active_bullets = 2
        elif bonus.bonus == bonus.BONUS_TANK:
            player.lives += 1
        elif bonus.bonus == bonus.BONUS_TIMER:
            self.toggleEnemyFreeze(True)
            gtimer.add(10000, lambda :self.toggleEnemyFreeze(False), 1)
        bonuses.remove(bonus)
        labels.append(Label(bonus.rect.topleft, "500", 500))

    def shieldPlayer(self, player, shield = True, duration = None):
        player.shielded = shield
        if shield:
            player.timer_uuid_shield = gtimer.add(100, lambda :player.toggleShieldImage())
        else:
            gtimer.destroy(player.timer_uuid_shield)

        if shield and duration != None:
            gtimer.add(duration, lambda :self.shieldPlayer(player, False), 1)


    def spawnEnemy(self):
        global enemies
        if len(enemies) >= self.level.max_active_enemies:
            return
        if len(self.level.enemies_left) < 1 or self.timefreeze:
            return
        enemy = Enemy(self.level, 1)

        enemies.append(enemy)


    def respawnPlayer(self, player, clear_scores = False):
        player.reset()
        if clear_scores:
            player.trophies = {
                "bonus" : 0, "enemy0" : 0, "enemy1" : 0, "enemy2" : 0, "enemy3" : 0
            }

        self.shieldPlayer(player, True, 4000)

    def gameOver(self):
        global play_sounds, sounds
        if play_sounds:
            for sound in sounds:
                sounds[sound].stop()
            sounds["end"].play()

        self.game_over_y = 416+40

        self.game_over = True
        gtimer.add(3000, lambda :self.showScores(), 1)

    def gameOverScreen(self):
        global screen
        self.running = False
        screen.fill([0, 0, 0])
        self.writeInBricks("game", [125, 140])
        self.writeInBricks("over", [125, 220])
        pygame.display.flip()

        while True:
            self.clock.tick(50)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.showMenu()
                        return

    def showMenu(self):
        global players, screen
        self.running = False
        del gtimer.timers[:]
        self.stage = 1
        self.IntroScreen()
        main_loop = True
        while main_loop:
            self.clock.tick(50)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        quit()
                    elif event.key == pygame.K_UP:
                        if self.nr_of_players == 2:
                            self.nr_of_players = 1
                            self.drawIntroScreen()
                    elif event.key == pygame.K_DOWN:
                        if self.nr_of_players == 1:
                            self.nr_of_players = 2
                            self.drawIntroScreen()
                    elif event.key == pygame.K_RETURN:
                        main_loop = False

        del players[:]
        self.nextLevel()
    def reloadPlayers(self):
        global players
        if len(players) == 0:
            # первый чел
            x = 8 * self.TILE_SIZE + (self.TILE_SIZE * 2 - 26) / 2
            y = 24 * self.TILE_SIZE + (self.TILE_SIZE * 2 - 26) / 2

            player = Player(
                self.level, 0, [x, y], self.DIR_UP, (0, 0, 13*2, 13*2)
            )
            players.append(player)

            # второй чел
            if self.nr_of_players == 2:
                x = 16 * self.TILE_SIZE + (self.TILE_SIZE * 2 - 26) / 2
                y = 24 * self.TILE_SIZE + (self.TILE_SIZE * 2 - 26) / 2
                player = Player(
                    self.level, 0, [x, y], self.DIR_UP, (16*2, 0, 13*2, 13*2)
                )
                player.controls = [102, 119, 100, 115, 97]
                players.append(player)

        for player in players:
            player.level = self.level
            self.respawnPlayer(player, True)

    def showScores(self):
        global screen, sprites, players, play_sounds, sounds
        self.running = False
        del gtimer.timers[:]
        if play_sounds:
            for sound in sounds:
                sounds[sound].stop()
        hiscore = self.loadHiscore()

        # лучший результат
        if players[0].score > hiscore:
            hiscore = players[0].score
            self.saveHiscore(hiscore)
        if self.nr_of_players == 2 and players[1].score > hiscore:
            hiscore = players[1].score
            self.saveHiscore(hiscore)

        img_tanks = [
            sprites.subsurface(32*2, 0, 13*2, 15*2),
            sprites.subsurface(48*2, 0, 13*2, 15*2),
            sprites.subsurface(64*2, 0, 13*2, 15*2),
            sprites.subsurface(80*2, 0, 13*2, 15*2)
        ]

        img_arrows = [
            sprites.subsurface(81*2, 48*2, 7*2, 7*2),
            sprites.subsurface(88*2, 48*2, 7*2, 7*2)
        ]

        screen.fill([0, 0, 0])
        # константы
        black = pygame.Color("black")
        white = pygame.Color("white")
        purple = pygame.Color(127, 64, 64)
        pink = pygame.Color(191, 160, 128)

        screen.blit(self.font.render("HI-SCORE", False, purple), [105, 35])
        screen.blit(self.font.render(str(hiscore), False, pink), [295, 35])
        screen.blit(self.font.render("STAGE"+str(self.stage - 1).rjust(3), False, white), [170, 65])
        screen.blit(self.font.render("I-PLAYER", False, purple), [25, 95])
        screen.blit(self.font.render(str(players[0].score).rjust(8), False, pink), [25, 125])

        if self.nr_of_players == 2:
            screen.blit(self.font.render("II-PLAYER", False, purple), [310, 95])
            screen.blit(self.font.render(str(players[1].score).rjust(8), False, pink), [325, 125])
        for i in range(4):
            screen.blit(img_tanks[i], [226, 160 + (i * 45)])
            screen.blit(img_arrows[0], [206, 168 + (i * 45)])
            if self.nr_of_players == 2:
                screen.blit(img_arrows[1], [258, 168 + (i * 45)])

        screen.blit(self.font.render("TOTAL", False, white), [70, 335])

        pygame.draw.line(screen, white, [170, 330], [307, 330], 4)
        pygame.display.flip()
        self.clock.tick(2)
        interval = 5
        for i in range(4):
            tanks = players[0].trophies["enemy" + str(i)]
            for n in range(tanks + 1):
                if n > 0 and play_sounds:
                    sounds["score"].play()

                screen.blit(self.font.render(str(n-1).rjust(2), False, black), [170, 168+(i*45)])
                screen.blit(self.font.render(str(n).rjust(2), False, white), [170, 168+(i*45)])
                screen.blit(self.font.render(str((n-1) * (i+1) * 100).rjust(4)+" PTS", False, black), [25, 168+(i*45)])
                screen.blit(self.font.render(str(n * (i+1) * 100).rjust(4)+" PTS", False, white), [25, 168+(i*45)])
                pygame.display.flip()
                self.clock.tick(interval)

            if self.nr_of_players == 2:
                tanks = players[1].trophies["enemy" + str(i)]
                for n in range(tanks + 1):
                    if n > 0 and play_sounds:
                        sounds["score"].play()
                    screen.blit(self.font.render(str(n-1).rjust(2), False, black), [277, 168+(i*45)])
                    screen.blit(self.font.render(str(n).rjust(2), False, white), [277, 168+(i*45)])
                    screen.blit(self.font.render(str((n-1) * (i+1) * 100).rjust(4)+" PTS", False, black), [325, 168+(i*45)])
                    screen.blit(self.font.render(str(n * (i+1) * 100).rjust(4)+" PTS", False, white), [325, 168+(i*45)])
                    pygame.display.flip()
                    self.clock.tick(interval)
            self.clock.tick(interval)
        tanks = sum([i for i in players[0].trophies.values()]) - players[0].trophies["bonus"]
        screen.blit(self.font.render(str(tanks).rjust(2), False, white), [170, 335])
        if self.nr_of_players == 2:
            tanks = sum([i for i in players[1].trophies.values()]) - players[1].trophies["bonus"]
            screen.blit(self.font.render(str(tanks).rjust(2), False, white), [277, 335])
        pygame.display.flip()
        self.clock.tick(1)
        if self.game_over:
            self.gameOverScreen()
        else:
            self.nextLevel()


    def draw(self):
        global screen, castle, players, enemies, bullets, bonuses
        screen.fill([0, 0, 0])
        self.level.draw([self.level.TILE_EMPTY, self.level.TILE_BRICK, self.level.TILE_STEEL, self.level.TILE_FROZE, self.level.TILE_WATER])
        castle.draw()
        for enemy in enemies:
            enemy.draw()
        for label in labels:
            label.draw()
        for player in players:
            player.draw()
        for bullet in bullets:
            bullet.draw()
        for bonus in bonuses:
            bonus.draw()
        self.level.draw([self.level.TILE_GRASS])
        if self.game_over:
            if self.game_over_y > 188:
                self.game_over_y -= 4
            screen.blit(self.im_game_over, [176, self.game_over_y]) # 176=(416-64)/2
        self.drawSidebar()
        pygame.display.flip()
    
    def drawSidebar(self):
        global screen, players, enemies
        x = 416
        y = 0
        screen.fill([100, 100, 100], pygame.Rect([416, 0], [64, 416]))
        xpos = x + 16
        ypos = y + 16
        # жизни врагов
        for n in range(len(self.level.enemies_left) + len(enemies)):
            screen.blit(self.enemy_life_image, [xpos, ypos])
            if n % 2 == 1:
                xpos = x + 16
                ypos+= 17
            else:
                xpos += 17
        if pygame.font.get_init():
            text_color = pygame.Color('black')
            for n in range(len(players)):
                if n == 0:
                    screen.blit(self.font.render(str(n+1)+"P", False, text_color), [x+16, y+200])
                    screen.blit(self.font.render(str(players[n].lives), False, text_color), [x+31, y+215])
                    screen.blit(self.player_life_image, [x+17, y+215])
                else:
                    screen.blit(self.font.render(str(n+1)+"P", False, text_color), [x+16, y+240])
                    screen.blit(self.font.render(str(players[n].lives), False, text_color), [x+31, y+255])
                    screen.blit(self.player_life_image, [x+17, y+255])

            screen.blit(self.flag_image, [x+17, y+280])
            screen.blit(self.font.render(str(self.stage), False, text_color), [x+17, y+312])


    def drawIntroScreen(self, put_on_surface = True):
        global screen
        screen.fill([0, 0, 0])
        if pygame.font.get_init():
            hiscore = self.loadHiscore()
            screen.blit(self.font.render("HI- "+str(hiscore), True, pygame.Color('white')), [170, 35])
            screen.blit(self.font.render("1 PLAYER", True, pygame.Color('white')), [165, 250])
            screen.blit(self.font.render("2 PLAYERS", True, pygame.Color('white')), [165, 275])

        if self.nr_of_players == 1:
            screen.blit(self.player_image, [125, 245])
        elif self.nr_of_players == 2:
            screen.blit(self.player_image, [125, 270])

        self.writeInBricks("battle", [65, 80])
        self.writeInBricks("city", [129, 160])

        if put_on_surface:
            pygame.display.flip()

    def IntroScreen(self):
        global screen
        self.drawIntroScreen(False)
        screen_cp = screen.copy()
        screen.fill([0, 0, 0])
        y = 0
        self.clock.tick(50)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    y = 0
                    break
        screen.blit(screen_cp, [0, y])
        pygame.display.flip()
        y -= 5
        screen.blit(screen_cp, [0, 0])
        pygame.display.flip()

    def chunks(self, l, n):
        return [l[i:i + n] for i in range(0, len(l), n)]

    def writeInBricks(self, text, pos):
        global screen, sprites
        bricks = sprites.subsurface(56*2, 64*2, 8*2, 8*2)
        brick1 = bricks.subsurface((0, 0, 8, 8))
        brick2 = bricks.subsurface((8, 0, 8, 8))
        brick3 = bricks.subsurface((8, 8, 8, 8))
        brick4 = bricks.subsurface((0, 8, 8, 8))

        alphabet = {  # чтоб нормально отображался шрифт
            "a" : "0071b63c7ff1e3",
            "b" : "01fb1e3fd8f1fe",
            "c" : "00799e0c18199e",
            "e" : "01fb060f98307e",
            "g" : "007d860cf8d99f",
            "i" : "01f8c183060c7e",
            "l" : "0183060c18307e",
            "m" : "018fbffffaf1e3",
            "o" : "00fb1e3c78f1be",
            "r" : "01fb1e3cff3767",
            "t" : "01f8c183060c18",
            "v" : "018f1e3eef8e08",
            "y" : "019b3667860c18"
        }

        abs_x, abs_y = pos
        for letter in text.lower():
            binstr = ""
            for h in self.chunks(alphabet[letter], 2):
                binstr += str(bin(int(h, 16)))[2:].rjust(8, "0")
            binstr = binstr[7:]
            x, y = 0, 0
            letter_w = 0
            surf_letter = pygame.Surface((56, 56))
            for j, row in enumerate(self.chunks(binstr, 7)):
                for i, bit in enumerate(row):
                    if bit == "1":
                        if i % 2 == 0 and j % 2 == 0:
                            surf_letter.blit(brick1, [x, y])
                        elif i % 2 == 1 and j % 2 == 0:
                            surf_letter.blit(brick2, [x, y])
                        elif i % 2 == 1 and j % 2 == 1:
                            surf_letter.blit(brick3, [x, y])
                        elif i % 2 == 0 and j % 2 == 1:
                            surf_letter.blit(brick4, [x, y])
                        if x > letter_w:
                            letter_w = x
                    x += 8
                x = 0
                y += 8
            screen.blit(surf_letter, [abs_x, abs_y])
            abs_x += letter_w + 16

    def toggleEnemyFreeze(self, freeze = True):
        global enemies
        for enemy in enemies:
            enemy.paused = freeze
        self.timefreeze = freeze


    def loadHiscore(self):
        filename = "hiscore.txt"
        if (not os.path.isfile(filename)):
            return 20000

        f = open(filename, "r")
        hiscore = int(f.read())
        if hiscore > 0 and hiscore < 1000000:
            return hiscore
        else:
            return 20000

    def saveHiscore(self, hiscore):
        try:
            f = open("hiscore.txt", "w")
        except:
            return False
        f.write(str(hiscore))
        f.close()
        return True


    def finishLevel(self):
        global play_sounds, sounds

        self.active = False
        gtimer.add(3000, lambda :self.showScores(), 1)

        print("Stage " + str(self.stage - 1) +" completed")

    def nextLevel(self):
        global castle, players, bullets, bonuses, play_sounds, sounds

        del bullets[:]
        del enemies[:]
        del bonuses[:]
        castle.rebuild()
        del gtimer.timers[:]

        self.stage += 1
        self.level = Level(self.stage)
        self.timefreeze = False

        levels_enemies = (
            (18,2,0,0), (14,4,0,2), (14,4,0,2), (2,5,10,3), (8,5,5,2), (9,2,7,2))

        if self.stage <= 35:
            enemies_l = levels_enemies[self.stage - 1]
        else:
            enemies_l = levels_enemies[34]

        self.level.enemies_left = [0]*enemies_l[0] + [1]*enemies_l[1] + [2]*enemies_l[2] + [3]*enemies_l[3]
        random.shuffle(self.level.enemies_left)
        if play_sounds:
            sounds["start"].play()
        self.reloadPlayers()
        gtimer.add(3000, lambda :self.spawnEnemy())
        self.game_over = False
        self.running = True
        self.active = True
        self.draw()

        while self.running:
            time_passed = self.clock.tick(50)
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pass
                elif event.type == pygame.QUIT:
                    quit()
                elif event.type == pygame.KEYDOWN and not self.game_over and self.active:
                    if event.key == pygame.K_p:
                        quit()
                    elif event.key == pygame.K_m:
                        play_sounds = not play_sounds
                        if not play_sounds:
                            pygame.mixer.stop()

                    for player in players:
                        if player.state == player.STATE_ALIVE:
                            try:
                                index = player.controls.index(event.key)
                            except:
                                pass
                            else:
                                if index == 0:
                                    if player.fire() and play_sounds:
                                        sounds["fire"].play()
                                elif index == 1:
                                    player.pressed[0] = True
                                elif index == 2:
                                    player.pressed[1] = True
                                elif index == 3:
                                    player.pressed[2] = True
                                elif index == 4:
                                    player.pressed[3] = True
                elif event.type == pygame.KEYUP and not self.game_over and self.active:
                    for player in players:
                        if player.state == player.STATE_ALIVE:
                            try:
                                index = player.controls.index(event.key)
                            except:
                                pass
                            else:
                                if index == 1:
                                    player.pressed[0] = False
                                elif index == 2:
                                    player.pressed[1] = False
                                elif index == 3:
                                    player.pressed[2] = False
                                elif index == 4:
                                    player.pressed[3] = False

            for player in players:
                if player.state == player.STATE_ALIVE and not self.game_over and self.active:
                    if player.pressed[0] == True:
                        player.move(self.DIR_UP)
                    elif player.pressed[1] == True:
                        player.move(self.DIR_RIGHT)
                    elif player.pressed[2] == True:
                        player.move(self.DIR_DOWN)
                    elif player.pressed[3] == True:
                        player.move(self.DIR_LEFT)
                player.update(time_passed)

            for enemy in enemies:
                if enemy.state == enemy.STATE_DEAD and not self.game_over and self.active:
                    enemies.remove(enemy)
                    if len(self.level.enemies_left) == 0 and len(enemies) == 0:
                        self.finishLevel()
                else:
                    enemy.update(time_passed)

            if not self.game_over and self.active:
                for player in players:
                    if player.state == player.STATE_ALIVE:
                        if player.bonus != None and player.side == player.SIDE_PLAYER:
                            self.triggerBonus(bonus, player)
                            player.bonus = None
                    elif player.state == player.STATE_DEAD:
                        self.superpowers = 0
                        player.lives -= 1
                        if player.lives > 0:
                            self.respawnPlayer(player)
                        else:
                            self.gameOver()

            for bullet in bullets:
                if bullet.state == bullet.STATE_REMOVED:
                    bullets.remove(bullet)
                else:
                    bullet.update()

            for bonus in bonuses:
                if bonus.active == False:
                    bonuses.remove(bonus)

            for label in labels:
                if not label.active:
                    labels.remove(label)

            if not self.game_over:
                if not castle.active:
                    self.gameOver()

            gtimer.update(time_passed)
            self.draw()

if __name__ == "__main__":

    gtimer = Timer()

    sprites = None
    screen = None
    players = []
    enemies = []
    bullets = []
    bonuses = []
    labels = []

    play_sounds = True
    sounds = {}
    game = Game()
    castle = Castle()
    game.showMenu()