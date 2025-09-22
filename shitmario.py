# app.py
# Streamlit Dino-like runner with double-press-to-fly toggle
# Save as app.py and run: streamlit run app.py

import time
from dataclasses import dataclass
from PIL import Image, ImageDraw
import streamlit as st

# ---------------- Config ----------------
W, H = 900, 360
FLOOR_Y = 280
PLAYER_SIZE = (36, 44)
OBSTACLE_SIZE = (36, 44)

# Gameplay tuning (feel free to tweak)
SPEED = -30            # obstacle speed (negative = moves left)
JUMP_VY = -12          # initial upward velocity for a normal jump (short jump)
GRAVITY = 3            # gravity applied each frame (stronger => shorter jump)
FLY_DURATION = 2.0     # seconds of flying on double-press
DOUBLE_PRESS_WINDOW = 0.40  # seconds in which two presses count as a double press
FRAME_SLEEP = 0.03     # seconds per frame (≈33 FPS)

# ---------------- Helpers / Dataclasses ----------------
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
# Ensure all necessary session_state keys exist (safe across re-runs)
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

# ---------------- Controls (top bar) ----------------
col1, col2 = st.columns([1, 3])
with col1:
    if st.button("🔄 Restart"):
        # Clear the session state and restart
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()  # safe call to restart the script

with col2:
    st.markdown("**Controls:** Press the **Jump (⬆️)** button. Double-press quickly to toggle flying for 2s (double-press again while flying cancels it).")

# Jump button: handle single / double press logic
jump_pressed = st.button("⬆️ Jump")
if jump_pressed and not st.session_state.game_over:
    now = time.time()
    delta = now - st.session_state.last_jump_time

    # Double-press inside the window -> toggle fly
    if delta <= DOUBLE_PRESS_WINDOW:
        if now < st.session_state.fly_until:
            # Already flying -> cancel immediately
            st.session_state.fly_until = 0.0
        else:
            # Start flying for FLY_DURATION seconds
            st.session_state.fly_until = now + FLY_DURATION
    else:
        # Single press: normal jump only if on ground and not currently flying
        on_ground = st.session_state.player_y >= (FLOOR_Y - PLAYER_SIZE[1]) - 1
        if on_ground and time.time() >= st.session_state.fly_until:
            st.session_state.player_vy = JUMP_VY

    st.session_state.last_jump_time = now

# ---------------- Game update ----------------
if not st.session_state.game_over:
    now = time.time()
    # Flying active?
    if now < st.session_state.fly_until:
        # Hover at a fixed fly height (keeps consistent behavior)
        FLY_HEIGHT = 120
        st.session_state.player_y = FLY_HEIGHT
        st.session_state.player_vy = 0
    else:
        # Normal physics: apply vertical velocity + gravity
        st.session_state.player_y += st.session_state.player_vy
        st.session_state.player_vy += GRAVITY
        # Clamp to floor
        if st.session_state.player_y >= FLOOR_Y - PLAYER_SIZE[1]:
            st.session_state.player_y = FLOOR_Y - PLAYER_SIZE[1]
            st.session_state.player_vy = 0

    # Move obstacle continuously
    st.session_state.obstacle_x += SPEED
    if st.session_state.obstacle_x < -OBSTACLE_SIZE[0]:
        # Respawn offscreen to the right; add a small random offset to avoid perfect repetition
        import random
        st.session_state.obstacle_x = W + random.randint(0, 200)
        st.session_state.score += 1

    # Collision check (player vs obstacle)
    player_rect = Rect(80, st.session_state.player_y, *PLAYER_SIZE)
    obstacle_rect = Rect(st.session_state.obstacle_x, FLOOR_Y - OBSTACLE_SIZE[1], *OBSTACLE_SIZE)
    if player_rect.intersects(obstacle_rect):
        st.session_state.game_over = True

# ---------------- Rendering ----------------
img = Image.new("RGBA", (W, H), (200, 230, 255))
draw = ImageDraw.Draw(img)

# Draw ground
draw.rectangle((0, FLOOR_Y, W, H), fill=(87, 59, 37))

# Draw player
draw.rectangle(player_rect.as_tuple(), fill=(235, 64, 52))
# little cap/highlight
draw.rectangle((player_rect.x, player_rect.y - 6, player_rect.x + player_rect.w, player_rect.y + 6), fill=(250, 230, 230))

# Draw obstacle
draw.rectangle(obstacle_rect.as_tuple(), fill=(40, 40, 40))

# HUD
draw.rectangle((0, 0, W, 36), fill=(0, 0, 0, 140))
draw.text((12, 8), f"Score: {st.session_state.score}", fill=(255, 255, 255))

st.image(img, use_container_width=True)

# Status text
if st.session_state.game_over:
    st.error("💀 Game Over! Press 🔄 Restart.")
else:
    if time.time() < st.session_state.fly_until:
        remaining = max(0.0, st.session_state.fly_until - time.time())
        st.info(f"🕊️ Flying — {remaining:.1f}s remaining  (Double-press again to cancel)")
    else:
        st.caption("Single press = short jump. Double-press quickly = fly for 2s (double-press again to cancel).")

# ---------------- Frame refresh / loop ----------------
# When the game is running, sleep a frame and rerun to animate.
if not st.session_state.game_over:
    time.sleep(FRAME_SLEEP)
    # Use st.rerun if available (modern Streamlit); otherwise fallback to experimental_rerun
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        # fallback for older Streamlit versions
        st.experimental_rerun()
