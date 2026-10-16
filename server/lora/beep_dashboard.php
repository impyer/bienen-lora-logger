<?php
// SPDX-License-Identifier: GPL-3.0-or-later
// Geschützte BEEP-Stockansicht: nutzt die Daten des GEMEINSAMEN LoRa-Eingangs.
declare(strict_types=1);
require __DIR__ . '/lora_verarbeitung.php';
require_once __DIR__ . '/beep_base.php';
$cfg = le_cfg_laden();
if (!$cfg) { http_response_code(503); exit('LoRa-Konfiguration fehlt'); }
$hash = isset($cfg['dashboard_passwort_hash']) ? $cfg['dashboard_passwort_hash'] : '';
if (!is_string($hash) || strlen($hash) < 40) { http_response_code(503); exit('Dashboard-Passwort nicht eingerichtet'); }
if (session_status() !== PHP_SESSION_ACTIVE) {
    session_set_cookie_params(array('lifetime'=>0, 'path'=>'/', 'secure'=>!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off',
        'httponly'=>true, 'samesite'=>'Strict'));
    ini_set('session.use_strict_mode', '1');
    session_start();
}
header('Cache-Control: no-store, max-age=0');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: DENY');
header('Referrer-Policy: no-referrer');
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['logout'])) {
    $_SESSION = array();
    session_destroy();
    header('Location: beep_dashboard.php');
    exit;
}
$fehler = false;
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['passwort'])) {
    if (password_verify((string)$_POST['passwort'], $hash)) {
        session_regenerate_id(true);
        $_SESSION['beep_dashboard'] = true;
        header('Location: beep_dashboard.php');
        exit;
    }
    $fehler = true;
}
$logged = !empty($_SESSION['beep_dashboard']);
if (isset($_GET['api'])) {
    if (!$logged) { http_response_code(401); exit; }
    header('Content-Type: application/json; charset=utf-8');
    $devices = array();
    foreach ((array)($cfg['beep_geraete'] ?? array()) as $device => $meta) {
        if (empty($meta['dev_eui']) || !preg_match('/^[0-9a-f]{16}$/i', (string)$meta['dev_eui'])) continue;
        $devices[] = array(
            'device' => $device,
            'name' => isset($meta['name']) ? (string)$meta['name'] : $device,
            'volk' => isset($meta['volk']) ? (string)$meta['volk'] : 'Nicht zugeordnet',
            'stand' => isset($meta['stand']) ? (string)$meta['stand'] : '',
            'rows' => bb_zeilen($cfg, $meta['dev_eui'], 9000),
        );
    }
    echo json_encode(array('devices' => $devices, 'refreshed' => gmdate('c')), JSON_UNESCAPED_UNICODE | JSON_INVALID_UTF8_SUBSTITUTE);
    exit;
}
function bb_h($s) { return htmlspecialchars((string)$s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'); }
?><!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bienenlogger – Völkerübersicht</title>
<style>
:root{color-scheme:light;--ink:#253d36;--muted:#698079;--line:#dfe7df;--cream:#f5f8f4;--accent:#347b5b;--honey:#ba832e}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--cream);color:var(--ink)}
header{padding:20px max(18px,calc((100vw - 1200px)/2));background:white;border-bottom:1px solid var(--line)}
.top{display:flex;align-items:center;justify-content:space-between;gap:15px;flex-wrap:wrap}
.logo{font-weight:800;font-size:19px;letter-spacing:-.5px}.logo span{color:var(--accent)}.tag{font-size:12px;color:var(--muted)}
main{max-width:1200px;margin:27px auto;padding:0 18px 50px}h1{font-size:26px;letter-spacing:-.7px;margin:0 0 4px}h2{font-size:18px;margin:0 0 15px}p{margin:0 0 20px;color:var(--muted)}
button,select,input{font:inherit}button{border:1px solid var(--line);background:white;border-radius:9px;padding:8px 12px;color:var(--ink);cursor:pointer}
button.active{background:var(--accent);color:white;border-color:var(--accent)}button:hover{filter:brightness(.96)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:15px;margin:22px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:16px;padding:19px;box-shadow:0 4px 20px #28463108}
.card{cursor:pointer;text-align:left;width:100%;transition:border .15s,box-shadow .15s}
.card.selected{border:2px solid var(--accent);padding:18px;box-shadow:0 6px 26px #347b5b20}
.card-title{display:flex;justify-content:space-between;gap:10px;align-items:center;margin-bottom:16px}
.card-title strong{font-size:18px}.pill{border-radius:50px;background:#eef4ed;color:var(--accent);font-size:11px;padding:4px 10px}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:14px}.number{font-size:25px;font-weight:750;letter-spacing:-.5px}
.small{color:var(--muted);font-size:12px}.foot{border-top:1px solid var(--line);padding-top:10px;margin-top:17px;font-size:12px;color:var(--muted)}
.controls{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:15px}.controls button{font-size:13px}
.panels{display:grid;grid-template-columns:2fr 1fr;gap:15px}.chart{height:315px}.spectrum{height:315px}
.login{max-width:420px;margin:70px auto}.login input{display:block;width:100%;padding:13px;border-radius:10px;border:1px solid var(--line);margin:15px 0}
.login button{background:var(--accent);color:white;width:100%;padding:12px}
.empty{padding:60px 10px;text-align:center;color:var(--muted)}.warn{color:#a54b25}.footnote{font-size:12px;color:var(--muted);margin-top:14px}
@media(max-width:780px){.panels{grid-template-columns:1fr}h1{font-size:23px}main{margin:18px auto}}
</style>
<?php if ($logged): ?><script src="https://cdn.jsdelivr.net/npm/echarts@5.6.0/dist/echarts.min.js"></script><?php endif; ?>
</head><body><header><div class="top"><div><div class="logo">⬡ <span>Bienen</span>logger</div><div class="tag">Stockmessdaten · geschützte Vorschau</div></div>
<?php if ($logged): ?><form method="post"><button name="logout" value="1">Abmelden</button></form><?php endif; ?>
</div></header>
<?php if (!$logged): ?>
<main><div class="panel login"><h1>Völkerübersicht</h1><p>Mit dem lokalen Dashboard-Passwort anmelden.</p>
<form method="post"><input type="password" name="passwort" autocomplete="current-password" aria-label="Passwort" required>
<button>Ansicht öffnen</button></form><?php if ($fehler): ?><p class="warn">Passwort nicht korrekt.</p><?php endif; ?></div></main>
<?php else: ?>
<main><h1>Völkerübersicht</h1><p>Gewicht, Temperatur und akustische Frequenzbänder – direkt aus den TTN-Uplinks.</p>
<div id="cards" class="cards" aria-live="polite"><div class="panel">Messdaten werden geladen …</div></div>
<div class="panel" style="margin-bottom:15px"><div class="top"><h2 id="focus">Messverlauf</h2>
<div class="controls" id="filters"><button data-days="1" class="active">24 Stunden</button><button data-days="7">7 Tage</button><button data-days="30">30 Tage</button></div></div>
<div id="trend" class="chart"></div><div id="trendFallback" class="empty" hidden>Diagramm benötigt ECharts (Internetverbindung) und mindestens einen Messwert.</div></div>
<div class="panels"><div class="panel"><h2>Akustisches Spektrum</h2><div id="spectrum" class="spectrum"></div><div class="small">Relative FFT-Rohwerte, keine kalibrierten dB. Bandgrenzen nach BEEP-Decoder.</div></div>
<div class="panel"><h2>Letzte Übertragung</h2><div id="details" class="small">Keine Daten</div></div></div>
<div class="footnote">Nur tatsächlich empfangene Daten werden gezeigt. Kein automatisches Ergänzen fehlender Messungen. Gewicht basiert auf gerätespezifischer Kalibrierung; alle Zeitangaben in Europe/Berlin.</div></main>
<script>
let dataset = [], selected = 0, days = 1, trendChart = null, fftChart = null;
const fmt = (v,n=2)=>v==null||!Number.isFinite(Number(v))?'–':Number(v).toLocaleString('de-DE',{minimumFractionDigits:n,maximumFractionDigits:n});
const time = s=>new Date(s).toLocaleString('de-DE',{timeZone:'Europe/Berlin',day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'});
const el = id=>document.getElementById(id);
function node(tag, cls, text) {let x=document.createElement(tag); if(cls)x.className=cls; if(text!==undefined)x.textContent=text; return x;}
async function load() {
  try {
    const resp=await fetch('beep_dashboard.php?api=1',{credentials:'same-origin',cache:'no-store'});
    if(!resp.ok)throw Error('HTTP '+resp.status);
    dataset=(await resp.json()).devices||[];
    if(selected>=dataset.length)selected=0;
    render();
  } catch(e) {el('cards').replaceChildren(node('div','panel warn','Datenabruf fehlgeschlagen: '+e.message));}
}
function render() {
  let container=el('cards');container.replaceChildren();
  if(!dataset.length){container.append(node('div','panel','Keine BEEP-Geräte konfiguriert.'));return;}
  dataset.forEach((d,i)=>{
    const r=d.rows[d.rows.length-1],c=node('button','card'+(i===selected?' selected':''));c.type='button';c.onclick=()=>{selected=i;render()};
    let top=node('div','card-title');top.append(node('strong','',d.volk));top.append(node('span','pill',r?'Messungen vorhanden':'Noch keine Daten'));c.append(top);
    c.append(node('div','small',d.name+(d.stand?' · '+d.stand:'')));
    let stats=node('div','stats');
    [[r?.gewicht_kg,'kg','Gewicht',3],[r?.temperatur_c,'°C','Temperatur',2],[r?.batterie_v,'V','Batterie',2],[r?.fft_baender?.length,'','FFT-Bänder',0]].forEach(([value,unit,label,digits])=>{
      let b=node('div');b.append(node('div','small',label));b.append(node('div','number',fmt(value,digits)+(value==null?'':' '+unit)));stats.append(b);
    });
    c.append(stats);c.append(node('div','foot',r?'Stand: '+time(r.zeit_utc):'Noch kein TTN-Uplink über diesen Eingang'));container.append(c);
  });
  let d=dataset[selected];el('focus').textContent='Messverlauf · '+d.volk;
  let r=d.rows[d.rows.length-1];
  const details=el('details');details.replaceChildren();
  [['Gerät',d.name],['Letzter Uplink',r?time(r.zeit_utc):'–'],['Gewichtsrohwert',r?.gewicht_roh ?? '–'],
   ['Kalibriertes Gewicht',r?.gewicht_kg==null?'nicht verfügbar':fmt(r.gewicht_kg,3)+' kg'],
   ['Brutnesttemperatur',r?.temperatur_c==null?'–':fmt(r.temperatur_c)+' °C'],
   ['Batterie',r?.batterie_v==null?'–':fmt(r.batterie_v,3)+' V'],
   ['RSSI',r?.rssi ?? '–'],['SNR',r?.snr ?? '–'],['Frame Counter',r?.f_cnt ?? '–']].forEach(([a,b])=>{
     let line=node('div','',a+': '+b);line.style.padding='8px 0';line.style.borderBottom='1px solid var(--line)';details.append(line);
   });
  paint(d);
}
function paint(d) {
  const min=Date.now()-days*86400000;
  const rows=d.rows.filter(r=>Date.parse(r.zeit_utc)>=min).sort((a,b)=>Date.parse(a.zeit_utc)-Date.parse(b.zeit_utc));
  if(!window.echarts){el('trendFallback').hidden=false;return;}
  if(!trendChart)trendChart=echarts.init(el('trend'));
  if(!fftChart)fftChart=echarts.init(el('spectrum'));
  let series=(key,name,yAxisIndex)=>({name,type:'line',showSymbol:rows.length<30,connectNulls:false,yAxisIndex,
    data:rows.map(r=>[Date.parse(r.zeit_utc),r[key]==null?null:r[key]]),smooth:false});
  trendChart.setOption({tooltip:{trigger:'axis'},legend:{top:0},grid:{left:60,right:60,top:45,bottom:50},
    xAxis:{type:'time'},yAxis:[{type:'value',name:'kg',scale:true},{type:'value',name:'°C',scale:true}],
    dataZoom:[{type:'inside'},{type:'slider',bottom:3,height:18}],series:[series('gewicht_kg','Gewicht',0),series('temperatur_c','Temperatur',1)]},true);
  let fft=d.rows.length?d.rows[d.rows.length-1].fft_baender||[]:[];
  fftChart.setOption({tooltip:{trigger:'axis'},grid:{left:46,right:8,top:18,bottom:85},
    xAxis:{type:'category',axisLabel:{rotate:48},data:fft.map(b=>b.von_hz+'–'+b.bis_hz)},
    yAxis:{type:'value',name:'Rohwert'},series:[{type:'bar',data:fft.map(b=>b.wert),itemStyle:{color:'#ba832e'}}]},true);
}
el('filters').addEventListener('click',e=>{const b=e.target.closest('button[data-days]');if(!b)return;days=Number(b.dataset.days);
  el('filters').querySelectorAll('button').forEach(x=>x.classList.toggle('active',x===b));if(dataset[selected])paint(dataset[selected]);});
window.addEventListener('resize',()=>{trendChart?.resize();fftChart?.resize()});load();
</script>
<?php endif; ?></body></html>
