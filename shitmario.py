# Streamlit Mini Platformer (Mario‑like)
# Save this as `app.py` and run with: streamlit run app.py

import math
import random
from dataclasses import dataclass
from typing import List, Tuple

import streamlit as st
from PIL import Image, ImageDraw

# --- App Config ---
st.set_page_config(page_title="Mini Platformer", layout="wide")

# --- Constants ---
W, H = 900, 540  # canvas size
FLOOR_Y = 470
GRAVITY = 0.9
MOVE_ACCEL = 1.4
MAX_SPEED = 7
FRICTION = 0.8
JUMP_VEL = 18
TICK_MS = 70  # ~14 FPS on cloud reliably
PLAYER_SIZE = (28, 34)
ENEMY_SIZE = (26, 24)
COIN_R = 8

# Colors
SKY = (135, 206, 235)
GROUND = (87, 59, 37)
PLATFORM = (120, 120, 180)
PLAYER_COL = (235, 64, 52)
PLAYER_CAP = (250, 230, 230)
ENEMY_COL = (153, 102, 51)
COIN_COL = (246, 197, 74)
FLAG_COL = (50, 200, 50)
TEXT_BG = (0, 0, 0, 110)

# --- Data Classes ---
@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float

    def as_tuple(self):
        return (self.x, self.y, self.x + self.w, self.y + self.h)

    def intersects(self, other: "Rect") -> bool:
        return not (
            self.x + self.w <= other.x
            or self.x >= other.x + other.w
            or self.y + self.h <= other.y
            or self.y >= other.y + other.h
        )

    def move_ip(self, dx: float, dy: float):
        self.x += dx
        self.y += dy


@dataclass
class Player:
    rect: Rect
    vx: float = 0.0
    vy: float = 0.0
    on_ground: bool = False
    facing: int = 1  # 1 right, -1 left


@dataclass
class Enemy:
    rect: Rect
    left: float
    right: float
    vx: float = 1.6
    alive: bool = True


# --- Level Layout ---
# Platforms (x, y, w, h)
PLATFORMS: List[Rect] = [
    Rect(0, FLOOR_Y, W, H - FLOOR_Y),  # ground
    Rect(110, 410, 120, 16),
    Rect(280, 360, 120, 16),
    Rect(460, 320, 120, 16),
    Rect(620, 280, 120, 16),
    Rect(740, 230, 110, 16),
    Rect(390, 450, 80, 16),
]

COINS: List[Tuple[int, int]] = [
    (170, 380), (220, 380),
    (320, 330), (370, 330),
    (500, 290), (550, 290),
    (660, 250), (710, 250),
    (780, 200)
]

ENEMIES_START: List[Enemy] = [
    Enemy(Rect(320, FLOOR_Y - ENEMY_SIZE[1], *ENEMY_SIZE), 300, 450, vx=1.4, alive=True),
    Enemy(Rect(620, FLOOR_Y - ENEMY_SIZE[1], *ENEMY_SIZE), 600, 760, vx=1.6, alive=True),
]

FLAG = Rect(W - 60, FLOOR_Y - 120, 14, 120)

# --- Helpers ---

def init_state():
    st.session_state.player = Player(rect=Rect(40, FLOOR_Y - PLAYER_SIZE[1], *PLAYER_SIZE))
    # Deep copy enemies
    st.session_state.enemies = [Enemy(Rect(e.rect.x, e.rect.y, e.rect.w, e.rect.h), e.left, e.right, e.vx, True) for e in ENEMIES_START]
    st.session_state.score = 0
    st.session_state.lives = 3
    st.session_state.win = False
    st.session_state.game_over = False
    st.session_state.collected = set()  # coin indexes
    st.session_state.ticks = 0
    st.session_state.paused = False


def reset_level(hard=False):
    if hard or 'player' not in st.session_state:
        init_state()
        return
    p = st.session_state.player
    p.rect.x, p.rect.y = 40, FLOOR_Y - PLAYER_SIZE[1]
    p.vx = p.vy = 0
    p.on_ground = False
    st.session_state.enemies = [Enemy(Rect(e.rect.x, e.rect.y, e.rect.w, e.rect.h), e.left, e.right, e.vx, True) for e in ENEMIES_START]
    st.session_state.win = False
    st.session_state.game_over = False


# Collision resolution with platforms

def horiz_collide(r: Rect, dx: float, solids: List[Rect]):
    r.x += dx
    for s in solids:
        if r.intersects(s):
            if dx > 0:
                r.x = s.x - r.w
            elif dx < 0:
                r.x = s.x + s.w
            return True
    return False


def vert_collide(r: Rect, dy: float, solids: List[Rect]):
    r.y += dy
    for s in solids:
        if r.intersects(s):
            if dy > 0:
                r.y = s.y - r.h
            elif dy < 0:
                r.y = s.y + s.h
            return True
    return False


# --- Rendering ---

def draw_scene():
    img = Image.new("RGBA", (W, H), SKY)
    d = ImageDraw.Draw(img)

    # Ground & platforms
    for plat in PLATFORMS:
        color = GROUND if plat is PLATFORMS[0] else PLATFORM
        d.rectangle(plat.as_tuple(), fill=color)

    # Flag pole
    d.rectangle(FLAG.as_tuple(), fill=FLAG_COL)
    d.polygon([(FLAG.x + FLAG.w, FLAG.y + 10), (FLAG.x + FLAG.w + 30, FLAG.y + 20), (FLAG.x + FLAG.w, FLAG.y + 30)], fill=FLAG_COL)

    # Coins
    for i, (cx, cy) in enumerate(COINS):
        if i in st.session_state.collected:
            continue
        d.ellipse((cx - COIN_R, cy - COIN_R, cx + COIN_R, cy + COIN_R), fill=COIN_COL)

    # Enemies
    for e in st.session_state.enemies:
        if not e.alive:
            continue
        d.rectangle(e.rect.as_tuple(), fill=ENEMY_COL)

    # Player (simple body + cap)
    p = st.session_state.player
    d.rectangle(p.rect.as_tuple(), fill=PLAYER_COL)
    # cap
    cap_h = 10
    d.rectangle((p.rect.x, p.rect.y - 4, p.rect.x + p.rect.w, p.rect.y + cap_h), fill=PLAYER_CAP)

    # HUD
    hud = Image.new("RGBA", (W, 40), (0, 0, 0, 0))
    dh = ImageDraw.Draw(hud)
    dh.rectangle((0, 0, W, 40), fill=TEXT_BG)
    text = f"Score: {st.session_state.score}   Lives: {st.session_state.lives}   Coins: {len(st.session_state.collected)}/{len(COINS)}"
    dh.text((12, 10), text, fill=(255, 255, 255))
    img.alpha_composite(hud, (0, 0))

    return img


# --- Game Step ---

def game_step(left: bool, right: bool, jump_once: bool):
    if st.session_state.paused or st.session_state.game_over or st.session_state.win:
        return

    p = st.session_state.player

    # Horizontal movement
    ax = 0
    if left:
        ax -= MOVE_ACCEL
        p.facing = -1
    if right:
        ax += MOVE_ACCEL
        p.facing = 1

    p.vx += ax

    # Clamp speed
    if p.vx > MAX_SPEED:
        p.vx = MAX_SPEED
    if p.vx < -MAX_SPEED:
        p.vx = -MAX_SPEED

    # Friction when no input
    if ax == 0:
        p.vx *= FRICTION
        if abs(p.vx) < 0.05:
            p.vx = 0

    # Jump
    if jump_once and p.on_ground:
        p.vy = -JUMP_VEL
        p.on_ground = False

    # Gravity
    p.vy += GRAVITY

    # Horizontal collide
    collided_x = horiz_collide(p.rect, p.vx, PLATFORMS)
    if collided_x:
        p.vx = 0

    # Vertical collide
    collided_y = vert_collide(p.rect, p.vy, PLATFORMS)
    if collided_y:
        if p.vy > 0:
            p.on_ground = True
        p.vy = 0
    else:
        p.on_ground = False

    # World bounds
    if p.rect.x < 0:
        p.rect.x = 0
        p.vx = 0
    if p.rect.x + p.rect.w > W:
        p.rect.x = W - p.rect.w
        p.vx = 0
    if p.rect.y > H + 200:
        lose_life()
        return

    # Coins
    for i, (cx, cy) in enumerate(COINS):
        if i in st.session_state.collected:
            continue
        if Rect(cx - COIN_R, cy - COIN_R, COIN_R * 2, COIN_R * 2).intersects(p.rect):
            st.session_state.collected.add(i)
            st.session_state.score += 10

    # Enemies
    for e in st.session_state.enemies:
        if not e.alive:
            continue
        # Patrol
        e.rect.x += e.vx
        if e.rect.x < e.left:
            e.rect.x = e.left
            e.vx = abs(e.vx)
        if e.rect.x + e.rect.w > e.right:
            e.rect.x = e.right - e.rect.w
            e.vx = -abs(e.vx)

        # Player interaction
        if p.rect.intersects(e.rect):
            # If player is falling onto enemy -> stomp
            if p.vy > 0 and p.rect.y + p.rect.h - e.rect.y < 14:
                e.alive = False
                p.vy = -JUMP_VEL * 0.7
                st.session_state.score += 50
            else:
                lose_life()
                return

    # Win condition
    if p.rect.intersects(FLAG):
        st.session_state.win = True
        st.session_state.score += 100

    st.session_state.ticks += 1


def lose_life():
    st.session_state.lives -= 1
    if st.session_state.lives <= 0:
        st.session_state.game_over = True
    reset_level(hard=False)


# --- UI Controls (Streamlit) ---
if 'player' not in st.session_state:
    init_state()

# Top bar
c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 2])
with c1:
    if st.button("⟲ Reset Level"):
        reset_level(hard=False)
with c2:
    if st.button("↺ New Game"):
        init_state()
with c3:
    st.session_state.paused = st.toggle("⏸ Pause", value=st.session_state.get('paused', False))
with c4:
    st.write("")
with c5:
    st.caption("Tip: toggle Left/Right and tap Jump. The game auto-refreshes.")

# Control panel
lc, rc, jc = st.columns(3)
with lc:
    st.session_state['hold_left'] = st.toggle("⬅️ Left", value=st.session_state.get('hold_left', False))
with rc:
    st.session_state['hold_right'] = st.toggle("➡️ Right", value=st.session_state.get('hold_right', False))
with jc:
    jump_now = st.button("⤴️ Jump", use_container_width=True)

# Consume jump as one-shot flag
if jump_now:
    st.session_state['jump_once'] = True
else:
    st.session_state['jump_once'] = False

# Run one step then render
game_step(st.session_state.get('hold_left', False), st.session_state.get('hold_right', False), st.session_state.get('jump_once', False))
img = draw_scene()
st.image(img, caption=("You Win! 🎉" if st.session_state.win else ("Game Over 💀" if st.session_state.game_over else "")), use_column_width=True)

# Auto-refresh to animate (disable when paused)
if not st.session_state.paused and not (st.session_state.win or st.session_state.game_over):
    st.experimental_rerun = st.experimental_rerun  # quiet linters
    st_autorefresh = st.experimental_memo or None  # placeholder to avoid import confusion
    st.autorefresh(interval=TICK_MS, key="tick")

# Footer
st.markdown("""
**How to play**  
- Toggle **Left/Right** to walk.  
- Tap **Jump** to hop; stomp enemies by landing on them.  
- Collect all coins and reach the green flag to finish.  

**Notes**  
- Streamlit doesn't do true realtime keyboard input, so controls are toggle buttons.  
- Everything is in one file. No extra assets required (uses Pillow to draw each frame).  
""")
