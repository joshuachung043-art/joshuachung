"""
Streamlit Super-Mario-like mini game (fixed key controls)
Run with: streamlit run streamlit_mario.py
"""
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Mini Mario (Streamlit)", layout='wide')
st.title("迷你瑪利歐 — 可在 Streamlit 遊玩的平台遊戲 (HTML5 Canvas)")
st.markdown("按 ← → 移動，空白鍵跳躍。收集金幣到達旗子過關！")

# Embedded HTML + JS game
html = r'''
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    html,body { margin:0; padding:0; background:#87CEEB; }
    canvas { display:block; margin:0 auto; background: linear-gradient(#87CEEB, #A0D8F1); }
    #wrapper { text-align:center; }
  </style>
</head>
<body>
  <div id="wrapper">
    <canvas id="game" width="960" height="540"></canvas>
  </div>
<script>
// Simple platformer: player, platforms, coins, enemy, goal
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const W = canvas.width, H = canvas.height;

let keys = {};
window.addEventListener('keydown', e=>{ keys[e.code]=true; });
window.addEventListener('keyup', e=>{ keys[e.code]=false; });

// Camera / world
let cameraX = 0;

// Player
let player = {
  x:50, y:380, w:28, h:40,
  vx:0, vy:0, speed:2.4, jumpPower:9, onGround:false,
  color:'#e74c3c'
};

const gravity = 0.3;

// Level layout (platforms as x,y,w,h)
let platforms = [
  {x:0,y:440,w:2000,h:100},
  {x:250,y:360,w:160,h:20},
  {x:460,y:300,w:140,h:20},
  {x:700,y:240,w:120,h:20},
  {x:920,y:330,w:160,h:20},
  {x:1200,y:380,w:100,h:20},
  {x:1400,y:320,w:160,h:20},
  {x:1700,y:360,w:220,h:20}
];

// Coins
let coins = [
  {x:280,y:320,collected:false},
  {x:500,y:260,collected:false},
  {x:740,y:200,collected:false},
  {x:980,y:290,collected:false},
  {x:1420,y:280,collected:false}
];
let score = 0;

// Enemy simple
let enemy = {x:1100,y:400,w:32,h:28,dir:1,speed:1.2};

// Goal (flag)
let goal = {x:1850,y:340,w:20,h:100};
let gameState = 'playing'; // 'playing', 'won', 'dead'

function rectsOverlap(a,b){
  return !(a.x+a.w < b.x || a.x > b.x+b.w || a.y+a.h < b.y || a.y > b.y+b.h);
}

function update(){
  if(gameState!=='playing') return;
  // input
  if(keys['ArrowLeft']||keys['KeyA']) player.vx = -player.speed;
  else if(keys['ArrowRight']||keys['KeyD']) player.vx = player.speed;
  else player.vx = 0;
  if((keys['Space']||keys['ArrowUp']||keys['KeyW']) && player.onGround){ player.vy = -player.jumpPower; player.onGround=false; }

  // physics
  player.vy += gravity;
  player.x += player.vx;
  player.y += player.vy;

  // collisions with platforms
  player.onGround = false;
  for(let p of platforms){
    let pp = {x:p.x, y:p.y, w:p.w, h:p.h};
    let pl = {x:player.x, y:player.y, w:player.w, h:player.h};
    if(rectsOverlap(pl,pp)){
      let px = (player.x + player.w/2) - (p.x + p.w/2);
      let py = (player.y + player.h/2) - (p.y + p.h/2);
      let overlapX = (player.w/2 + p.w/2) - Math.abs(px);
      let overlapY = (player.h/2 + p.h/2) - Math.abs(py);
      if(overlapX < overlapY){
        if(px>0) player.x += overlapX; else player.x -= overlapX;
        player.vx = 0;
      } else {
        if(py>0){ player.y += overlapY; player.vy = 0; }
        else { player.y -= overlapY; player.vy = 0; player.onGround = true; }
      }
    }
  }

  // enemy movement
  enemy.x += enemy.dir * enemy.speed;
  if(enemy.x < 1060) enemy.dir = 1;
  if(enemy.x > 1260) enemy.dir = -1;

  // camera follow
  cameraX = player.x - 200;
  if(cameraX < 0) cameraX = 0;

  // coin collection
  for(let c of coins){
    if(!c.collected){
      let coinBox = {x:c.x-8, y:c.y-8, w:16, h:16};
      let pl = {x:player.x, y:player.y, w:player.w, h:player.h};
      if(rectsOverlap(coinBox,pl)){
        c.collected = true; score += 1;
      }
    }
  }

  // enemy collision -> die
  if(rectsOverlap({x:enemy.x,y:enemy.y,w:enemy.w,h:enemy.h}, {x:player.x,y:player.y,w:player.w,h:player.h})){
    if(player.vy > 1){ enemy.dead = true; player.vy = -6; }
    else { gameState = 'dead'; }
  }

  // win if reach goal
  if(player.x > goal.x){ gameState = 'won'; }
}

function draw(){
  ctx.clearRect(0,0,W,H);

  ctx.fillStyle='#8BC34A';
  for(let i=0;i<6;i++){
    let hx = (i*400 - cameraX*0.2)%2000 - 100;
    ctx.beginPath(); ctx.ellipse(hx,430,150,60,0,0,2*Math.PI); ctx.fill();
  }

  for(let p of platforms){
    ctx.fillStyle='#654321';
    ctx.fillRect(p.x - cameraX, p.y, p.w, p.h);
    ctx.fillStyle='#2ecc71';
    ctx.fillRect(p.x - cameraX, p.y-6, Math.min(p.w,50), 6);
  }

  for(let c of coins){
    if(!c.collected){
      ctx.fillStyle='#f1c40f';
      ctx.beginPath(); ctx.arc(c.x - cameraX, c.y, 8, 0, Math.PI*2); ctx.fill();
      ctx.strokeStyle='rgba(0,0,0,0.2)'; ctx.stroke();
    }
  }

  if(!enemy.dead){
    ctx.fillStyle='#2c3e50';
    ctx.fillRect(enemy.x - cameraX, enemy.y, enemy.w, enemy.h);
  } else {
    ctx.fillStyle='rgba(44,62,80,0.6)';
    ctx.fillRect(enemy.x - cameraX, enemy.y+10, enemy.w, 6);
  }

  ctx.fillStyle='#333'; ctx.fillRect(goal.x - cameraX, goal.y, 6, goal.h);
  ctx.fillStyle='#e74c3c'; ctx.beginPath(); ctx.moveTo(goal.x+6 - cameraX, goal.y+10); ctx.lineTo(goal.x+36 - cameraX, goal.y+24); ctx.lineTo(goal.x+6 - cameraX, goal.y+36); ctx.closePath(); ctx.fill();

  ctx.fillStyle = player.color;
  ctx.fillRect(player.x - cameraX, player.y, player.w, player.h);
  ctx.fillStyle = '#fff'; ctx.fillRect(player.x - cameraX +6, player.y+8,6,6); ctx.fillStyle='#000'; ctx.fillRect(player.x - cameraX +8, player.y+10,2,2);

  ctx.fillStyle = 'rgba(0,0,0,0.6)'; ctx.fillRect(10,10,140,36);
  ctx.fillStyle = '#fff'; ctx.font='16px Arial'; ctx.fillText('金幣: '+score, 18,32);

  if(gameState==='won'){
    ctx.fillStyle='rgba(0,0,0,0.6)'; ctx.fillRect(W/2-160,H/2-40,320,80);
    ctx.fillStyle='#fff'; ctx.font='28px Arial'; ctx.fillText('你贏了！恭喜過關 🎉', W/2-130, H/2);
  }
  if(gameState==='dead'){
    ctx.fillStyle='rgba(0,0,0,0.6)'; ctx.fillRect(W/2-160,H/2-40,320,80);
    ctx.fillStyle='#fff'; ctx.font='28px Arial'; ctx.fillText('你死了，按 R 重新開始', W/2-160, H/2);
  }
}

function reset(){
  player.x=50; player.y=380; player.vx=0; player.vy=0; score=0; cameraX=0; gameState='playing';
  for(let c of coins) c.collected=false; enemy.dead=false; enemy.x=1100; enemy.dir=1;
}

window.addEventListener('keydown', e=>{
  if(e.code==='KeyR'){ reset(); }
});

function loop(){ update(); draw(); requestAnimationFrame(loop); }
loop();
</script>
</body>
</html>
'''

components.html(html, height=600, scrolling=False)

st.markdown('---')
col1, col2 = st.columns(2)
with col1:
    st.header('控制')
    st.write('← → 移動，空白鍵或上鍵跳，R 重置遊戲。')
with col2:
    st.header('說明')
    st.write('這是個極簡版的平台遊戲示範。若要加入：')
    st.write('- 真正的像素角色圖、音效、更多關卡')
    st.write('- 敵人 AI、碰撞優化、手機支援')

st.info('這個版本已移除 preventDefault，鍵盤輸入更容易生效。記得要先點一下遊戲畫面再操作。')
