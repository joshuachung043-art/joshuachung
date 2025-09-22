# app.py
import streamlit as st
from dataclasses import dataclass
from PIL import Image, ImageDraw
import time
import random

# ---------------- CONFIG ----------------
W, H = 900, 360
FLOOR_Y = 280
PLAYER_SIZE = (36, 44)
OBSTACLE_SIZE = (36, 44)
SPEED = -30
JUMP_VY = -12
GRAVITY = 3
FLY_DURATION = 2.0
DOUBLE_PRESS_WINDOW = 0.4
FRAME_SLEEP = 0.03

# ---------------- DATACLASS ----------------
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

# ---------------- SESSION STATE ----------------
for key, value in [
    ("player_y", FLOOR_Y - PLAYER_SIZE[1]),
    ("player_vy", 0),
    ("obstacle_x", W),
    ("score", 0),
    ("game_over", False),
    ("fly_until", 0.0),
    ("last_jump_time", 0.0)
]:
    if key not in st.session_state:
        st.session_state[key] = value

# ---------------- UI ----------------
col1, col2 = st.columns([1, 3])
with col1:
    restart_pressed = st.button("🔄 Restart")
with col2:
    st.markdown("**Controls:** Single ⬆️ = jump. Double ⬆️ quickly = fly for 2s. Double ⬆️ again while flying = cancel fly.")

if restart_pressed:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()

jump_pressed = st.button("⬆️ Jump")
now = time.time()
if jump_pressed and not st.session_state.game_over:
    delta = now - st.session_state.last_jump_time
    if delta <= DOUBLE_PRESS_WINDOW:
        if now < st.session_state.fly_until:
            st.session_state.fly_until = 0.0
        else:
            st.session_state.fly_until = now + FLY_DURATION
    else:
        on_ground = st.session_state.player_y >= FLOOR_Y - PLAYER_SIZE[1] - 1
        if on_ground and now >= st.session_state.fly_until:
            st.session_state.player_vy = JUMP_VY
    st.session_state.last_jump_time = now

# ---------------- GAME LOOP ----------------
canvas = st.empty()  # placeholder for drawing

# Only animate if game is running
while True:
    if st.session_state.game_over:
        break

    now = time.time()
    # Flying or normal
    if now < st.session_state.fly_until:
        st.session_state.player_y = 120
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

    # Draw
    img = Image.new("RGBA", (W, H), (200, 230, 255))
    d = ImageDraw.Draw(img)
    d.rectangle((0, FLOOR_Y, W, H), fill=(87, 59, 37))  # ground
    d.rectangle(player_rect.as_tuple(), fill=(235, 64, 52))
    d.rectangle(obstacle_rect.as_tuple(), fill=(40, 40, 40))
    d.text((12, 12), f"Score: {st.session_state.score}", fill=(255, 255, 255))
    canvas.image(img, use_container_width=True)

    # HUD
    if st.session_state.fly_until > now:
        remaining = max(0, st.session_state.fly_until - now)
        st.info(f"🕊️ Flying — {remaining:.1f}s left (double press again to cancel)")
    elif st.session_state.game_over:
        st.error("💀 Game Over! Press 🔄 Restart.")
    else:
        st.caption("Press ⬆️ once = jump, double = fly for 2s")

    time.sleep(FRAME_SLEEP)
