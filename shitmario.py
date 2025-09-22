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
SPEED = 200  # pixels per second
JUMP_VY = -12
GRAVITY = 3
FLY_DURATION = 2.0
DOUBLE_PRESS_WINDOW = 0.4

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
defaults = {
    "player_y": FLOOR_Y - PLAYER_SIZE[1],
    "player_vy": 0,
    "obstacle_x": W,
    "score": 0,
    "game_over": False,
    "fly_until": 0.0,
    "last_jump_time": 0.0,
    "last_time": time.time()
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ---------------- UI ----------------
col1, col2 = st.columns([1,3])
with col1:
    restart_pressed = st.button("🔄 Restart")
with col2:
    st.markdown("**Controls:** Single ⬆️ = jump. Double ⬆️ quickly = fly 2s. Double ⬆️ again cancels fly.")

if restart_pressed:
    for key, val in defaults.items():
        st.session_state[key] = val

jump_pressed = st.button("⬆️ Jump")
now = time.time()
if jump_pressed and not st.session_state.game_over:
    delta = now - st.session_state.last_jump_time
    if delta <= DOUBLE_PRESS_WINDOW:
        if now < st.session_state.fly_until:
            st.session_state.fly_until = 0.0  # cancel flying
        else:
            st.session_state.fly_until = now + FLY_DURATION  # start flying
    else:
        on_ground = st.session_state.player_y >= FLOOR_Y - PLAYER_SIZE[1] - 1
        if on_ground and now >= st.session_state.fly_until:
            st.session_state.player_vy = JUMP_VY
    st.session_state.last_jump_time = now

# ---------------- TIME DELTA ----------------
current_time = time.time()
dt = current_time - st.session_state.last_time
st.session_state.last_time = current_time

# ---------------- GAME LOGIC ----------------
if not st.session_state.game_over:
    # Flying or normal
    if current_time < st.session_state.fly_until:
        st.session_state.player_y = 120
        st.session_state.player_vy = 0
    else:
        st.session_state.player_y += st.session_state.player_vy
        st.session_state.player_vy += GRAVITY
        if st.session_state.player_y >= FLOOR_Y - PLAYER_SIZE[1]:
            st.session_state.player_y = FLOOR_Y - PLAYER_SIZE[1]
            st.session_state.player_vy = 0

    # Move obstacle
    st.session_state.obstacle_x -= SPEED * dt
    if st.session_state.obstacle_x < -OBSTACLE_SIZE[0]:
        st.session_state.obstacle_x = W + random.randint(0,200)
        st.session_state.score += 1

    # Collision
    player_rect = Rect(80, st.session_state.player_y, *PLAYER_SIZE)
    obstacle_rect = Rect(st.session_state.obstacle_x, FLOOR_Y - OBSTACLE_SIZE[1], *OBSTACLE_SIZE)
    if player_rect.intersects(obstacle_rect):
        st.session_state.game_over = True

# ---------------- DRAW ----------------
canvas = st.empty()
img = Image.new("RGBA", (W,H), (200,230,255))
d = ImageDraw.Draw(img)
d.rectangle((0,FLOOR_Y,W,H), fill=(87,59,37))
player_rect = Rect(80, st.session_state.player_y, *PLAYER_SIZE)
d.rectangle(player_rect.as_tuple(), fill=(235,64,52))
obstacle_rect = Rect(st.session_state.obstacle_x, FLOOR_Y - OBSTACLE_SIZE[1], *OBSTACLE_SIZE)
d.rectangle(obstacle_rect.as_tuple(), fill=(40,40,40))
d.text((12,12), f"Score: {st.session_state.score}", fill=(255,255,255))
canvas.image(img, use_container_width=True)

# ---------------- HUD ----------------
if st.session_state.fly_until > current_time:
    remaining = max(0, st.session_state.fly_until - current_time)
    st.info(f"🕊️ Flying — {remaining:.1f}s left (double press again to cancel)")
elif st.session_state.game_over:
    st.error("💀 Game Over! Press 🔄 Restart.")
else:
    st.caption("Press ⬆️ once = jump, double = fly 2s, double again cancels")
