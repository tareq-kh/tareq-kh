"""
Tetris — a classic falling-blocks game built with pygame.

Controls:
    Left / Right      Move piece horizontally
    Down              Soft drop (move down faster)
    Up / X            Rotate clockwise
    Z                 Rotate counter-clockwise
    Space             Hard drop (slam to bottom)
    C                 Hold piece
    P                 Pause / resume
    Esc / Q           Quit

Run:
    pip install pygame
    python tetris.py
"""

import random
import sys

import pygame

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
COLS, ROWS = 10, 20          # Playfield size in cells
CELL = 30                    # Pixel size of one cell
SIDEBAR = 6 * CELL           # Width of the right-hand info panel
WIDTH = COLS * CELL + SIDEBAR
HEIGHT = ROWS * CELL
FPS = 60

# Colors (R, G, B)
BLACK = (15, 15, 20)
GRID = (40, 40, 50)
WHITE = (235, 235, 240)
GREY = (120, 120, 130)

# Tetromino definitions. Each shape is a list of rotation states, where each
# state is a list of (row, col) offsets occupied by the four blocks.
SHAPES = {
    "I": [[(1, 0), (1, 1), (1, 2), (1, 3)],
          [(0, 2), (1, 2), (2, 2), (3, 2)],
          [(2, 0), (2, 1), (2, 2), (2, 3)],
          [(0, 1), (1, 1), (2, 1), (3, 1)]],
    "O": [[(0, 1), (0, 2), (1, 1), (1, 2)]],
    "T": [[(0, 1), (1, 0), (1, 1), (1, 2)],
          [(0, 1), (1, 1), (1, 2), (2, 1)],
          [(1, 0), (1, 1), (1, 2), (2, 1)],
          [(0, 1), (1, 0), (1, 1), (2, 1)]],
    "S": [[(0, 1), (0, 2), (1, 0), (1, 1)],
          [(0, 1), (1, 1), (1, 2), (2, 2)],
          [(1, 1), (1, 2), (2, 0), (2, 1)],
          [(0, 0), (1, 0), (1, 1), (2, 1)]],
    "Z": [[(0, 0), (0, 1), (1, 1), (1, 2)],
          [(0, 2), (1, 1), (1, 2), (2, 1)],
          [(1, 0), (1, 1), (2, 1), (2, 2)],
          [(0, 1), (1, 0), (1, 1), (2, 0)]],
    "J": [[(0, 0), (1, 0), (1, 1), (1, 2)],
          [(0, 1), (0, 2), (1, 1), (2, 1)],
          [(1, 0), (1, 1), (1, 2), (2, 2)],
          [(0, 1), (1, 1), (2, 0), (2, 1)]],
    "L": [[(0, 2), (1, 0), (1, 1), (1, 2)],
          [(0, 1), (1, 1), (2, 1), (2, 2)],
          [(1, 0), (1, 1), (1, 2), (2, 0)],
          [(0, 0), (0, 1), (1, 1), (2, 1)]],
}

COLORS = {
    "I": (45, 200, 220),
    "O": (240, 210, 60),
    "T": (170, 80, 220),
    "S": (80, 210, 100),
    "Z": (230, 70, 90),
    "J": (70, 110, 230),
    "L": (235, 150, 50),
}

# Standard scoring for line clears (index = number of lines cleared).
LINE_SCORES = [0, 100, 300, 500, 800]


class Piece:
    """A single tetromino with position and rotation state."""

    def __init__(self, kind):
        self.kind = kind
        self.rotation = 0
        self.row = 0
        # Spawn roughly centered near the top.
        self.col = COLS // 2 - 2

    def cells(self, rotation=None, row=None, col=None):
        """Return the absolute (row, col) cells this piece occupies."""
        rotation = self.rotation if rotation is None else rotation
        row = self.row if row is None else row
        col = self.col if col is None else col
        states = SHAPES[self.kind]
        offsets = states[rotation % len(states)]
        return [(row + r, col + c) for r, c in offsets]


class Bag:
    """7-bag randomizer: yields each of the 7 pieces once before reshuffling."""

    def __init__(self):
        self._items = []

    def next(self):
        if not self._items:
            self._items = list(SHAPES.keys())
            random.shuffle(self._items)
        return Piece(self._items.pop())


class Tetris:
    def __init__(self):
        # The board stores either None (empty) or a piece-kind string (filled).
        self.board = [[None] * COLS for _ in range(ROWS)]
        self.bag = Bag()
        self.current = self.bag.next()
        self.next_piece = self.bag.next()
        self.hold = None
        self.hold_used = False
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.paused = False

    # -- collision & locking -------------------------------------------------
    def valid(self, rotation=None, row=None, col=None):
        for r, c in self.current.cells(rotation, row, col):
            if c < 0 or c >= COLS or r >= ROWS:
                return False
            if r >= 0 and self.board[r][c] is not None:
                return False
        return True

    def lock(self):
        for r, c in self.current.cells():
            if r < 0:
                # Piece locked above the top -> game over.
                self.game_over = True
                continue
            self.board[r][c] = self.current.kind
        self.clear_lines()
        self.spawn_next()

    def spawn_next(self):
        self.current = self.next_piece
        self.next_piece = self.bag.next()
        self.hold_used = False
        if not self.valid():
            self.game_over = True

    def clear_lines(self):
        remaining = [row for row in self.board if any(c is None for c in row)]
        cleared = ROWS - len(remaining)
        if cleared:
            for _ in range(cleared):
                remaining.insert(0, [None] * COLS)
            self.board = remaining
            self.score += LINE_SCORES[cleared] * self.level
            self.lines += cleared
            self.level = 1 + self.lines // 10

    # -- player actions ------------------------------------------------------
    def move(self, dr, dc):
        if self.valid(row=self.current.row + dr, col=self.current.col + dc):
            self.current.row += dr
            self.current.col += dc
            return True
        return False

    def rotate(self, direction):
        new_rot = self.current.rotation + direction
        # Try basic wall kicks: in place, then nudged left/right.
        for kick in (0, -1, 1, -2, 2):
            if self.valid(rotation=new_rot, col=self.current.col + kick):
                self.current.rotation = new_rot % len(SHAPES[self.current.kind])
                self.current.col += kick
                return

    def soft_drop(self):
        if not self.move(1, 0):
            self.lock()

    def hard_drop(self):
        while self.move(1, 0):
            self.score += 2
        self.lock()

    def hold_piece(self):
        if self.hold_used:
            return
        if self.hold is None:
            self.hold = self.current.kind
            self.spawn_next()
        else:
            self.hold, self.current = self.current.kind, Piece(self.hold)
        self.hold_used = True

    def ghost_row(self):
        """Row where the current piece would land (for the ghost preview)."""
        r = self.current.row
        while self.valid(row=r + 1):
            r += 1
        return r

    def gravity_interval(self):
        """Milliseconds between automatic drops, faster at higher levels."""
        return max(80, 800 - (self.level - 1) * 70)


# ----------------------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------------------
def draw_cell(surface, row, col, color, ghost=False):
    x, y = col * CELL, row * CELL
    rect = pygame.Rect(x, y, CELL, CELL)
    if ghost:
        pygame.draw.rect(surface, color, rect, 2)
    else:
        pygame.draw.rect(surface, color, rect)
        # Subtle bevel highlight for a bit of depth.
        light = tuple(min(255, c + 40) for c in color)
        pygame.draw.rect(surface, light, rect, 2)


def draw_mini(surface, kind, ox, oy):
    """Draw a small preview of a piece at pixel offset (ox, oy)."""
    cells = SHAPES[kind][0]
    for r, c in cells:
        rect = pygame.Rect(ox + c * (CELL - 6), oy + r * (CELL - 6),
                           CELL - 8, CELL - 8)
        pygame.draw.rect(surface, COLORS[kind], rect)


def render(screen, game, font, big):
    screen.fill(BLACK)

    # Grid lines.
    for r in range(ROWS + 1):
        pygame.draw.line(screen, GRID, (0, r * CELL), (COLS * CELL, r * CELL))
    for c in range(COLS + 1):
        pygame.draw.line(screen, GRID, (c * CELL, 0), (c * CELL, HEIGHT))

    # Settled blocks.
    for r in range(ROWS):
        for c in range(COLS):
            kind = game.board[r][c]
            if kind:
                draw_cell(screen, r, c, COLORS[kind])

    if not game.game_over:
        # Ghost piece.
        gr = game.ghost_row()
        delta = gr - game.current.row
        for r, c in game.current.cells():
            draw_cell(screen, r + delta, c, COLORS[game.current.kind], ghost=True)
        # Active piece.
        for r, c in game.current.cells():
            if r >= 0:
                draw_cell(screen, r, c, COLORS[game.current.kind])

    # Sidebar.
    panel_x = COLS * CELL + 20
    screen.blit(big.render("TETRIS", True, WHITE), (panel_x, 15))

    screen.blit(font.render("SCORE", True, GREY), (panel_x, 70))
    screen.blit(font.render(str(game.score), True, WHITE), (panel_x, 92))

    screen.blit(font.render("LINES", True, GREY), (panel_x, 130))
    screen.blit(font.render(str(game.lines), True, WHITE), (panel_x, 152))

    screen.blit(font.render("LEVEL", True, GREY), (panel_x, 190))
    screen.blit(font.render(str(game.level), True, WHITE), (panel_x, 212))

    screen.blit(font.render("NEXT", True, GREY), (panel_x, 255))
    draw_mini(screen, game.next_piece.kind, panel_x, 280)

    screen.blit(font.render("HOLD", True, GREY), (panel_x, 345))
    if game.hold:
        draw_mini(screen, game.hold, panel_x, 370)

    if game.paused:
        overlay_text(screen, big, font, "PAUSED", "Press P to resume")
    if game.game_over:
        overlay_text(screen, big, font, "GAME OVER", "Press R to restart")

    pygame.display.flip()


def overlay_text(screen, big, font, title, subtitle):
    overlay = pygame.Surface((COLS * CELL, HEIGHT))
    overlay.set_alpha(200)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    t = big.render(title, True, WHITE)
    s = font.render(subtitle, True, GREY)
    screen.blit(t, t.get_rect(center=(COLS * CELL // 2, HEIGHT // 2 - 20)))
    screen.blit(s, s.get_rect(center=(COLS * CELL // 2, HEIGHT // 2 + 20)))


# ----------------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------------
def main():
    pygame.init()
    pygame.display.set_caption("Tetris")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 22)
    big = pygame.font.SysFont("consolas", 34, bold=True)

    game = Tetris()
    drop_timer = 0

    while True:
        dt = clock.tick(FPS)
        if not game.paused and not game.game_over:
            drop_timer += dt
            if drop_timer >= game.gravity_interval():
                drop_timer = 0
                game.soft_drop()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type != pygame.KEYDOWN:
                continue
            key = event.key

            if key in (pygame.K_ESCAPE, pygame.K_q):
                pygame.quit()
                sys.exit()
            if key == pygame.K_r and game.game_over:
                game = Tetris()
                drop_timer = 0
                continue
            if key == pygame.K_p:
                game.paused = not game.paused
                continue
            if game.paused or game.game_over:
                continue

            if key == pygame.K_LEFT:
                game.move(0, -1)
            elif key == pygame.K_RIGHT:
                game.move(0, 1)
            elif key == pygame.K_DOWN:
                game.soft_drop()
                drop_timer = 0
            elif key in (pygame.K_UP, pygame.K_x):
                game.rotate(1)
            elif key == pygame.K_z:
                game.rotate(-1)
            elif key == pygame.K_SPACE:
                game.hard_drop()
                drop_timer = 0
            elif key == pygame.K_c:
                game.hold_piece()

        render(screen, game, font, big)


if __name__ == "__main__":
    main()
