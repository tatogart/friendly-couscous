# -*- coding: utf-8 -*-
"""Собирает index_tv.html из index.html.

Движок тот же, меняется только оболочка: пульт вместо мыши, отступы под
overscan телевизора и фокус, который ходит по кнопкам. Поэтому телевизорная
версия не копируется руками, а пересобирается одной командой:

    python3 tools/make_tv.py

После правок в index.html прогони скрипт заново, иначе версии разъедутся.
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "index.html")
DST = os.path.join(ROOT, "index_tv.html")

subs = []


def rep(old, new, count=1):
    subs.append((old, new, count))


# ---------------------------------------------------------------- заголовок
rep(u"<title>Перемена — 15 минут свободы</title>",
    u"<title>Перемена — версия для телевизора</title>")

# ------------------------------------------------- оболочка под телевизор
rep(u"""  #wrap{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;padding:8px}""",
    u"""  /* Телевизор режет края картинки (overscan), поэтому отступаем от рамки. */
  #wrap{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;
    padding:3.5vh 4vw;background:#05080f}
  canvas{cursor:none}
  #pad,#rotate{display:none !important}""")

# --------------------------------------------- подсказка управления в меню
rep(u"""    text(isTouch ? "слева бежать · справа прыжок и предмет"
                 : "← →  бежать · ПРОБЕЛ прыжок · E предмет · F весь экран · P пауза",
         VW/2, 382, 10.5, "rgba(200,220,255,.5)", "center", 600);""",
    u"""    text("стрелки — выбор · OK — нажать · Назад — вернуться · в забеге ◀ ▶ бег, OK прыжок",
         VW/2, 382, 10.5, "rgba(200,220,255,.5)", "center", 600);""")

rep(u"""  name: "Звонок!", hint: "\u2190 \u2192 бежать   ПРОБЕЛ прыгать   R заново",""",
    u"""  name: "Звонок!", hint: "\u25c0 \u25b6 бежать   OK прыгать   Назад — пауза",""")

rep(u"""  text("вибрация и кнопки — для телефона", 716, 384, 11, "rgba(200,220,255,.4)", "right", 600);""",
    u"""  text("на телевизоре лучше «быстро»", 716, 384, 11, "rgba(200,220,255,.4)", "right", 600);""")

# Слабому телевизору честнее сразу отдать быстрый режим, а не «авто».
rep(u"""function freshSet(){
  return { vol:2, buzz:1, shake:2, hints:1, gfx:0, padSize:1, lefty:0, tapJump:0 };
}""",
    u"""function freshSet(){        // на телевизоре по умолчанию «быстро»: чип слабый
  return { vol:2, buzz:0, shake:2, hints:1, gfx:2, padSize:1, lefty:0, tapJump:0 };
}""")

# ---------------------------------------------- картинка на весь экран
rep(u"""function render(){
  var dpr = Math.min(2, window.devicePixelRatio || 1);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);""",
    u"""function render(){
  var dpr = cv.width / VW;              // масштаб задаёт tvResize, а не браузер
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);""")

# ------------------------------------------------------------- слой пульта
TV_LAYER = u'''
/* ================== ПУЛЬТ И ТЕЛЕВИЗОР ==================
   Движок остался прежним, поменялся только ввод: мыши на диване нет,
   поэтому по кнопкам ходит фокус, а нажимает его OK.
   Кнопки игра и так пересобирает каждый кадр в G.buttons — фокус просто
   выбирает из этого списка, так что новый экран работает сам собой. */
var TV = { id:null, hold:0, dir:0, padSeen:false, was:{} };

function tvUi(){                          // экраны, где стрелки — это выбор, а не бег
  var s = G.state;
  return s !== "play" && s !== "clear" && s !== "lesson" && s !== "hub";
}
/* «secret» — невидимая зона на заголовке для входа в панель разработчика.
   Мышь по ней попадает случайно, а фокус вставать не должен: рамка повисла бы
   в пустоте. На телевизоре в панель заходят с геймпада: Start четыре раза. */
var TV_SKIP = { secret:1 };

/* Панель рисуется поверх меню или холла, и кнопки фона остаются в списке —
   мышь их не достаёт (панель сверху), а фокус бы цеплялся, и рамка повисала
   посреди чужого текста. Запоминаем, с какого места в списке начинается
   верхний экран, и ниже не спускаемся. */
var tvBase = 0;
function tvTop(base){
  return function(){ tvBase = G.buttons.length; return base.apply(null, arguments); };
}
function tvOk(b, i){
  return b && !TV_SKIP[b.id] && (i === undefined || i >= tvBase);
}
function tvRect(id){
  for(var i=G.buttons.length-1;i>=0;i--)
    if(G.buttons[i].id === id) return tvOk(G.buttons[i], i) ? G.buttons[i] : null;
  return null;
}
var TV_FIRST = ["play","resume","again","seed_ok","chest","claim_day","back"];
function tvPick(){                        // на что встать, если фокуса ещё нет
  var i, b, best = null;
  for(i=0;i<TV_FIRST.length;i++){ b = tvRect(TV_FIRST[i]); if(b) return b.id; }
  for(i=0;i<G.buttons.length;i++){
    b = G.buttons[i];
    if(!tvOk(b, i)) continue;
    if(!best || (b.y*2 + b.x) < (best.y*2 + best.x)) best = b;
  }
  return best ? best.id : null;
}
function tvMove(dx, dy){
  /* Считаем не по центрам, а по зазору между краями: соседом становится тот,
     кто лежит по ходу стрелки и перекрывается с текущей кнопкой поперёк.
     Без этого фокус срывается по диагонали в соседний ряд. */
  var cur = tvRect(TV.id);
  if(!cur){ TV.id = tvPick(); return; }
  var i, b, a0, a1, b0, b1, ov, along, sc;
  var best = null, bestSc = 1e9, wrap = null, wrapSc = -1;
  for(i=0;i<G.buttons.length;i++){
    b = G.buttons[i];
    if(b.id === TV.id || !tvOk(b, i)) continue;
    if(dx){
      along = (dx > 0) ? (b.x - (cur.x + cur.w)) : (cur.x - (b.x + b.w));
      a0 = cur.y; a1 = cur.y + cur.h; b0 = b.y; b1 = b.y + b.h;
    } else {
      along = (dy > 0) ? (b.y - (cur.y + cur.h)) : (cur.y - (b.y + b.h));
      a0 = cur.x; a1 = cur.x + cur.w; b0 = b.x; b1 = b.x + b.w;
    }
    ov = Math.min(a1, b1) - Math.max(a0, b0);    // перекрытие поперёк хода
    if(along >= -2){
      sc = Math.max(0, along) + (ov > 0 ? 0 : (-ov)*3 + 400);
      if(sc < bestSc){ bestSc = sc; best = b; }
    } else if(ov > 0 && -along > wrapSc){        // упёрлись в край — прыгаем на другой конец
      wrapSc = -along; wrap = b;
    }
  }
  b = best || wrap;
  if(b && b.id !== TV.id){ TV.id = b.id; sfx.key(); }
}
function tvPress(){
  var b = tvRect(TV.id);
  actx();
  if(b){ doButton(b.id); return; }
  uiAction();
}
function tvBack(){
  actx();
  if(G.state === "play"){ G.state = "paused"; sfx.key(); return; }
  if(tvRect("back")){ doButton("back"); return; }
  if(G.state === "paused"){ G.state = "play"; return; }
  if(G.state === "win" || G.state === "over"){ doButton("menu"); return; }
}

/* Фокус подсвечивается дважды: рамкой и обычным наведением самой игры —
   для этого курсор просто ставится в центр выбранной кнопки. */
function tvSync(){
  if(!tvUi()){ TV.id = null; G.mx = -999; G.my = -999; return; }
  if(!tvRect(TV.id)) TV.id = tvPick();
  var b = tvRect(TV.id);
  if(!b){ G.mx = -999; G.my = -999; return; }
  G.mx = b.x + b.w/2; G.my = b.y + b.h/2;
}
function tvRing(){
  var b = tvRect(TV.id);
  if(!b) return;
  var k = 1 + 0.025*Math.sin(G.tick*0.14), pad = 7;
  ctx.save();
  ctx.translate(b.x + b.w/2, b.y + b.h/2);
  ctx.scale(k, k);
  ctx.translate(-(b.x + b.w/2), -(b.y + b.h/2));
  ctx.strokeStyle = "rgba(255,209,102,.95)";
  ctx.lineWidth = 3.2;
  ctx.shadowColor = "rgba(255,209,102,.75)";
  ctx.shadowBlur = 16;
  rrect(b.x - pad, b.y - pad, b.w + pad*2, b.h + pad*2, 15);
  ctx.stroke();
  ctx.restore();
}

/* ---------------- кнопки пульта ----------------
   У телевизоров свои коды «Назад»: 8 — обычный, 461 — LG, 10009 — Samsung. */
function tvIsBack(e){
  var k = e.keyCode || 0;
  if(k === 27 || k === 461 || k === 10009 || k === 166) return true;
  if(e.key === "GoBack" || e.key === "BrowserBack") return true;
  if(k === 8) return G.state !== "seedin" && G.state !== "code";   // там это «стереть»
  return false;
}
document.addEventListener("keydown", function(e){
  var k = e.keyCode || 0, code = e.code;
  if(tvIsBack(e)){ e.preventDefault(); e.stopPropagation(); tvBack(); return; }
  if(!tvUi()) return;                      // в забеге стрелки остаются бегом
  if(code === "ArrowLeft"  || k === 37){ e.preventDefault(); e.stopPropagation(); tvMove(-1, 0); return; }
  if(code === "ArrowRight" || k === 39){ e.preventDefault(); e.stopPropagation(); tvMove( 1, 0); return; }
  if(code === "ArrowUp"    || k === 38){ e.preventDefault(); e.stopPropagation(); tvMove( 0,-1); return; }
  if(code === "ArrowDown"  || k === 40){ e.preventDefault(); e.stopPropagation(); tvMove( 0, 1); return; }
  if(code === "Enter" || code === "NumpadEnter" || k === 13 || code === "Space" || k === 32){
    e.preventDefault(); e.stopPropagation();
    if(!e.repeat) tvPress();
    return;
  }
}, true);

/* ---------------- геймпад ----------------
   Многие приставки и телевизоры отдают пульт как геймпад. */
function tvHit(g, i){                     // нажали именно сейчас, а не держат
  var b = g.buttons[i];
  var now = !!(b && (b.pressed || b.value > 0.5)), key = g.index + ":" + i;
  var hit = now && !TV.was[key];
  TV.was[key] = now;
  return hit;
}
function tvHeld(g, i){
  var b = g.buttons[i];
  return !!(b && (b.pressed || b.value > 0.5));
}
function tvPads(){
  if(!navigator.getGamepads) return;
  var list, i, g, ax, ay, dir;
  try{ list = navigator.getGamepads(); }catch(e){ return; }
  for(i=0;i<list.length;i++){
    g = list[i];
    if(!g || !g.connected) continue;
    TV.padSeen = true;
    ax = (g.axes && g.axes.length > 0) ? g.axes[0] : 0;
    ay = (g.axes && g.axes.length > 1) ? g.axes[1] : 0;
    if(tvHeld(g, 14)) ax = -1; else if(tvHeld(g, 15)) ax = 1;
    if(tvHeld(g, 12)) ay = -1; else if(tvHeld(g, 13)) ay = 1;

    if(tvUi()){
      dir = 0;
      if(ax < -0.55) dir = 1; else if(ax > 0.55) dir = 2;
      else if(ay < -0.55) dir = 3; else if(ay > 0.55) dir = 4;
      if(!dir){ TV.dir = 0; TV.hold = 0; }
      else if(dir !== TV.dir || --TV.hold <= 0){
        TV.hold = (dir === TV.dir) ? 9 : 22;     // первый шаг, дальше автоповтор
        TV.dir = dir;
        tvMove(dir === 1 ? -1 : dir === 2 ? 1 : 0, dir === 3 ? -1 : dir === 4 ? 1 : 0);
      }
      if(tvHit(g, 0)) tvPress();
      if(tvHit(g, 1)) tvBack();
    } else {
      setKey("left",  ax < -0.4);
      setKey("right", ax >  0.4);
      setKey("jump",  tvHeld(g, 0) || ay < -0.5);
      if(tvHit(g, 2) || tvHit(g, 3)) setKey("item", true);   // предмет — по нажатию
      if(tvHit(g, 1)) tvBack();
      if(tvHit(g, 9)) tvBack();
    }
    if(tvHit(g, 8) && G.state === "menu") doButton("secret");  // Select ×4 — вход для разработчика
  }
}

/* ---------------- размер картинки ----------------
   Базовая версия оставляет холст в его родных 800x480: на мониторе это
   аккуратное окно, а на телевизоре — марка на пол-экрана. Здесь картинка
   растягивается на весь безопасный прямоугольник с сохранением пропорций,
   а буфер держим не выше полутора раз — иначе слабый чип телевизора
   начинает захлёбываться заливкой. */
function tvResize(){
  var pad = 0.94;                                  // запас на обрезку краёв
  var k = Math.min(Math.max(320, window.innerWidth  * pad) / VW,
                   Math.max(200, window.innerHeight * pad) / VH);
  /* Буфер держим родным, а растягивает картинку сам телевизор: масштабирование
     ему ничего не стоит, а рисование полутора миллионов лишних точек стоит
     дорого — на слабом чипе это 7 кадров в секунду вместо сорока. Крупнее
     буфер берём только если игрок сам выбрал «красиво». */
  var big = Math.max(1, Math.min(1.5, k));
  var buf = Math.round(VW * (SET.gfx === 1 ? big : 1));
  if(cv.width !== buf){ cv.width = buf; cv.height = Math.round(buf * VH / VW); }
  cv.style.width  = Math.round(VW*k) + "px";
  cv.style.height = Math.round(VH*k) + "px";
}
resize = tvResize;                                 // тем же именем зовут из полноэкранного
window.addEventListener("resize", tvResize);
tvResize();

/* Курсора на диване нет — и стрелка мыши тоже не нужна. */
drawCursor = function(){};

drawNews = tvTop(drawNews);           // экраны поверх фона
drawEvents = tvTop(drawEvents);
drawProfile = tvTop(drawProfile);
drawFriends = tvTop(drawFriends);
drawMods = tvTop(drawMods);
drawSkins = tvTop(drawSkins);
drawRecords = tvTop(drawRecords);
drawItemInfo = tvTop(drawItemInfo);
drawSettings = tvTop(drawSettings);
drawSeedIn = tvTop(drawSeedIn);
drawCode = tvTop(drawCode);
drawAdmin = tvTop(drawAdmin);
drawPaused = tvTop(drawPaused);
drawWin = tvTop(drawWin);
drawOver = tvTop(drawOver);

var tvBaseRender = render;
var tvGfx = SET.gfx;
render = function(){
  tvBase = 0;
  if(SET.gfx !== tvGfx){ tvGfx = SET.gfx; tvResize(); }   // сменили качество — пересобрать буфер
  tvPads();
  tvBaseRender();
  tvSync();                 /* кнопки пересобраны — только теперь видно, куда встать */
  if(tvUi()) tvRing();
};
'''

rep(u"""window.PEREMENA_DEBUG = {""",
    TV_LAYER.strip() + u"""

window.PEREMENA_DEBUG = {""")

rep(u"""  dev: function(){ return { on: devOn, god: devGod, box: devBox }; },""",
    u"""  tv: function(){ return { id: TV.id, ui: tvUi(), pad: TV.padSeen }; },
  tvMove: function(dx, dy){ tvMove(dx, dy); }, tvPress: tvPress, tvBack: tvBack,
  dev: function(){ return { on: devOn, god: devGod, box: devBox }; },""")


def main():
    src = io.open(SRC, encoding="utf-8").read()
    for old, new, count in subs:
        found = src.count(old)
        if found != count:
            sys.exit(u"make_tv: не нашёл кусок (%d вместо %d):\n%s" % (found, count, old[:120]))
        src = src.replace(old, new, count)
    io.open(DST, "w", encoding="utf-8").write(src)
    print(u"index_tv.html собран, правок: %d, строк: %d" % (len(subs), src.count("\n") + 1))


if __name__ == "__main__":
    main()
