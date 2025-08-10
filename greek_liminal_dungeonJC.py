import pygame
import math
import random
import os
import wave
import struct
from pyjoycon import JoyCon, get_R_id, get_L_id

# 古代ギリシャ・リミナル迷宮探索ゲーム 拡張版
# 追加要素:
# - コレクタブル(オリンポスの印章)の配置と取得
# - 祭壇でのインタラクト(全印章を捧げるとクリア)
# - スプライト(簡易ビルボード)描画と壁オクルージョン
# - 浮遊粒子エフェクト/やわらかい色変化
# - ミニマップ拡張(コレクタブル/祭壇表示)
# - UI強化(目的/取得数/エリア表示/近接ヒント)

pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ancient Greek Liminal Dungeon - 古代ギリシャの境界迷宮")
clock = pygame.time.Clock()

# ゲーム定数
WALL_HEIGHT = 300


class Player:
    def __init__(self):
        self.x = 1.5
        self.y = 1.5
        self.angle = 0
        self.fov = math.pi / 3  # 60度

    def move_forward(self, world_map, dt, speed, can_walk):
        new_x = self.x + math.cos(self.angle) * speed * dt
        new_y = self.y + math.sin(self.angle) * speed * dt
        if new_y >= len(world_map):
            return
        if can_walk(new_x, new_y):
            self.x, self.y = new_x, new_y

    def move_backward(self, world_map, dt, speed, can_walk):
        new_x = self.x - math.cos(self.angle) * speed * dt
        new_y = self.y - math.sin(self.angle) * speed * dt
        if new_y >= len(world_map):
            return
        if can_walk(new_x, new_y):
            self.x, self.y = new_x, new_y

    def turn_left(self, dt, turn_speed):
        self.angle -= turn_speed * dt

    def turn_right(self, dt, turn_speed):
        self.angle += turn_speed * dt

    def strafe_left(self, world_map, dt, speed, can_walk):
        new_x = self.x + math.cos(self.angle - math.pi / 2) * speed * dt
        new_y = self.y + math.sin(self.angle - math.pi / 2) * speed * dt
        if new_y >= len(world_map):
            return
        if can_walk(new_x, new_y):
            self.x, self.y = new_x, new_y

    def strafe_right(self, world_map, dt, speed, can_walk):
        new_x = self.x + math.cos(self.angle + math.pi / 2) * speed * dt
        new_y = self.y + math.sin(self.angle + math.pi / 2) * speed * dt
        if new_y >= len(world_map):
            return
        if can_walk(new_x, new_y):
            self.x, self.y = new_x, new_y


# 拡大マップ (0=通路, 1=壁, 2=柱, 3=彫像, 4=建物, 5=海, 6=砂浜)
world_map = [
    # 迷宮エリア (0-9, 0-24)
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 2, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 0, 0, 0, 1, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    # 街エリア (10-14, 0-24)
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 4, 0, 0, 4, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 4, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 4, 0, 0, 4, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 4, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0],
    # 海岸エリア (15-24, 0-24)
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6],
    [6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
]


def cast_ray(player, angle_offset):
    ray_angle = player.angle + angle_offset
    ray_x = player.x
    ray_y = player.y
    step_x = math.cos(ray_angle) * 0.02
    step_y = math.sin(ray_angle) * 0.02
    distance = 0
    hit_type = 0

    while distance < 20:
        ray_x += step_x
        ray_y += step_y
        distance += 0.02
        map_x = int(ray_x)
        map_y = int(ray_y)

        if map_x < 0 or map_x >= len(world_map[0]) or map_y < 0:
            hit_type = 1
            break
        elif map_y >= len(world_map):
            break

        cell = world_map[map_y][map_x]
        if cell not in [0, 5, 6]:  # 通路、海、砂浜以外はヒット
            hit_type = cell
            break

    # 魚眼効果を補正
    distance *= max(0.0001, math.cos(angle_offset))
    return distance, hit_type


def get_current_area(player_x, player_y):
    if player_y < 10:
        return "dungeon"
    elif player_y < 15:
        return "town"
    elif player_y < 18:
        return "beach"
    else:
        return "ocean"


def draw_background_by_area(area, frame_count):
    for y in range(HEIGHT):
        if area == "dungeon":
            if y < HEIGHT // 2:
                depth_ratio = y / (HEIGHT // 2)
                red = int(255 - depth_ratio * 50)
                green = int(200 - depth_ratio * 80)
                blue = int(230 + depth_ratio * 25)
            else:
                depth_ratio = (y - HEIGHT // 2) / (HEIGHT // 2)
                red = int(205 - depth_ratio * 45)
                green = int(120 + depth_ratio * 40)
                blue = int(255 - depth_ratio * 75)
        elif area == "town":
            if y < HEIGHT // 2:
                depth_ratio = y / (HEIGHT // 2)
                red = int(255 - depth_ratio * 50)
                green = int(200 - depth_ratio * 80)
                blue = int(230 + depth_ratio * 25)
            else:
                depth_ratio = (y - HEIGHT // 2) / (HEIGHT // 2)
                red = int(175 + depth_ratio * 60)
                green = int(120 + depth_ratio * 80)
                blue = int(100 + depth_ratio * 50)
        elif area == "beach":
            if y < HEIGHT // 2:
                depth_ratio = y / (HEIGHT // 2)
                red = int(255 - depth_ratio * 50)
                green = int(200 - depth_ratio * 80)
                blue = int(230 + depth_ratio * 25)
            else:
                depth_ratio = (y - HEIGHT // 2) / (HEIGHT // 2)
                red = int(195 + depth_ratio * 40)
                green = int(160 + depth_ratio * 50)
                blue = int(120 + depth_ratio * 30)
        elif area == "ocean":
            if y < HEIGHT // 2:
                depth_ratio = y / (HEIGHT // 2)
                red = int(255 - depth_ratio * 50)
                green = int(200 - depth_ratio * 80)
                blue = int(230 + depth_ratio * 25)
            else:
                wave_effect = math.sin(frame_count * 0.1 + y * 0.05) * 15
                depth_ratio = (y - HEIGHT // 2) / (HEIGHT // 2)
                red = int(100 + depth_ratio * 50 + wave_effect * 0.3)
                green = int(180 + depth_ratio * 40 + wave_effect * 0.5)
                blue = int(255 - depth_ratio * 30 + wave_effect * 0.2)

        color = (
            max(0, min(255, red)),
            max(0, min(255, green)),
            max(0, min(255, blue)),
        )
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))


def draw_wall_slice(x, wall_height, wall_type, distance):
    # 壁の色を距離に応じて調整
    distance_factor = max(0.3, min(1.0, 8.0 / max(0.0001, distance)))

    if wall_type == 1:  # 通常の壁
        base_color = (220, 210, 200)
    elif wall_type == 2:  # 柱
        base_color = (240, 235, 220)
    elif wall_type == 3:  # 彫像
        base_color = (200, 190, 180)
    elif wall_type == 4:  # 建物
        base_color = (180, 150, 120)
    else:
        base_color = (180, 170, 160)

    wall_color = tuple(int(c * distance_factor) for c in base_color)

    wall_top = (HEIGHT - wall_height) // 2
    wall_bottom = wall_top + wall_height

    pygame.draw.line(screen, wall_color, (x, wall_top), (x, wall_bottom), 2)

    # リミナルな光の効果
    if wall_type == 2:  # 柱に光の効果
        glow_color = (255, 250, 240)
        for i in range(3):
            glow_y = wall_top + (wall_bottom - wall_top) // 4 * (i + 1)
            pygame.draw.circle(screen, glow_color, (x, glow_y), 2)
    elif wall_type == 3:  # 彫像に神秘的な光
        statue_color = (200, 180, 255)
        statue_center_y = (wall_top + wall_bottom) // 2
        pygame.draw.circle(screen, statue_color, (x, statue_center_y), 3)
    elif wall_type == 4:  # 建物に暖かい光
        building_color = (255, 200, 100)
        for i in range(2):
            window_y = wall_top + (wall_bottom - wall_top) // 3 * (i + 1)
            pygame.draw.rect(screen, building_color, (x - 1, window_y - 2, 2, 4))


class Collectible:
    def __init__(self, x, y, kind="sigil"):
        self.x = x
        self.y = y
        self.kind = kind
        self.collected = False
        self.seed = random.random() * 1000


class Altar:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.activated = False


def project_sprite(player, obj_x, obj_y):
    dx = obj_x - player.x
    dy = obj_y - player.y
    dist = math.hypot(dx, dy)
    angle_to = math.atan2(dy, dx) - player.angle
    # 角度を -pi..pi に正規化
    while angle_to > math.pi:
        angle_to -= 2 * math.pi
    while angle_to < -math.pi:
        angle_to += 2 * math.pi

    # 視野外は描画しない
    if abs(angle_to) > player.fov:
        return None

    # 画面X位置(中心で0, 左-1, 右+1)
    cam_x = math.tan(angle_to) / math.tan(player.fov / 2)
    screen_x = int((cam_x + 1) * 0.5 * WIDTH)

    # 歪み補正した距離
    corrected = max(0.0001, dist * math.cos(angle_to))
    size = min(HEIGHT, int(WALL_HEIGHT / corrected))
    return screen_x, size, corrected


def draw_collectibles_and_altar(player, zbuffer, collectibles, altar, frame_count, font_small):
    hint_text = None
    hint_pos = None
    for item in collectibles:
        if item.collected:
            continue
        proj = project_sprite(player, item.x, item.y)
        if proj is None:
            continue
        sx, size, dist = proj
        # 奥行きの簡易チェック(スプライト幅ぶん)
        half = max(2, size // 4)
        vis = False
        for xx in range(max(0, sx - half), min(WIDTH, sx + half + 1)):
            if dist < zbuffer[xx]:
                vis = True
                break
        if vis:
            # 柔らかい揺れ
            bob = math.sin(frame_count * 0.08 + item.seed) * (size * 0.05)
            top = int(HEIGHT // 2 - size // 2 - bob)
            color = (255, 220, 120)  # 金色
            pygame.draw.circle(screen, color, (sx, max(0, top + size // 2)), max(4, size // 6))

        # 取得ロジック(近接)
        if math.hypot(player.x - item.x, player.y - item.y) < 0.7:
            hint_text = "Press F: 印章を拾う"
            hint_pos = (sx, HEIGHT // 2 - size // 2 - 20)

    # 祭壇
    proj = project_sprite(player, altar.x, altar.y)
    if proj is not None:
        sx, size, dist = proj
        half = max(2, size // 4)
        vis = False
        for xx in range(max(0, sx - half), min(WIDTH, sx + half + 1)):
            if dist < zbuffer[xx]:
                vis = True
                break
        if vis:
            bob = math.sin(frame_count * 0.06) * (size * 0.04)
            top = int(HEIGHT // 2 - size // 2 - bob)
            base_color = (180, 200, 255) if not altar.activated else (180, 255, 200)
            pygame.draw.rect(
                screen, base_color, (sx - size // 6, max(0, top + size // 3), max(6, size // 3), max(6, size // 4))
            )
        # 近接ヒント
        if math.hypot(player.x - altar.x, player.y - altar.y) < 1.0:
            hint_text = "Press F: 祭壇に捧げる"
            hint_pos = (sx, HEIGHT // 2 - size // 2 - 20)

    # ヒント表示
    if hint_text and hint_pos:
        text_surf = font_small.render(hint_text, True, (255, 255, 255))
        rect = text_surf.get_rect(center=(max(30, min(WIDTH - 30, hint_pos[0])), max(20, hint_pos[1])))
        screen.blit(text_surf, rect)


# かわいい動物/蝶スプライト
def draw_cute_sprite(kind, sx, ypix, size):
    wing = max(4, size // 6)
    body_h = max(3, size // 8)
    if kind in ("butterfly",):
        c1, c2, c3 = (255, 170, 200), (220, 120, 230), (80, 50, 90)
        pygame.draw.ellipse(screen, c1, (sx - wing - 2, ypix - wing, wing, int(wing * 1.4)))
        pygame.draw.ellipse(screen, c2, (sx + 2, ypix - wing, wing, int(wing * 1.4)))
        pygame.draw.rect(screen, c3, (sx - 1, ypix - body_h, 2, body_h * 2))
        pygame.draw.line(screen, c3, (sx, ypix - body_h), (sx - wing // 2, ypix - body_h - wing // 2), 1)
        pygame.draw.line(screen, c3, (sx, ypix - body_h), (sx + wing // 2, ypix - body_h - wing // 2), 1)
    elif kind in ("moth",):
        c1, c2, c3 = (230, 220, 190), (200, 190, 160), (90, 70, 50)
        pygame.draw.ellipse(screen, c1, (sx - wing - 2, ypix - wing, wing, int(wing * 1.3)))
        pygame.draw.ellipse(screen, c2, (sx + 2, ypix - wing, wing, int(wing * 1.3)))
        pygame.draw.rect(screen, c3, (sx - 1, ypix - body_h, 2, body_h * 2))
    elif kind == "mouse":
        c1, c2, c3 = (200, 200, 210), (170, 170, 180), (60, 60, 70)
        bw = max(6, size // 4); bh = max(4, size // 6)
        pygame.draw.ellipse(screen, c1, (sx - bw // 2, ypix - bh // 2, bw, bh))
        pygame.draw.circle(screen, c2, (sx - bw // 3, ypix - bh // 2), max(2, bh // 3))
        pygame.draw.circle(screen, c2, (sx + bw // 3, ypix - bh // 2), max(2, bh // 3))
        pygame.draw.line(screen, c3, (sx + bw // 2, ypix), (sx + bw, ypix + bh // 3), 1)
    elif kind == "crab":
        c1, c2 = (220, 100, 100), (60, 30, 30)
        bw = max(8, size // 3); bh = max(4, size // 6)
        pygame.draw.ellipse(screen, c1, (sx - bw // 2, ypix - bh // 2, bw, bh))
        pygame.draw.circle(screen, c1, (sx - bw // 2, ypix - bh // 3), max(2, bh // 3))
        pygame.draw.circle(screen, c1, (sx + bw // 2, ypix - bh // 3), max(2, bh // 3))
    elif kind == "fish":
        c1, c2 = (100, 180, 255), (60, 120, 200)
        bw = max(8, size // 3); bh = max(4, size // 7)
        pygame.draw.ellipse(screen, c1, (sx - bw // 2, ypix - bh // 2, bw, bh))
        pygame.draw.polygon(screen, c2, [(sx + bw // 2, ypix), (sx + bw // 2 + bh, ypix - bh // 2), (sx + bw // 2 + bh, ypix + bh // 2)])


def draw_animals(player, zbuffer, animals, world_map, dt, frame_count, current_area):
    def is_walkable(nx, ny, allowed):
        R = 0.14
        for ox, oy in ((0,0),(R,0),(-R,0),(0,R),(0,-R)):
            tx, ty = int(nx + ox), int(ny + oy)
            if not (0 <= tx < len(world_map[0]) and 0 <= ty < len(world_map)):
                return False
            if world_map[ty][tx] not in allowed:
                return False
        return True

    for a in animals:
        if a.get('area') and a['area'] != current_area:
            continue
        if frame_count >= a.get('next_turn', 0):
            ang = random.random() * math.tau
            spd = a.get('speed', 1.2)
            a['vx'], a['vy'] = math.cos(ang) * spd, math.sin(ang) * spd
            a['next_turn'] = frame_count + random.randint(20, 100)
        nx = a['x'] + a.get('vx',0) * dt
        ny = a['y'] + a.get('vy',0) * dt
        allowed = a.get('allowed', [0,5,6])
        if is_walkable(nx, a['y'], allowed):
            a['x'] = nx
        else:
            a['vx'] = -a.get('vx',0)
        if is_walkable(a['x'], ny, allowed):
            a['y'] = ny
        else:
            a['vy'] = -a.get('vy',0)

        proj = project_sprite(player, a['x'], a['y'])
        if not proj:
            continue
        sx, size, dist = proj
        half = max(2, size // 4)
        vis = False
        for xx in range(max(0, sx - half), min(WIDTH, sx + half + 1)):
            if dist < zbuffer[xx]:
                vis = True
                break
        if not vis:
            continue
        kind = a.get('type', 'butterfly')
        if kind in ('butterfly','moth','fish'):
            bob = math.sin(frame_count * 0.05 + a.get('seed',0)) * (size * 0.06)
        else:
            bob = 0
        ypix = int(HEIGHT // 2 - size // 2 - bob + size * (0.5 if kind in ('butterfly','moth') else 0.3))
        draw_cute_sprite(kind, sx, ypix, size)


def draw_floating_particles(frame_count, particles):
    # 浮遊する神秘的な粒子: 画面オーバーレイ
    for i, p in enumerate(particles):
        t = frame_count * 0.01 + p[2]
        x = int((p[0] + math.sin(t) * 20) % WIDTH)
        y = int((p[1] + math.cos(t * 0.8) * 15) % HEIGHT)
        a = int(80 + 60 * (0.5 + 0.5 * math.sin(t * 1.7)))
        col = (200, 200, 255)
        # 軽いグロー表現
        pygame.draw.circle(screen, col, (x, y), 1)
        if i % 5 == 0:
            pygame.draw.circle(screen, (180, 180, 240), (x, y), 2)


def draw_minimap(player, collectibles, altar):
    map_scale = 6
    map_offset_x = WIDTH - 160
    map_offset_y = 10
    map_size = 150

    pygame.draw.rect(screen, (30, 30, 30), (map_offset_x, map_offset_y, map_size, map_size))

    center_x = int(player.x)
    center_y = int(player.y)
    view_range = 12

    for dy in range(-view_range, view_range + 1):
        for dx in range(-view_range, view_range + 1):
            world_x = center_x + dx
            world_y = center_y + dy
            if 0 <= world_x < len(world_map[0]) and 0 <= world_y < len(world_map):
                cell = world_map[world_y][world_x]
                if cell == 0:
                    color = (80, 80, 80)
                elif cell == 1:
                    color = (160, 160, 160)
                elif cell == 2:
                    color = (255, 255, 100)
                elif cell == 3:
                    color = (255, 100, 255)
                elif cell == 4:
                    color = (200, 150, 100)
                elif cell == 5:
                    color = (100, 150, 255)
                elif cell == 6:
                    color = (255, 220, 150)
                else:
                    color = (100, 100, 100)

                mini_x = map_offset_x + (dx + view_range) * map_scale
                mini_y = map_offset_y + (dy + view_range) * map_scale
                pygame.draw.rect(screen, color, (mini_x, mini_y, map_scale - 1, map_scale - 1))

    # コレクタブル/祭壇表示
    for it in collectibles:
        if it.collected:
            continue
        mx = map_offset_x + (int(it.x) - center_x + view_range) * map_scale
        my = map_offset_y + (int(it.y) - center_y + view_range) * map_scale
        if map_offset_x <= mx < map_offset_x + map_size and map_offset_y <= my < map_offset_y + map_size:
            pygame.draw.circle(screen, (255, 230, 120), (mx, my), 2)

    mx = map_offset_x + (int(altar.x) - center_x + view_range) * map_scale
    my = map_offset_y + (int(altar.y) - center_y + view_range) * map_scale
    if map_offset_x <= mx < map_offset_x + map_size and map_offset_y <= my < map_offset_y + map_size:
        pygame.draw.circle(screen, (180, 220, 255), (mx, my), 2)

    # プレイヤー位置(中央)
    player_mini_x = map_offset_x + view_range * map_scale
    player_mini_y = map_offset_y + view_range * map_scale
    pygame.draw.circle(screen, (255, 0, 0), (player_mini_x, player_mini_y), 3)
    view_end_x = int(player_mini_x + math.cos(player.angle) * 15)
    view_end_y = int(player_mini_y + math.sin(player.angle) * 15)
    pygame.draw.line(screen, (255, 0, 0), (player_mini_x, player_mini_y), (view_end_x, view_end_y), 2)

    # エリア表示
    font = pygame.font.Font(None, 20)
    current_area = get_current_area(player.x, player.y)
    area_text = font.render(f"Area: {current_area.title()}", True, (255, 255, 255))
    screen.blit(area_text, (map_offset_x, map_offset_y + map_size + 5))


def draw_ui(collected_count, total_count, objective_text, message_text=None):
    font = pygame.font.Font(None, 24)
    lines = [
        "WASD/JoyCon: Move  Q/E/XB: Turn  Shift+A/D/ZL+Stick: Strafe  F/A: Interact  M/+: Mute",
        f"Sigils: {collected_count}/{total_count}",
        f"Objective: {objective_text}",
    ]
    for i, line in enumerate(lines):
        text = font.render(line, True, (255, 255, 255))
        screen.blit(text, (10, 10 + i * 24))

    if message_text:
        msg = font.render(message_text, True, (255, 255, 180))
        rect = msg.get_rect(center=(WIDTH // 2, 30))
        screen.blit(msg, rect)


def ensure_bgm(path: str, length_sec: float = 28.0, sr: int = 22050):
    if os.path.exists(path):
        return

    random.seed(42)
    nchannels = 1
    sampwidth = 2  # 16-bit
    framerate = sr
    nframes = int(length_sec * sr)

    # 音階(ドリアンスケール風)
    scale = [146.83, 164.81, 174.61, 196.00, 220.00, 246.94, 261.63, 293.66]
    base_drone = [(146.83, 0.18), (220.00, 0.12), (293.66, 0.07)]

    # チャイムの発音タイムスタンプ
    chime_interval = 1.5
    chime_len = 0.9
    chime_events = [i * chime_interval for i in range(int(length_sec // chime_interval))]
    chime_notes = [random.choice(scale) for _ in chime_events]

    with wave.open(path, "wb") as wf:
        wf.setparams((nchannels, sampwidth, framerate, nframes, "NONE", "not compressed"))

        prev_noise = 0.0
        for i in range(nframes):
            t = i / sr

            # ドローン
            drone = 0.0
            for f, a in base_drone:
                lfo = 0.97 + 0.03 * math.sin(2 * math.pi * 0.1 * t + f * 0.01)
                drone += a * lfo * math.sin(2 * math.pi * f * t)

            # チャイム(減衰)
            ch = 0.0
            for start_t, note_f in zip(chime_events, chime_notes):
                dt = t - start_t
                if 0 <= dt < chime_len:
                    env = math.exp(-3.5 * dt) * (0.6 + 0.4 * math.sin(2 * math.pi * 0.2 * dt))
                    ch += 0.23 * env * math.sin(2 * math.pi * note_f * t)

            # ほのかなノイズ(ローパス)
            wn = (random.random() * 2.0 - 1.0) * 0.02
            noise = prev_noise * 0.997 + wn * 0.003
            prev_noise = noise

            s = drone + ch + noise * 0.4

            # フェードイン/アウトでクリック防止
            fade_edge = 0.02
            if t < fade_edge:
                s *= t / fade_edge
            if length_sec - t < fade_edge:
                s *= (length_sec - t) / fade_edge

            # 出力クリップ
            s = max(-1.0, min(1.0, s * 0.6))
            wf.writeframes(struct.pack("<h", int(s * 32767)))


def main():
    # Joy-Con初期化（より安全なエラーハンドリング）
    left_joycon = None
    right_joycon = None
    joycon_enabled = False
    
    try:
        left_joycon_id = get_L_id()
        left_joycon = JoyCon(*left_joycon_id)
        print("左Joy-Con (青) 接続完了!")
        joycon_enabled = True
    except Exception as e:
        print(f"左Joy-Con (青) が見つかりません: {e}")
    
    try:
        right_joycon_id = get_R_id()
        right_joycon = JoyCon(*right_joycon_id)
        print("右Joy-Con (赤) 接続完了!")
        if left_joycon:
            joycon_enabled = True
    except Exception as e:
        print(f"右Joy-Con (赤) が見つかりません: {e}")
    
    if not joycon_enabled:
        print("Joy-Conが利用できません。キーボード操作のみで開始します。")
    
    player = Player()
    running = True
    frame_count = 0
    font_small = pygame.font.Font(None, 22)

    # コレクタブル配置: 迷宮/街/砂浜に各1つ
    collectibles = [
        Collectible(7.5, 3.5, "sigil"),   # 迷宮(通路側に配置)
        Collectible(12.5, 12.5, "sigil"), # 街の広場
        Collectible(10.5, 16.5, "sigil"), # 砂浜
    ]
    total_sigils = len(collectibles)
    altar = Altar(13.5, 11.5)  # 街の祭壇
    message_text = None
    message_timer = 0

    # 粒子
    particles = [(random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1), random.random() * 10) for _ in range(80)]
    # 動物（エリア別）
    animals = [
        {"x": 3.5, "y": 4.5, "type": "moth", "area": "dungeon", "speed": 1.0, "seed": random.random()*10, "allowed": [0]},
        {"x": 11.5, "y": 12.5, "type": "butterfly", "area": "town", "speed": 1.2, "seed": random.random()*10, "allowed": [0]},
        {"x": 13.0, "y": 13.5, "type": "mouse", "area": "town", "speed": 1.5, "seed": random.random()*10, "allowed": [0]},
        {"x": 9.5, "y": 16.5, "type": "crab", "area": "beach", "speed": 0.8, "seed": random.random()*10, "allowed": [6]},
        {"x": 12.5, "y": 19.5, "type": "fish", "area": "ocean", "speed": 1.0, "seed": random.random()*10, "allowed": [5]},
    ]

    game_cleared = False
    path_opened = False

    # 入力デバウンス
    interact_latch = False

    # 速度設定
    MOVE_SPEED = 3.2  # units/sec
    TURN_SPEED = 2.6  # rad/sec

    def can_walk(nx, ny):
        # 半径の簡易コリジョン
        R = 0.18
        for ox, oy in ((0, 0), (R, 0), (-R, 0), (0, R), (0, -R)):
            tx, ty = int(nx + ox), int(ny + oy)
            if not (0 <= tx < len(world_map[0]) and 0 <= ty < len(world_map)):
                return False
            if world_map[ty][tx] not in (0, 5, 6):
                return False
        return True

    # BGM 準備と再生
    bgm_path = os.path.join(os.path.dirname(__file__), "generated_bgm.wav")
    ensure_bgm(bgm_path)
    music_volume = 0.30
    music_muted = False
    try:
        pygame.mixer.music.load(bgm_path)
        pygame.mixer.music.set_volume(music_volume)
        pygame.mixer.music.play(-1)
    except Exception:
        pass

    while running:
        frame_count += 1
        # ループ開始時にdt計算
        dt = clock.tick(60) / 1000.0

        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_m:
                        music_muted = not music_muted
        except Exception as e:
            print(f"Pygame イベント処理エラー: {e}")
            continue
        
        # Joy-Con入力の取得（エラーハンドリング強化）
        left_stick_h = 0
        left_stick_v = 0
        right_buttons = {}
        left_buttons = {}
        plus_pressed = False
        
        # Joy-Conの状態が悪い場合は無効化
        if left_joycon and joycon_enabled:
            try:
                left_status = left_joycon.get_status()
                if left_status and 'analog-sticks' in left_status and 'buttons' in left_status:
                    left_stick = left_status['analog-sticks']['left']
                    left_buttons = left_status['buttons']['left']
                    
                    # スティック入力を正規化（縦方向は符号反転）
                    if 'horizontal' in left_stick and 'vertical' in left_stick:
                        left_stick_h = (left_stick['horizontal'] - 2048) / 2048
                        left_stick_v = -((left_stick['vertical'] - 2048) / 2048)
                        
                        # デッドゾーン適用
                        if abs(left_stick_h) < 0.15:
                            left_stick_h = 0
                        if abs(left_stick_v) < 0.15:
                            left_stick_v = 0
            except Exception as e:
                joycon_enabled = False
                print(f"Joy-Con読み取りエラー、無効化します: {e}")
        
        if right_joycon and joycon_enabled:
            try:
                right_status = right_joycon.get_status()
                if right_status and 'buttons' in right_status:
                    right_buttons = right_status['buttons']['right']
                    plus_pressed = right_buttons.get('plus', False)
            except Exception as e:
                joycon_enabled = False
                print(f"Joy-Con読み取りエラー、無効化します: {e}")
        
        # Joy-Conのミュート機能 (右Joy-Conの+ボタン、デバウンス付き)
        if plus_pressed and not hasattr(main, 'plus_latch'):
            main.plus_latch = False
        if plus_pressed and not main.plus_latch:
            music_muted = not music_muted
            main.plus_latch = True
        elif not plus_pressed:
            main.plus_latch = False

        # キーボード入力とJoy-Con入力を統合
        keys = pygame.key.get_pressed()
        
        # 前後移動 (W/S キーまたは左スティック縦)
        if keys[pygame.K_w] or left_stick_v < -0.3:
            player.move_forward(world_map, dt, MOVE_SPEED, can_walk)
        if keys[pygame.K_s] or left_stick_v > 0.3:
            player.move_backward(world_map, dt, MOVE_SPEED, can_walk)
            
        # 回転 (Q/E キーまたは右Joy-ConのX/Bボタン)
        if keys[pygame.K_q] or right_buttons.get('x', False):
            player.turn_left(dt, TURN_SPEED)
        if keys[pygame.K_e] or right_buttons.get('b', False):
            player.turn_right(dt, TURN_SPEED)
            
        # 左右移動/回転 (A/D キー)
        if keys[pygame.K_a]:
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or left_buttons.get('zl', False):
                player.strafe_left(world_map, dt, MOVE_SPEED, can_walk)
            else:
                player.turn_left(dt, TURN_SPEED)
        if keys[pygame.K_d]:
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or left_buttons.get('zl', False):
                player.strafe_right(world_map, dt, MOVE_SPEED, can_walk)
            else:
                player.turn_right(dt, TURN_SPEED)
        
        # Joy-Conでのストレイフ (左スティック横 + ZLボタン)
        if abs(left_stick_h) > 0.3 and left_buttons.get('zl', False):
            if left_stick_h < 0:
                player.strafe_left(world_map, dt, MOVE_SPEED * abs(left_stick_h), can_walk)
            else:
                player.strafe_right(world_map, dt, MOVE_SPEED * abs(left_stick_h), can_walk)
        elif abs(left_stick_h) > 0.3:
            if left_stick_h < 0:
                player.turn_left(dt, TURN_SPEED * abs(left_stick_h))
            else:
                player.turn_right(dt, TURN_SPEED * abs(left_stick_h))

        # F: 近接インタラクト(取得/捧げる) または右Joy-ConのAボタン
        if (keys[pygame.K_f] or right_buttons.get('a', False)) and not interact_latch:
            interact_latch = True
            # 取得
            for item in collectibles:
                if not item.collected and math.hypot(player.x - item.x, player.y - item.y) < 0.8:
                    item.collected = True
                    message_text = "印章を手に入れた！"
                    message_timer = frame_count + 120
            # 祭壇
            if math.hypot(player.x - altar.x, player.y - altar.y) < 1.0 and not game_cleared:
                if sum(1 for it in collectibles if it.collected) == total_sigils:
                    altar.activated = True
                    game_cleared = True
                    message_text = "すべての印章を捧げた。海の向こうに道が見える…"
                    message_timer = frame_count + 240
                else:
                    remain = total_sigils - sum(1 for it in collectibles if it.collected)
                    message_text = f"まだ印章が {remain} つ足りない。"
                    message_timer = frame_count + 120
        elif not keys[pygame.K_f] and not right_buttons.get('a', False):
            interact_latch = False

        # メッセージタイムアウト
        if message_text and frame_count > message_timer:
            message_text = None

        # 現在のエリア
        current_area = get_current_area(player.x, player.y)

        # BGM音量のエリア連動(ソフトに追従)
        target_vol = {
            "dungeon": 0.25,
            "town": 0.30,
            "beach": 0.32,
            "ocean": 0.35,
        }.get(current_area, 0.30)
        if game_cleared:
            target_vol += 0.05
        # スムース
        music_volume += (target_vol - music_volume) * 0.02
        try:
            pygame.mixer.music.set_volume(0.0 if music_muted else music_volume)
        except Exception:
            pass

        # 背景
        draw_background_by_area(current_area, frame_count)

        # レイキャスティング & Zバッファ
        zbuffer = [1e9] * WIDTH
        for x in range(WIDTH):
            camera_x = 2 * x / WIDTH - 1
            ray_angle_offset = math.atan(camera_x * math.tan(player.fov / 2))
            distance, wall_type = cast_ray(player, ray_angle_offset)
            zbuffer[x] = distance if distance > 0 else zbuffer[x]
            if distance > 0:
                wall_height = min(WALL_HEIGHT, int(WALL_HEIGHT / distance))
                draw_wall_slice(x, wall_height, wall_type, distance)

        # スプライト(コレクタブル/祭壇)
        draw_collectibles_and_altar(player, zbuffer, collectibles, altar, frame_count, font_small)

        # 動物/蝶の描画
        draw_animals(player, zbuffer, animals, world_map, dt, frame_count, current_area)

        # エフェクト
        draw_floating_particles(frame_count, particles)

        # UI
        collected_count = sum(1 for it in collectibles if it.collected)
        objective = (
            "祭壇を探し、印章を捧げる" if collected_count == total_sigils and not game_cleared else "印章を3つ集める"
        )
        if game_cleared:
            objective = "海辺へ進み、静かな景色を眺める"
        draw_ui(collected_count, total_sigils, objective, message_text)

        # クリア後の演出: 海辺に細い道を開く(一度だけ)
        if game_cleared and not path_opened:
            # 砂浜と海の境界を一部歩行可にする
            try:
                for x in range(8, 17):
                    if world_map[18][x] == 5:
                        world_map[18][x] = 6  # 砂浜に寄せる
                    if world_map[17][x] in (5, 6):
                        world_map[17][x] = 0  # 薄い通路
                path_opened = True
            except Exception:
                path_opened = True

        # ささやかなクリア演出: クリア後は海の波が少し明るくなる
        if game_cleared and current_area == "ocean":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((220, 240, 255, 20))
            screen.blit(overlay, (0, 0))

        # ミニマップ
        draw_minimap(player, collectibles, altar)

        pygame.display.flip()

    # Joy-Conをクリーンアップ
    if left_joycon:
        try:
            left_joycon.disconnect()
        except:
            pass
    if right_joycon:
        try:
            right_joycon.disconnect()
        except:
            pass
    
    pygame.quit()


if __name__ == "__main__":
    main()
