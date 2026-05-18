import pygame
import sys
import math
import random
from collections import deque

pygame.init()

CELL = 24
COLS = 28
ROWS = 31
W = COLS * CELL
H = ROWS * CELL + 60
FPS = 60

BLACK = (0,0,0)
YELLOW = (255,220,0)
WHITE = (255,255,255)
BLUE = (33,33,222)
DBLUE = (0,0,80)
RED = (220,0,0)
PINK = (255,182,255)
CYAN = (0,220,220)
ORANGE = (255,165,0)
DGRAY = (40,40,40)
LBLUE = (100,100,255)

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

WALL = 0
DOT = 1
POWER = 2
EMPTY = 3
DOOR = 4

def make_maze():
    grid = []
    dots = []
    powers = []
    for r in range(31):
        row = []
        for c in range(28):
            ch = RAW_MAZE[r][c]
            if ch == 'W':
                row.append(WALL)
            elif ch == '.':
                row.append(DOT)
                dots.append((c, r))
            elif ch == 'o':
                row.append(POWER)
                powers.append((c, r))
            elif ch == '-':
                row.append(DOOR)
            else:
                row.append(EMPTY)
        grid.append(row)
    return grid, dots, powers

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
DIRS = [UP, DOWN, LEFT, RIGHT]

def find_path(grid, start, target):
    sr, sc = start
    tr, tc = target
    if (sr, sc) == (tr, tc):
        return start
    
    visited = {(sr, sc): None}
    q = deque([(sr, sc)])
    
    while q:
        r, c = q.popleft()
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
            q.append((nr, nc))
    return start

class Ghost:
    def __init__(self, name, grid):
        self.name = name
        self.grid = grid
        
        if name == 'blinky':
            self.color = RED
            self.sx, self.sy = 13, 11
            self.exit_wait = 0
        elif name == 'pinky':
            self.color = PINK
            self.sx, self.sy = 13, 13
            self.exit_wait = 60
        elif name == 'inky':
            self.color = CYAN
            self.sx, self.sy = 11, 13
            self.exit_wait = 120
        else:
            self.color = ORANGE
            self.sx, self.sy = 15, 13
            self.exit_wait = 180
        
        self.scatter = {
            'blinky': (25, 0),
            'pinky': (2, 0),
            'inky': (25, 30),
            'clyde': (2, 30)
        }
        
        self.reset()
    
    def reset(self):
        self.col = self.sx
        self.row = self.sy
        self.x = self.col * CELL
        self.y = self.row * CELL
        self.dir = LEFT
        self.scared = False
        self.eaten = False
        self.timer = self.exit_wait
        self.speed = 1.5
        self.scare_timer = 0
    
    def get_target(self, pc, pr, pd, bc, br):
        if self.scared:
            return (random.randint(0,27), random.randint(0,30))
        if self.eaten:
            return (13, 13)
        if self.name == 'blinky':
            return (pc, pr)
        elif self.name == 'pinky':
            return (pc + pd[0]*4, pr + pd[1]*4)
        elif self.name == 'inky':
            mx = pc + pd[0]*2
            my = pr + pd[1]*2
            return (2*mx - bc, 2*my - br)
        else:
            d = math.hypot(self.col-pc, self.row-pr)
            if d > 8:
                return (pc, pr)
            else:
                return self.scatter['clyde']
    
    def move(self, pc, pr, pd, bc, br):
        sp = self.speed
        if self.scared:
            sp = 0.9
        if self.eaten:
            sp = 2.5
        
        if self.timer > 0:
            self.timer -= 1
            return
        
        if self.scare_timer > 0:
            self.scare_timer -= 1
            if self.scare_timer == 0:
                self.scared = False
        
        if self.eaten and (self.col, self.row) == (13, 13):
            self.eaten = False
            self.scared = False
        
        tx, ty = self.get_target(pc, pr, pd, bc, br)
        
        cx = self.col * CELL
        cy = self.row * CELL
        
        if abs(self.x - cx) < sp and abs(self.y - cy) < sp:
            self.x = cx
            self.y = cy
            next_cell = find_path(self.grid, (self.row, self.col), (ty, tx))
            if next_cell != (self.row, self.col):
                nr, nc = next_cell
                self.dir = (nc - self.col, nr - self.row)
            else:
                random.shuffle(DIRS)
                for d in DIRS:
                    nx = self.col + d[0]
                    ny = self.row + d[1]
                    if 0 <= ny < 31 and 0 <= nx < 28 and self.grid[ny][nx] != WALL:
                        self.dir = d
                        break
        
        self.x += self.dir[0] * sp
        self.y += self.dir[1] * sp
        
        if self.x < -CELL:
            self.x = W
        elif self.x > W:
            self.x = -CELL
        
        self.col = round(self.x / CELL)
        self.row = round(self.y / CELL)
        self.col = max(0, min(27, self.col))
        self.row = max(0, min(30, self.row))
    
    def scare(self):
        if not self.eaten:
            self.scared = True
            self.scare_timer = 6 * FPS
    
    def draw(self, surf):
        cx = int(self.x) + CELL//2
        cy = int(self.y) + CELL//2 + 60
        r = CELL//2 - 1
        
        if self.scared:
            if self.scare_timer > FPS*2 or (self.scare_timer // 8) % 2 == 0:
                col = LBLUE
            else:
                col = WHITE
        elif self.eaten:
            col = WHITE
        else:
            col = self.color
        
        if self.eaten:
            pygame.draw.circle(surf, WHITE, (cx-4, cy-3), 3)
            pygame.draw.circle(surf, WHITE, (cx+4, cy-3), 3)
            pygame.draw.circle(surf, BLUE, (cx-3, cy-2), 2)
            pygame.draw.circle(surf, BLUE, (cx+5, cy-2), 2)
            return
        
        pygame.draw.circle(surf, col, (cx, cy), r)
        pygame.draw.rect(surf, col, (cx-r, cy, r*2, r))
        
        for i in range(3):
            xo = cx - r + i*(r*2//3)
            pygame.draw.circle(surf, BLACK, (xo + (r//3), cy+r), r//3)
        
        if not self.scared:
            pygame.draw.circle(surf, WHITE, (cx-4, cy-3), 3)
            pygame.draw.circle(surf, WHITE, (cx+4, cy-3), 3)
            pygame.draw.circle(surf, BLUE, (cx-3, cy-2), 2)
            pygame.draw.circle(surf, BLUE, (cx+5, cy-2), 2)
        else:
            pygame.draw.circle(surf, WHITE, (cx-4, cy-2), 2)
            pygame.draw.circle(surf, WHITE, (cx+4, cy-2), 2)
            pts = [(cx-5,cy+3),(cx-3,cy+1),(cx-1,cy+3),(cx+1,cy+1),(cx+3,cy+3),(cx+5,cy+1)]
            pygame.draw.lines(surf, WHITE, False, pts, 1)

class PacMan:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.col = 14
        self.row = 23
        self.x = self.col * CELL
        self.y = self.row * CELL
        self.dir = LEFT
        self.next = LEFT
        self.speed = 2.0
        self.mouth = 45
        self.opening = False
        self.counter = 0
        self.alive = True
        self.death = 0
    
    def set_dir(self, d):
        self.next = d
    
    def can_move(self, grid, col, row, d):
        nx = col + d[0]
        ny = row + d[1]
        if nx < 0 or nx >= 28 or ny < 0 or ny >= 31:
            return True
        return grid[ny][nx] not in (WALL, DOOR)
    
    def update(self, grid):
        if not self.alive:
            self.death += 1
            return
        
        self.counter += 1
        if self.counter >= 4:
            self.counter = 0
            if self.opening:
                self.mouth += 10
                if self.mouth >= 75:
                    self.opening = False
            else:
                self.mouth -= 10
                if self.mouth <= 15:
                    self.opening = True
        
        cx = self.col * CELL
        cy = self.row * CELL
        aligned = abs(self.x - cx) < self.speed and abs(self.y - cy) < self.speed
        
        if aligned:
            self.x = cx
            self.y = cy
            if self.can_move(grid, self.col, self.row, self.next):
                self.dir = self.next
            if not self.can_move(grid, self.col, self.row, self.dir):
                return
        
        self.x += self.dir[0] * self.speed
        self.y += self.dir[1] * self.speed
        
        if self.x < -CELL:
            self.x = W
        elif self.x > W:
            self.x = -CELL
        
        self.col = round(self.x / CELL)
        self.row = round(self.y / CELL)
        self.col = max(0, min(27, self.col))
        self.row = max(0, min(30, self.row))
    
    def draw(self, surf):
        cx = int(self.x) + CELL//2
        cy = int(self.y) + CELL//2 + 60
        r = CELL//2 - 2
        
        if not self.alive:
            f = max(0, 1 - self.death / 40)
            r2 = int(r * f)
            if r2 > 0:
                pygame.draw.circle(surf, YELLOW, (cx, cy), r2)
            return
        
        pygame.draw.circle(surf, YELLOW, (cx, cy), r)
        
        mouth_size = int(r * (self.mouth / 90))
        
        if self.dir == RIGHT:
            p1 = (cx + r, cy - mouth_size)
            p2 = (cx + r, cy + mouth_size)
            p3 = (cx, cy)
        elif self.dir == LEFT:
            p1 = (cx - r, cy - mouth_size)
            p2 = (cx - r, cy + mouth_size)
            p3 = (cx, cy)
        elif self.dir == UP:
            p1 = (cx - mouth_size, cy - r)
            p2 = (cx + mouth_size, cy - r)
            p3 = (cx, cy)
        else:
            p1 = (cx - mouth_size, cy + r)
            p2 = (cx + mouth_size, cy + r)
            p3 = (cx, cy)
        
        pygame.draw.polygon(surf, BLACK, [p1, p2, p3])

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("PAC-MAN")
        self.clock = pygame.time.Clock()
        self.font1 = pygame.font.SysFont("monospace", 28, bold=True)
        self.font2 = pygame.font.SysFont("monospace", 18, bold=True)
        self.new_game()
    
    def new_game(self):
        self.grid, self.dots, self.powers = make_maze()
        self.remaining = set(self.dots) | set(self.powers)
        self.score = 0
        self.lives = 3
        self.level = 1
        self.state = 'playing'
        self.death_timer = 0
        self.combo = 0
        self.pac = PacMan()
        self.ghosts = [
            Ghost('blinky', self.grid),
            Ghost('pinky', self.grid),
            Ghost('inky', self.grid),
            Ghost('clyde', self.grid)
        ]
    
    def respawn(self):
        self.pac = PacMan()
        for g in self.ghosts:
            g.reset()
        self.combo = 0
    
    def check_keys(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if self.state in ('dead','gameover','win'):
                    if event.key == pygame.K_r:
                        self.new_game()
                    return
                if event.key == pygame.K_a:
                    self.pac.set_dir(LEFT)
                if event.key == pygame.K_d:
                    self.pac.set_dir(RIGHT)
                if event.key == pygame.K_w:
                    self.pac.set_dir(UP)
                if event.key == pygame.K_s:
                    self.pac.set_dir(DOWN)
    
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
        
        bx = self.ghosts[0].col
        by = self.ghosts[0].row
        
        for g in self.ghosts:
            g.move(self.pac.col, self.pac.row, self.pac.dir, bx, by)
        
        pos = (self.pac.col, self.pac.row)
        if pos in self.remaining:
            cell = self.grid[pos[1]][pos[0]]
            self.remaining.remove(pos)
            self.grid[pos[1]][pos[0]] = EMPTY
            if cell == DOT:
                self.score += 10
            elif cell == POWER:
                self.score += 50
                self.combo = 0
                for g in self.ghosts:
                    g.scare()
        
        if not self.remaining:
            self.state = 'win'
            return
        
        for g in self.ghosts:
            d = math.hypot(g.x - self.pac.x, g.y - self.pac.y)
            if d < CELL * 0.8:
                if g.scared and not g.eaten:
                    g.eaten = True
                    g.scared = False
                    self.combo += 1
                    self.score += 200 * (2 ** (self.combo - 1))
                elif not g.scared and not g.eaten:
                    self.lives -= 1
                    self.pac.alive = False
                    self.state = 'dead'
                    self.death_timer = 60
                    return
    
    def draw_maze(self):
        for r in range(31):
            for c in range(28):
                x = c * CELL
                y = r * CELL + 60
                cell = self.grid[r][c]
                if cell == WALL:
                    pygame.draw.rect(self.screen, BLUE, (x+1, y+1, CELL-2, CELL-2), border_radius=3)
                    pygame.draw.rect(self.screen, DBLUE, (x+2, y+2, CELL-4, CELL-4), border_radius=2)
                elif cell == DOT:
                    pygame.draw.circle(self.screen, WHITE, (x+CELL//2, y+CELL//2), 2)
                elif cell == POWER:
                    t = pygame.time.get_ticks()
                    pulse = int(4 + 3*math.sin(t/200))
                    pygame.draw.circle(self.screen, WHITE, (x+CELL//2, y+CELL//2), pulse)
                elif cell == DOOR:
                    pygame.draw.rect(self.screen, PINK, (x, y+CELL//2-2, CELL, 4))
    
    def draw_hud(self):
        pygame.draw.rect(self.screen, DGRAY, (0, 0, W, 56))
        
        txt = self.font1.render(f"SCORE {self.score:06d}", True, WHITE)
        self.screen.blit(txt, (10, 12))
        
        txt = self.font2.render(f"LVL {self.level}", True, YELLOW)
        self.screen.blit(txt, (W - 90, 18))
        
        for i in range(self.lives):
            cx = W//2 - 40 + i*26
            cy = 30
            pygame.draw.circle(self.screen, YELLOW, (cx, cy), 9)
            pygame.draw.polygon(self.screen, BLACK, [(cx, cy), (cx+9, cy-6), (cx+9, cy+6)])
    
    def draw_overlay(self):
        if self.state == 'gameover':
            txt1 = self.font1.render("GAME OVER", True, RED)
            txt2 = self.font2.render("Press R to restart", True, WHITE)
            self.screen.blit(txt1, (W//2 - txt1.get_width()//2, H//2 - 30))
            self.screen.blit(txt2, (W//2 - txt2.get_width()//2, H//2 + 10))
        elif self.state == 'win':
            txt1 = self.font1.render("YOU WIN!", True, YELLOW)
            txt2 = self.font2.render("Press R to restart", True, WHITE)
            self.screen.blit(txt1, (W//2 - txt1.get_width()//2, H//2 - 30))
            self.screen.blit(txt2, (W//2 - txt2.get_width()//2, H//2 + 10))
    
    def run(self):
        while True:
            self.screen.fill(BLACK)
            self.check_keys()
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