/*  Перемена — сервер для игры по локальной сети.
 *  Запуск:  node server.js  [порт]
 *  Зависимостей нет: раздаёт index.html и держит WebSocket-комнату,
 *  в которой все бегут один и тот же набор уровней наперегонки.
 */
"use strict";
var http = require("http");
var fs = require("fs");
var os = require("os");
var path = require("path");
var crypto = require("crypto");

var PORT = parseInt(process.argv[2] || process.env.PORT || "8080", 10);
var ROOT = __dirname;
var GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11";
var MIME = { ".html":"text/html; charset=utf-8", ".js":"text/javascript; charset=utf-8",
             ".css":"text/css; charset=utf-8", ".md":"text/markdown; charset=utf-8" };

/* ---------------- раздача файлов ---------------- */
var server = http.createServer(function(req, res){
  var url = decodeURIComponent((req.url || "/").split("?")[0]);
  if(url === "/") url = "/index.html";
  var file = path.join(ROOT, path.normalize(url).replace(/^(\.\.[\/\\])+/, ""));
  if(file.indexOf(ROOT) !== 0){ res.writeHead(403); res.end("нельзя"); return; }
  fs.readFile(file, function(err, data){
    if(err){ res.writeHead(404, {"Content-Type":"text/plain; charset=utf-8"}); res.end("не найдено"); return; }
    res.writeHead(200, { "Content-Type": MIME[path.extname(file)] || "application/octet-stream",
                         "Cache-Control": "no-cache" });
    res.end(data);
  });
});

/* ---------------- минимальный WebSocket ---------------- */
function frame(payload, opcode){
  var body = Buffer.isBuffer(payload) ? payload : Buffer.from(String(payload), "utf8");
  var len = body.length, head;
  if(len < 126){ head = Buffer.alloc(2); head[1] = len; }
  else if(len < 65536){ head = Buffer.alloc(4); head[1] = 126; head.writeUInt16BE(len, 2); }
  else { head = Buffer.alloc(10); head[1] = 127; head.writeBigUInt64BE(BigInt(len), 2); }
  head[0] = 0x80 | (opcode || 0x1);
  return Buffer.concat([head, body]);
}
function send(sock, obj){
  if(!sock || sock.destroyed) return;
  try{ sock.write(frame(JSON.stringify(obj), 0x1)); }catch(e){}
}

server.on("upgrade", function(req, sock){
  var key = req.headers["sec-websocket-key"];
  if(!key){ sock.destroy(); return; }
  var accept = crypto.createHash("sha1").update(key + GUID).digest("base64");
  sock.write("HTTP/1.1 101 Switching Protocols\r\n" +
             "Upgrade: websocket\r\nConnection: Upgrade\r\n" +
             "Sec-WebSocket-Accept: " + accept + "\r\n\r\n");
  sock.setNoDelay(true);
  attach(sock);
});

function attach(sock){
  var buf = Buffer.alloc(0);
  var player = addPlayer(sock);
  sock.on("data", function(chunk){
    buf = Buffer.concat([buf, chunk]);
    for(;;){
      if(buf.length < 2) return;
      var op = buf[0] & 0x0f, masked = buf[1] & 0x80;
      var len = buf[1] & 0x7f, off = 2;
      if(len === 126){ if(buf.length < 4) return; len = buf.readUInt16BE(2); off = 4; }
      else if(len === 127){ if(buf.length < 10) return; len = Number(buf.readBigUInt64BE(2)); off = 10; }
      var mask = null;
      if(masked){ if(buf.length < off + 4) return; mask = buf.slice(off, off + 4); off += 4; }
      if(buf.length < off + len) return;
      var body = Buffer.from(buf.slice(off, off + len));
      if(mask) for(var i=0;i<body.length;i++) body[i] ^= mask[i % 4];
      buf = buf.slice(off + len);
      if(op === 0x8){ sock.end(); return; }
      if(op === 0x9){ try{ sock.write(frame(body, 0xA)); }catch(e){} continue; }
      if(op !== 0x1 && op !== 0x0) continue;
      var msg = null;
      try{ msg = JSON.parse(body.toString("utf8")); }catch(e){}
      if(msg) onMessage(player, msg);
    }
  });
  sock.on("error", function(){ dropPlayer(player); });
  sock.on("close", function(){ dropPlayer(player); });
}

/* ---------------- комната ---------------- */
var players = [];          // порядок = порядок подключения, первый — ведущий
var nextId = 1;
var race = null;           // {seed, src, mode, startedAt, finished:[]}
var setup = { mode:"normal", src:"classic", seed:"" };   // что выбрал ведущий
var COLORS = ["#3aa0e8","#e8663a","#4fc27a","#b06fe0","#e8c23a","#e83a95","#3ad6e8","#9ae83a"];

function addPlayer(sock){
  var p = { id: nextId++, sock: sock, name: "", ready: false,
            level: 0, coins: 0, done: false, alive: true };
  players.push(p);
  return p;
}
function dropPlayer(p){
  if(!p || !p.alive) return;
  p.alive = false;
  var i = players.indexOf(p);
  if(i >= 0) players.splice(i, 1);
  broadcast({ t:"left", id:p.id });
  sendRoom();
  log(p.name ? p.name + " отключился" : "игрок отключился");
}
function hostId(){ return players.length ? players[0].id : 0; }
function colorOf(p){ return COLORS[(players.indexOf(p) + p.id) % COLORS.length]; }
function roomList(){
  return players.map(function(p){
    return { id:p.id, name:p.name || ("Игрок " + p.id), ready:p.ready, color:colorOf(p),
             level:p.level, coins:p.coins, done:p.done };
  });
}
function broadcast(obj, exceptId){
  for(var i=0;i<players.length;i++)
    if(players[i].id !== exceptId) send(players[i].sock, obj);
}
function sendRoom(){
  broadcast({ t:"room", host:hostId(), players:roomList(), setup:setup,
              race: race ? { seed:race.seed, src:race.src, mode:race.mode } : null });
}

function onMessage(p, m){
  if(!p.alive) return;
  if(m.t === "hello"){
    p.name = String(m.name || "").slice(0, 14) || ("Игрок " + p.id);
    send(p.sock, { t:"welcome", id:p.id, host:hostId(), color:colorOf(p), setup:setup,
                   players:roomList(), race: race ? { seed:race.seed, src:race.src, mode:race.mode } : null });
    sendRoom();
    log(p.name + " вошёл (" + players.length + " в комнате)");
  }
  else if(m.t === "ready"){ p.ready = !!m.v; sendRoom(); }
  else if(m.t === "setup"){
    if(p.id !== hostId()) return;                       // настройки задаёт ведущий
    setup = { mode: m.mode === "hard" ? "hard" : "normal",
              src: m.src === "classic" ? "classic" : "seed",
              seed: String(m.seed || "").slice(0,8) };
    sendRoom();
  }
  else if(m.t === "start"){
    if(p.id !== hostId()) return;                       // старт даёт только ведущий
    race = { seed: String(m.seed || "").slice(0,8), src: m.src === "classic" ? "classic" : "seed",
             mode: m.mode === "hard" ? "hard" : "normal", startedAt: Date.now(), finished: [] };
    players.forEach(function(q){ q.level = 0; q.coins = 0; q.done = false; q.ready = false; });
    broadcast({ t:"start", seed:race.seed, src:race.src, mode:race.mode });
    sendRoom();
    log("забег начался: " + race.mode + ", " + (race.src === "seed" ? "сид " + race.seed : "классика"));
  }
  else if(m.t === "pos"){
    m.id = p.id; m.color = colorOf(p); m.name = p.name;
    broadcast(m, p.id);                                  // позиции просто пересылаем
  }
  else if(m.t === "progress"){
    p.level = m.level | 0; p.coins = m.coins | 0;
  }
  else if(m.t === "finish"){
    if(!race || p.done) return;
    p.done = true;
    race.finished.push({ id:p.id, name:p.name, time:m.time, coins:m.coins, deaths:m.deaths|0 });
    broadcast({ t:"results", list:race.finished, players:roomList() });
    log(p.name + " финишировал: " + m.time + " сек, пирожков " + m.coins);
  }
  else if(m.t === "lost"){                               // выбыл (хардкор)
    p.done = true;
    broadcast({ t:"lost", id:p.id, name:p.name });
    sendRoom();
  }
}

/* сводка по комнате раз в полсекунды — чтобы не слать на каждое движение */
setInterval(function(){
  if(players.length) broadcast({ t:"board", players:roomList(), setup:setup });
}, 500);

/* ---------------- запуск ---------------- */
function log(s){ console.log("[" + new Date().toLocaleTimeString("ru-RU") + "] " + s); }
function addresses(){
  var out = [], nets = os.networkInterfaces();
  Object.keys(nets).forEach(function(name){
    (nets[name] || []).forEach(function(net){
      if(net.family === "IPv4" && !net.internal) out.push(net.address);
    });
  });
  return out;
}
server.listen(PORT, function(){
  console.log("\n  Перемена — сервер запущен\n");
  console.log("  на этом компьютере:  http://localhost:" + PORT);
  addresses().forEach(function(ip){ console.log("  в локальной сети:    http://" + ip + ":" + PORT); });
  console.log("\n  Открой адрес на всех устройствах в одной сети, нажми «ПО СЕТИ»,");
  console.log("  первый вошедший — ведущий, он и запускает забег.\n");
});
