import streamlit as st
from dataclasses import dataclass
from PIL import Image, ImageDraw
import time

# --- Config ---
W, H = 800, 300
FLOOR_Y = 250
PLAYER_SIZE = (30, 40)
OBSTACLE_SIZE = (30, 40)
SPEED = -25   # obstacle speed
FLY_DURATION = 2  # seconds

@dataclass
class Rect:
    x: int
    y: int
    w: int
    h: int
    def as_tuple(self):
        return (self.x, self.y, self.x + self.w, self.y + self.h)
    def intersects(self, other: "Rect") -> bool:
        return not (
            self.x + self.w <= other.x
            or self.x >= other.x + other.w
            or self.y + self.h <= other.y
            or self.y >= other.y + other.h
        )

# --- Restart button ---
if st.button("🔄 Restart"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- Initialize ---
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
    st.session_state.fly_until = 0
if "last_jump_time" not in st.session_state:
    st.session_state.last_jump_time = 0

# --- Controls ---
if st.button("⬆️ Jump") and not st.session_state.game_over:
    now = time.time()
    # Detect double press (within 0.4s)
    if now - st.session_state.last_jump_time < 0.4:
        if now < st.session_state.fly_until:
            # If already flying → cancel fly immediately
            st.session_state.fly_until = 0
        else:
            # Start flying
            st.session_state.fly_until = now + FLY_DURATION
    else:
        # Normal jump if on ground
        if st.session_state.player_y == FLOOR_Y - PLAYER_SIZE[1]:
            st.session_state.player_vy = -12
    st.session_state.last_jump_time = now

# --- Game Loop ---
if not st.session_state.game_over:
    now = time.time()

    if now < st.session_state.fly_until:
        # Flying mode → float at a fixed height
        st.session_state.player_y = 100
        st.session_state.player_vy = 0
    else:
        # Normal physics
        st.session_state.player_y += st.session_state.player_vy
        st.session_state.player_vy += 2   # gravity
        if st.session_state.player_y >= FLOOR_Y - PLAYER_SIZE[1]:
            st.session_state.player_y = FLOOR_Y - PLAYER_SIZE[1]
            st.session_state.player_vy = 0

    # Obstacle movement
    st.session_state.obstacle_x += SPEED
    if st.session_state.obstacle_x < -OBSTACLE_SIZE[0]:
        st.session_state.obstacle_x = W
        st.session_state.score += 1

    # Collision
    player_rect = Rect(80, st.session_state.player_y, *PLAYER_SIZE)
    obstacle_rect = Rect(st.session_state.obstacle_x, FLOOR_Y - OBSTACLE_SIZE[1], *OBSTACLE_SIZE)
    if player_rect.intersects(obstacle_rect):
        st.session_state.game_over = True

# --- Draw ---
img = Image.new("RGBA", (W, H), (200, 230, 255))
d = ImageDraw.Draw(img)

# Ground
d.rectangle((0, FLOOR_Y, W, H), fill=(87, 59, 37))

# Player
player_rect = Rect(80, st.session_state.player_y, *PLAYER_SIZE)
d.rectangle(player_rect.as_tuple(), fill=(235, 64, 52))

# Obstacle
obstacle_rect = Rect(st.session_state.obstacle_x, FLOOR_Y - OBSTACLE_SIZE[1], *OBSTACLE_SIZE)
d.rectangle(obstacle_rect.as_tuple(), fill=(50, 50, 50))

st.image(img, use_container_width=True)

# HUD
st.markdown(f"**Score:** {st.session_state.score}")

if st.session_state.game_over:
    st.error("💀 Game Over! Press 🔄 Restart.")
elif st.session_state.fly_until > time.time():
    st.info("🕊️ Flying mode active! (Press ⬆️ twice again to cancel)")
else:
    st.caption("Press ⬆️ once to jump, twice quickly to fly for 2s.")

# --- Refresh ---
if not st.session_state.game_over:
    time.sleep(0.03)
    st.rerun()
