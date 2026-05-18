import pygame
import sys
import math
import random
from collections import deque

# ── Constants ──────────────────────────────────────────────────────────────────
CELL  = 24
COLS  = 28
ROWS  = 31
W     = COLS * CELL
H     = ROWS * CELL + 60
FPS   = 60

BLACK   = (0,   0,   0)
YELLOW  = (255, 220,  0)
WHITE   = (255, 255, 255)
BLUE    = (33,  33, 222)
DBLUE   = (0,   0,  80)
RED     = (220,  0,  0)
PINK    = (255, 182, 255)
CYAN    = (0,  220, 220)
ORANGE  = (255, 165,  0)
DGRAY   = (40,  40,  40)
LBLUE   = (100, 100, 255)

RAW_MAZE = [
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    "W............WW............W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "WoWWWW.WWWWW.WW.WWWWW.WWWWoW",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "W..........................W",
    "W.WWWW.WW.WWWWWWWW.WW.WWWW.W",
    "W.WWWW.WW.WWWWWWWW.WW.WWWW.W",
    "W......WW....WW....WW......W",
    "WWWWWW.WWWWW WW WWWWW.WWWWWW",
    "WWWWWW.WWWWW WW WWWWW.WWWWWW",
    "WWWWWW.WW          WW.WWWWWW",
    "WWWWWW.WW WWW--WWW WW.WWWWWW",
    "WWWWWW.WW W      W WW.WWWWWW",
    "      .   W      W   .      ",
    "WWWWWW.WW W      W WW.WWWWWW",
    "WWWWWW.WW WWWWWWWW WW.WWWWWW",
    "WWWWWW.WW          WW.WWWWWW",
    "WWWWWW.WW WWWWWWWW WW.WWWWWW",
    "WWWWWW.WW WWWWWWWW WW.WWWWWW",
    "W............WW............W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "Wo..WW................WW..oW",
    "WWW.WW.WW.WWWWWWWW.WW.WW.WWW",
    "WWW.WW.WW.WWWWWWWW.WW.WW.WWW",
    "W......WW....WW....WW......W",
    "W.WWWWWWWWWW.WW.WWWWWWWWWW.W",
    "W.WWWWWWWWWW.WW.WWWWWWWWWW.W",
    "W..........................W",
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWW",
]

WALL = 0; DOT = 1; POWER = 2; EMPTY = 3; DOOR = 4

def parse_maze():
    grid = []
    dots = []
    powers = []
    for r, row in enumerate(RAW_MAZE):
        line = []
        for c, ch in enumerate(row):
            if   ch == 'W': line.append(WALL)
            elif ch == '.': line.append(DOT);   dots.append((c, r))
            elif ch == 'o': line.append(POWER);  powers.append((c, r))
            elif ch == '-': line.append(DOOR)
            else:           line.append(EMPTY)
        grid.append(line)
    return grid, dots, powers

UP    = (0, -1)
DOWN  = (0,  1)
LEFT  = (-1, 0)
RIGHT = (1,  0)
DIRS  = [UP, DOWN, LEFT, RIGHT]

def bfs_next(grid, start, target):
    sr, sc = start
    tr, tc = target
    if (sr, sc) == (tr, tc):
        return start
    visited = {(sr, sc): None}
    queue   = deque([(sr, sc)])
    while queue:
        r, c = queue.popleft()
        for dr, dc in DIRS:
            nr, nc = r+dr, c+dc
            if nr < 0 or nr >= 31 or nc < 0 or nc >= 28:
                continue
            if (nr, nc) in visited:
                continue
            if grid[nr][nc] == WALL:
                continue
            visited[(nr, nc)] = (r, c)
            if nr == tr and nc == tc:
                cur = (nr, nc)
                while visited[cur] != (sr, sc):
                    cur = visited[cur]
                return cur
            queue.append((nr, nc))
    return start

class Ghost:
    SCATTER_CORNERS = {
        'blinky': (25, 0),
        'pinky':  (2,  0),
        'inky':   (25, 30),
        'clyde':  (2,  30),
    }
    COLORS = {
        'blinky': RED,
        'pinky':  PINK,
        'inky':   CYAN,
        'clyde':  ORANGE,
    }

    def __init__(self, name, grid):
        self.name  = name
        self.color = self.COLORS[name]
        self.grid  = grid
        self.reset()

    def reset(self):
        spawn = {'blinky':(13,11),'pinky':(13,13),'inky':(11,13),'clyde':(15,13)}
        sx, sy = spawn[self.name]
        self.col = sx; self.row = sy
        self.px  = sx * CELL; self.py = sy * CELL
        self.dir = LEFT
        self.frightened   = False
        self.eaten        = False
        self.exit_timer   = {'blinky':0,'pinky':60,'inky':120,'clyde':180}[self.name]
        self.speed        = 1.5
        self.fright_timer = 0

    def target_cell(self, pac_col, pac_row, pac_dir, blinky_col, blinky_row):
        if self.frightened:
            return (random.randint(0,27), random.randint(0,30))
        if self.eaten:
            return (13, 13)
        if self.name == 'blinky':
            return (pac_col, pac_row)
        elif self.name == 'pinky':
            return (pac_col + pac_dir[0]*4, pac_row + pac_dir[1]*4)
        elif self.name == 'inky':
            mid = (pac_col + pac_dir[0]*2, pac_row + pac_dir[1]*2)
            return (2*mid[0]-blinky_col, 2*mid[1]-blinky_row)
        else:
            dist = math.hypot(self.col-pac_col, self.row-pac_row)
            return (pac_col, pac_row) if dist > 8 else self.SCATTER_CORNERS['clyde']

    def update(self, pac_col, pac_row, pac_dir, blinky_col, blinky_row):
        speed = self.speed
        if self.frightened: speed = 0.9
        if self.eaten:      speed = 2.5

        if self.exit_timer > 0:
            self.exit_timer -= 1
            return

        if self.fright_timer > 0:
            self.fright_timer -= 1
            if self.fright_timer == 0:
                self.frightened = False

        if self.eaten and (self.col, self.row) == (13, 13):
            self.eaten = False
            self.frightened = False

        target = self.target_cell(pac_col, pac_row, pac_dir, blinky_col, blinky_row)
        cx = self.col * CELL; cy = self.row * CELL
        if abs(self.px - cx) < speed and abs(self.py - cy) < speed:
            self.px = cx; self.py = cy
            next_cell = bfs_next(self.grid, (self.row, self.col), (target[1], target[0]))
            if next_cell != (self.row, self.col):
                nr, nc = next_cell
                self.dir = (nc - self.col, nr - self.row)
            else:
                random.shuffle(DIRS)
                for d in DIRS:
                    nc2, nr2 = self.col+d[0], self.row+d[1]
                    if 0<=nr2<31 and 0<=nc2<28 and self.grid[nr2][nc2] != WALL:
                        self.dir = d; break

        self.px += self.dir[0] * speed
        self.py += self.dir[1] * speed
        if self.px < -CELL:      self.px = W
        elif self.px > W:        self.px = -CELL
        self.col = round(self.px / CELL)
        self.row = round(self.py / CELL)
        self.col = max(0, min(27, self.col))
        self.row = max(0, min(30, self.row))

    def frighten(self):
        if not self.eaten:
            self.frightened   = True
            self.fright_timer = 6 * FPS

    def draw(self, surf):
        cx = int(self.px) + CELL//2
        cy = int(self.py) + CELL//2 + 60
        r  = CELL//2 - 1

        if self.frightened:
            t = self.fright_timer
            col = LBLUE if t > FPS*2 or (t // 8) % 2 == 0 else WHITE
        elif self.eaten:
            col = WHITE
        else:
            col = self.color

        if self.eaten:
            for ex, ey in [(-4, -3), (4, -3)]:
                pygame.draw.circle(surf, WHITE, (cx+ex, cy+ey), 3)
                pygame.draw.circle(surf, BLUE,  (cx+ex+1, cy+ey+1), 2)
            return

        pygame.draw.circle(surf, col, (cx, cy), r)
        pygame.draw.rect(surf, col, (cx-r, cy, r*2, r))
        for i in range(3):
            x0 = cx - r + i*(r*2//3)
            pygame.draw.circle(surf, BLACK, (x0 + (r//3), cy+r), r//3)
        
        if not self.frightened:
            for ex, ey in [(-4, -3), (4, -3)]:
                pygame.draw.circle(surf, WHITE, (cx+ex, cy+ey), 3)
                pygame.draw.circle(surf, BLUE,  (cx+ex+1, cy+ey+1), 2)
        else:
            pygame.draw.circle(surf, WHITE, (cx-4, cy-2), 2)
            pygame.draw.circle(surf, WHITE, (cx+4, cy-2), 2)
            pts = [(cx-5,cy+3),(cx-3,cy+1),(cx-1,cy+3),(cx+1,cy+1),(cx+3,cy+3),(cx+5,cy+1)]
            pygame.draw.lines(surf, WHITE, False, pts, 1)

# ── SIMPLIFIED PERFECT PAC-MAN - Draws circle with mouth cutout ───────────────
class PacMan:
    def __init__(self):
        self.reset()

    def reset(self):
        self.col   = 14; self.row = 23
        self.px    = self.col * CELL
        self.py    = self.row * CELL
        self.dir   = LEFT
        self.next_dir = LEFT
        self.speed = 2.0
        self.mouth_angle = 45
        self.mouth_opening = False
        self.animation_counter = 0
        self.alive = True
        self.death_frame = 0

    def set_dir(self, d):
        self.next_dir = d

    def can_move(self, grid, col, row, d):
        nc, nr = col + d[0], row + d[1]
        if nc < 0 or nc >= 28 or nr < 0 or nr >= 31:
            return True
        return grid[nr][nc] not in (WALL, DOOR)

    def update(self, grid):
        if not self.alive:
            self.death_frame += 1
            return

        self.animation_counter += 1
        if self.animation_counter >= 4:
            self.animation_counter = 0
            if self.mouth_opening:
                self.mouth_angle += 10
                if self.mouth_angle >= 75:
                    self.mouth_opening = False
            else:
                self.mouth_angle -= 10
                if self.mouth_angle <= 15:
                    self.mouth_opening = True

        cx = self.col * CELL; cy = self.row * CELL
        aligned = abs(self.px - cx) < self.speed and abs(self.py - cy) < self.speed

        if aligned:
            self.px = cx; self.py = cy
            if self.can_move(grid, self.col, self.row, self.next_dir):
                self.dir = self.next_dir
            if not self.can_move(grid, self.col, self.row, self.dir):
                return

        self.px += self.dir[0] * self.speed
        self.py += self.dir[1] * self.speed

        if self.px < -CELL:  self.px = W
        elif self.px > W:    self.px = -CELL

        self.col = round(self.px / CELL)
        self.row = round(self.py / CELL)
        self.col = max(0, min(27, self.col))
        self.row = max(0, min(30, self.row))

    def draw(self, surf):
        cx = int(self.px) + CELL//2
        cy = int(self.py) + CELL//2 + 60
        r = CELL//2 - 2

        if not self.alive:
            frac = max(0, 1 - self.death_frame / 40)
            r2 = int(r * frac)
            if r2 > 0:
                pygame.draw.circle(surf, YELLOW, (cx, cy), r2)
            return

        # Draw the main yellow circle
        pygame.draw.circle(surf, YELLOW, (cx, cy), r)
        
        # Calculate mouth triangle points based on direction
        mouth_size = int(r * (self.mouth_angle / 90))  # Scale mouth size with angle
        
        if self.dir == RIGHT:
            # Mouth pointing RIGHT
            point1 = (cx + r, cy - mouth_size)
            point2 = (cx + r, cy + mouth_size)
            point3 = (cx, cy)
        elif self.dir == LEFT:
            # Mouth pointing LEFT
            point1 = (cx - r, cy - mouth_size)
            point2 = (cx - r, cy + mouth_size)
            point3 = (cx, cy)
        elif self.dir == UP:
            # Mouth pointing UP
            point1 = (cx - mouth_size, cy - r)
            point2 = (cx + mouth_size, cy - r)
            point3 = (cx, cy)
        else:  # DOWN
            # Mouth pointing DOWN
            point1 = (cx - mouth_size, cy + r)
            point2 = (cx + mouth_size, cy + r)
            point3 = (cx, cy)
        
        # Draw the mouth (black triangle cutout)
        pygame.draw.polygon(surf, BLACK, [point1, point2, point3])

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("PAC-MAN")
        self.screen = pygame.display.set_mode((W, H))
        self.clock  = pygame.time.Clock()
        self.font_big   = pygame.font.SysFont("monospace", 28, bold=True)
        self.font_small = pygame.font.SysFont("monospace", 18, bold=True)
        self.new_game()

    def new_game(self):
        self.grid, self.dots, self.powers = parse_maze()
        self.remaining = set(map(tuple, self.dots)) | set(map(tuple, self.powers))
        self.score = 0
        self.lives = 3
        self.level = 1
        self.state = 'playing'
        self.death_timer = 0
        self.ghost_combo = 0
        self.pac = PacMan()
        self.ghosts = [Ghost(n, self.grid) for n in ('blinky','pinky','inky','clyde')]

    def respawn(self):
        self.pac = PacMan()
        for g in self.ghosts:
            g.reset()
        self.ghost_combo = 0

    def handle_input(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if self.state in ('dead','gameover','win'):
                    if ev.key == pygame.K_RETURN:
                        self.new_game()
                    return
                if ev.key == pygame.K_LEFT:  self.pac.set_dir(LEFT)
                if ev.key == pygame.K_RIGHT: self.pac.set_dir(RIGHT)
                if ev.key == pygame.K_UP:    self.pac.set_dir(UP)
                if ev.key == pygame.K_DOWN:  self.pac.set_dir(DOWN)

    def update(self):
        if self.state != 'playing':
            if self.state == 'dead':
                self.death_timer -= 1
                self.pac.update(self.grid)
                if self.death_timer <= 0:
                    if self.lives <= 0:
                        self.state = 'gameover'
                    else:
                        self.respawn()
                        self.state = 'playing'
            return

        self.pac.update(self.grid)
        blinky = self.ghosts[0]
        for g in self.ghosts:
            g.update(self.pac.col, self.pac.row, self.pac.dir, blinky.col, blinky.row)

        pos = (self.pac.col, self.pac.row)
        if pos in self.remaining:
            cell = self.grid[pos[1]][pos[0]]
            self.remaining.discard(pos)
            self.grid[pos[1]][pos[0]] = EMPTY
            if cell == DOT:
                self.score += 10
            elif cell == POWER:
                self.score += 50
                self.ghost_combo = 0
                for g in self.ghosts:
                    g.frighten()

        if not self.remaining:
            self.state = 'win'
            return

        for g in self.ghosts:
            dist = math.hypot(g.px - self.pac.px, g.py - self.pac.py)
            if dist < CELL * 0.8:
                if g.frightened and not g.eaten:
                    g.eaten = True
                    g.frightened = False
                    self.ghost_combo += 1
                    self.score += 200 * (2 ** (self.ghost_combo - 1))
                elif not g.frightened and not g.eaten:
                    self.lives -= 1
                    self.pac.alive = False
                    self.state = 'dead'
                    self.death_timer = 60
                    return

    def draw_maze(self):
        surf = self.screen
        surf.fill(BLACK)
        for r in range(31):
            for c in range(28):
                x = c * CELL; y = r * CELL + 60
                cell = self.grid[r][c]
                if cell == WALL:
                    pygame.draw.rect(surf, BLUE, (x+1, y+1, CELL-2, CELL-2), border_radius=3)
                    pygame.draw.rect(surf, DBLUE, (x+2, y+2, CELL-4, CELL-4), border_radius=2)
                elif cell == DOT:
                    pygame.draw.circle(surf, WHITE, (x+CELL//2, y+CELL//2), 2)
                elif cell == POWER:
                    t = pygame.time.get_ticks()
                    pulse = int(4 + 3*math.sin(t/200))
                    pygame.draw.circle(surf, WHITE, (x+CELL//2, y+CELL//2), pulse)
                elif cell == DOOR:
                    pygame.draw.rect(surf, PINK, (x, y+CELL//2-2, CELL, 4))

    def draw_hud(self):
        surf = self.screen
        pygame.draw.rect(surf, DGRAY, (0, 0, W, 56))
        sc = self.font_big.render(f"SCORE {self.score:06d}", True, WHITE)
        surf.blit(sc, (10, 12))
        lv = self.font_small.render(f"LVL {self.level}", True, YELLOW)
        surf.blit(lv, (W - 90, 18))
        for i in range(self.lives):
            cx = W//2 - 40 + i*26
            cy = 30
            pygame.draw.circle(surf, YELLOW, (cx, cy), 9)
            pygame.draw.polygon(surf, BLACK, [(cx, cy), (cx+9, cy-6), (cx+9, cy+6)])

    def draw_overlay(self):
        surf = self.screen
        if self.state == 'gameover':
            txt1 = self.font_big.render("GAME  OVER", True, RED)
            txt2 = self.font_small.render("Press ENTER to restart", True, WHITE)
            surf.blit(txt1, (W//2 - txt1.get_width()//2, H//2 - 30))
            surf.blit(txt2, (W//2 - txt2.get_width()//2, H//2 + 10))
        elif self.state == 'win':
            txt1 = self.font_big.render("YOU  WIN!", True, YELLOW)
            txt2 = self.font_small.render("Press ENTER to restart", True, WHITE)
            surf.blit(txt1, (W//2 - txt1.get_width()//2, H//2 - 30))
            surf.blit(txt2, (W//2 - txt2.get_width()//2, H//2 + 10))

    def run(self):
        while True:
            self.handle_input()
            self.update()
            self.draw_maze()
            self.pac.draw(self.screen)
            for g in self.ghosts:
                g.draw(self.screen)
            self.draw_hud()
            self.draw_overlay()
            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == '__main__':
    Game().run()