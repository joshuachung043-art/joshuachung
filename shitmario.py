# app.py
# Streamlit Dino-like runner with double-press-to-fly toggle
# Save as app.py and run: streamlit run app.py

import time
from dataclasses import dataclass
from PIL import Image, ImageDraw
import streamlit as st
import random

# ---------------- Config ----------------
W, H = 900, 360
FLOOR_Y = 280
PLAYER_SIZE = (36, 44)
OBSTACLE_SIZE = (36, 44)

# Gameplay tuning
SPEED = -30            # obstacle speed
JUMP_VY = -12          # jump strength
GRAVITY = 3            # gravity
FLY_DURATION = 2.0     # seconds of flying
DOUBLE_PRESS_WINDOW = 0.40  # seconds for double press detection
FRAME_SLEEP = 0.03     # seconds per frame (~33 FPS)

# ---------------- Helpers ----------------
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

# ---------------- Session-state init ----------------
if "player_y" not in st.session_state:
    st.session_state.player_y = FLOOR_Y - PLAYER_SIZE[1]
if "player_vy" not in st.session_state:
    st.session_state.player_vy = 0
if "obstacle_x" not in st.session_state:
    st.session_state.obstacle_x = W
if "score" not in st.session_state:
    st.session_state.score = 0
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "fly_until" not in st.session_state:
    st.session_state.fly_until = 0.0
if "last_jump_time" not in st.session_state:
    st.session_state.last_jump_time = 0.0

# ---------------- Controls ----------------
col1, col2 = st.columns([1, 3])
with col1:
    if st.button("🔄 Restart"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()  # modern rerun call

with col2:
    st.markdown("**Controls:** Single ⬆️ = jump. Double ⬆️ quickly = fly for 2s. Double ⬆️ again while flying = cancel fly.")

jump_pressed = st.button("⬆️ Jump")
if jump_pressed and not st.session_state.game_over:
    now = time.time()
    delta = now - st.session_state.last_jump_time

    # Double-press logic
    if delta <= DOUBLE_PRESS_WINDOW:
        if now < st.session_state.fly_until:
            st.session_state.fly_until = 0.0  # cancel flying
        else:
            st.session_state.fly_until = now + FLY_DURATION  # start flying
    else:
        # Normal jump (only from ground, and not while flying)
        on_ground = st.session_state.player_y >= (FLOOR_Y - PLAYER_SIZE[1]) - 1
        if on_ground and now >= st.session_state.fly_until:
            st.session_state.player_vy = JUMP_VY

    st.session_state.last_jump_time = now

# ---------------- Game update ----------------
if not st.session_state.game_over:
    now = time.time()

    if now < st.session_state.fly_until:
        st.session_state.player_y = 120  # flying height
        st.session_state.player_vy = 0
    else:
        st.session_state.player_y += st.session_state.player_vy
        st.session_state.player_vy += GRAVITY
        if st.session_state.player_y >= FLOOR_Y - PLAYER_SIZE[1]:
            st.session_state.player_y = FLOOR_Y - PLAYER_SIZE[1]
            st.session_state.player_vy = 0

    # Move obstacle
    st.session_state.obstacle_x += SPEED
    if st.session_state.obstacle_x < -OBSTACLE_SIZE[0]:
        st.session_state.obstacle_x = W + random.randint(0, 200)
        st.session_state.score += 1

    # Collision
    player_rect = Rect(80, st.session_state.player_y, *PLAYER_SIZE)
    obstacle_rect = Rect(st.session_state.obstacle_x, FLOOR_Y - OBSTACLE_SIZE[1], *OBSTACLE_SIZE)
    if player_rect.intersects(obstacle_rect):
        st.session_state.game_over = True

# ---------------- Rendering ----------------
img = Image.new("RGBA", (W, H), (200, 230, 255))
draw = ImageDraw.Draw(img)

draw.rectangle((0, FLOOR_Y, W, H), fill=(87, 59, 37))  # ground
player_rect = Rect(80, st.session_state.player_y, *PLAYER_SIZE)
draw.rectangle(player_rect.as_tuple(), fill=(235, 64, 52))  # player
obstacle_rect = Rect(st.session_state.obstacle_x, FLOOR_Y - OBSTACLE_SIZE[1], *OBSTACLE_SIZE)
draw.rectangle(obstacle_rect.as_tuple(), fill=(40, 40, 40))  # obstacle

st.image(img, use_container_width=True)

st.markdown(f"**Score:** {st.session_state.score}")

if st.session_state.game_over:
    st.error("💀 Game Over! Press 🔄 Restart.")
elif st.session_state.fly_until > time.time():
    remaining = max(0.0, st.session_state.fly_until - time.time())
    st.info(f"🕊️ Flying — {remaining:.1f}s left (Double-press again to cancel)")
else:
    st.caption("Press ⬆️ once to jump. Press twice quickly to fly for 2s.")

# ---------------- Frame refresh ----------------
if not st.session_state.game_over:
    time.sleep(FRAME_SLEEP)
    st.rerun()
