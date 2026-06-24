#pragma once
// Mobile control page, served from flash. Relative fetch() calls so it works
// at whatever IP the SoftAP hands out (default 192.168.4.1).
const char INDEX_HTML[] PROGMEM = R"HTML(<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>Gripper Control</title>
<style>
  :root { --bg:#0e1116; --card:#1a1f29; --fg:#e8edf4; --muted:#7d8794;
          --open:#2ecc71; --close:#e74c3c; --accent:#3d7bff; }
  * { box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
  html,body { margin:0; height:100%; background:var(--bg); color:var(--fg);
              font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif; }
  .wrap { max-width:520px; margin:0 auto; padding:18px 16px 40px; }
  h1 { font-size:20px; font-weight:600; margin:6px 0 2px; }
  .sub { color:var(--muted); font-size:13px; margin-bottom:16px; }
  .btns { display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:18px; }
  button { border:0; border-radius:16px; color:#fff; font-size:22px; font-weight:700;
           padding:34px 0; touch-action:manipulation; cursor:pointer; transition:filter .1s, transform .05s; }
  button:active { transform:scale(.97); filter:brightness(1.15); }
  .open  { background:var(--open); }
  .close { background:var(--close); }
  .card { background:var(--card); border-radius:14px; padding:16px; margin-bottom:14px; }
  .row { display:flex; justify-content:space-between; align-items:center; gap:10px; margin:8px 0; }
  .row .k { color:var(--muted); font-size:14px; }
  .row .v { font-variant-numeric:tabular-nums; font-size:16px; font-weight:600; }
  .dot { width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:7px;
         background:var(--close); vertical-align:middle; }
  .dot.on { background:var(--open); }
  input[type=range] { width:100%; accent-color:var(--accent); height:34px; }
  .mini { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
  .mini button { font-size:14px; font-weight:600; padding:13px 0; background:#2a3140; }
  .toggle { display:flex; align-items:center; gap:10px; }
  .switch { position:relative; width:52px; height:30px; background:#39414f; border-radius:30px; transition:.2s; }
  .switch.on { background:var(--accent); }
  .switch i { position:absolute; top:3px; left:3px; width:24px; height:24px; background:#fff;
              border-radius:50%; transition:.2s; }
  .switch.on i { left:25px; }
  .foot { color:var(--muted); font-size:12px; text-align:center; margin-top:18px; line-height:1.6; }
  .pos-label { color:var(--muted); font-size:13px; display:flex; justify-content:space-between; }
</style>
</head>
<body>
<div class="wrap">
  <h1>Gripper Control</h1>
  <div class="sub">Feetech STS bus servo &middot; <span id="net">192.168.4.1</span></div>

  <div class="btns">
    <button class="open"  onpointerdown="act('open')">OPEN</button>
    <button class="close" onpointerdown="act('close')">CLOSE</button>
  </div>

  <div class="card">
    <div class="row"><span class="k"><span id="dot" class="dot"></span>Status</span>
        <span class="v" id="state">connecting…</span></div>
    <div class="row"><span class="k">Position</span><span class="v" id="pos">–</span></div>
    <div class="row"><span class="k">Load</span><span class="v" id="load">–</span></div>
    <div class="row"><span class="k">Voltage</span><span class="v" id="volt">–</span></div>
    <div class="row"><span class="k">Temp</span><span class="v" id="temp">–</span></div>
  </div>

  <div class="card">
    <div class="toggle row">
      <span class="k">Torque</span>
      <div id="tq" class="switch" onclick="toggleTorque()"><i></i></div>
    </div>
    <div class="pos-label"><span>Manual position</span><span id="manval">2048</span></div>
    <input type="range" id="slider" min="0" max="4095" value="2048"
           oninput="manval.textContent=this.value" onchange="goto(this.value)">
    <div class="mini">
      <button onclick="calib('open')">Set current as OPEN</button>
      <button onclick="calib('close')">Set current as CLOSE</button>
    </div>
  </div>

  <div class="foot">
    Wi-Fi <b>Gripper</b> &middot; pass <b>gripper1234</b><br>
    Offline appliance &middot; no internet by design
  </div>
</div>

<script>
const $ = id => document.getElementById(id);
let torqueOn = false;

async function post(path){
  try { const r = await fetch(path, {method:'POST'}); return await r.json(); }
  catch (e) { return {error:String(e)}; }
}
function act(which){ post('/api/'+which); flash(which); }
function goto(v){ post('/api/goto?pos='+v); }
function calib(which){ post('/api/calibrate?which='+which).then(refresh); }
function toggleTorque(){ torqueOn=!torqueOn; post('/api/torque?on='+(torqueOn?1:0)); paintTorque(); }
function paintTorque(){ $('tq').classList.toggle('on', torqueOn); }
function flash(which){
  const b=document.querySelector('.'+which); b.style.filter='brightness(1.4)';
  setTimeout(()=>b.style.filter='',150);
}

async function refresh(){
  let s; try { s = await (await fetch('/api/status')).json(); } catch(e){ s=null; }
  if(!s){ $('state').textContent='no server'; return; }
  const ok = s.connected;
  $('dot').classList.toggle('on', ok);
  $('state').textContent = ok ? 'connected' : 'servo not found';
  $('pos').textContent  = s.position!=null ? s.position : '–';
  $('load').textContent = s.load!=null ? s.load : '–';
  $('volt').textContent = s.voltage ? s.voltage.toFixed(1)+' V' : '–';
  $('temp').textContent = s.temp!=null ? s.temp+' °C' : '–';
  if(ok && s.position!=null && document.activeElement!==$('slider')){
    $('slider').value = s.position; $('manval').textContent = s.position;
  }
}
setInterval(refresh, 600);
refresh();
</script>
</body>
</html>)HTML";
