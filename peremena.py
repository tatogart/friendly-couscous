#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПЕРЕМЕНА — успей пробежать школу за перемену.

Питоновская версия игры из index.html: та же физика, те же уровни, те же сиды.
Один файл, одна зависимость — pygame.

    pip install pygame
    python3 peremena.py

Управление: ← → бежать, ПРОБЕЛ прыгать (держишь — выше), E предмет,
R начать уровень заново, P пауза, M звук, F весь экран, Esc назад.
"""

import json
import math
import os
import random
import sys
import time
from array import array

import pygame

# ================== КОНСТАНТЫ ==================
TS, VW, VH = 32, 800, 480
GRAV, MAXFALL, JUMP_V, PAD_V, RUN_MAX = 0.62, 13.0, -12.2, -19.0, 4.4
SOLID = "#="
STEP = 1.0 / 60.0
SAVE_PATH = os.environ.get("PEREMENA_SAVE") or os.path.join(os.path.expanduser("~"), ".peremena.json")

DIFFS = {
    "normal":  {"key": "normal",  "name": "Обычный",     "time": 10 * 60, "enemy": 1.0,
                "fly": 1.0,  "range": 3.0, "coyote": 7, "one_life": False,
                "tag": "10 минут"},
    "hard":    {"key": "hard",    "name": "ХАРДКОР",     "time": 6 * 60,  "enemy": 1.6,
                "fly": 1.45, "range": 4.5, "coyote": 3, "one_life": True,
                "tag": "6 минут · 1 жизнь"},
    "endless": {"key": "endless", "name": "БЕСКОНЕЧНЫЙ", "time": 75,      "enemy": 1.15,
                "fly": 1.1,  "range": 3.5, "coyote": 6, "one_life": False,
                "endless": True, "bonus": 24, "tag": "75 сек · +24/этаж"},
}

# ================== ЦВЕТА ==================
WHITE = (255, 255, 255)
INK = (14, 32, 44)
MINT = (139, 255, 207)
SKYBLUE = (159, 216, 255)
GOLD = (255, 209, 102)
WARM = (255, 185, 138)
RED = (255, 128, 128)
DIM = (200, 220, 255)

# ================== УРОВНИ ==================
# .  пустота   #  кирпич   =  доска (проходится снизу)   @ старт   E выход
# o  пирожок   ^  шипы     x  завуч   v  самолётик   J батут   K ключ
# ?  шкафчик   m  мяч      B  кнопка звонка
CAMPAIGN = [
    {"name": "Звонок!",
     "hint": "← → бежать   ПРОБЕЛ прыгать   R заново",
     "rows": [
        "........................................",
        "........................................",
        "........................................",
        "........................................",
        "........................................",
        "........................................",
        "........................................",
        "........................................",
        "........................................",
        "..............ooo..............ooo......",
        ".............=====...........=====......",
        "........................................",
        "..@..o.............o.......o.......E.o..",
        "#########...###########...##############",
        "#########...###########...##############"]},
    {"name": "Столовая",
     "hint": "Прыгай завучу на голову — он обидится",
     "rows": [
        "........................................",
        "........................................",
        "........................................",
        "........................................",
        "........................................",
        "........................................",
        "........................................",
        "........................................",
        "........................................",
        "..........ooo...........................",
        ".........=====..........................",
        "........................ooo.............",
        "..@....x......o....^^....x....o....E....",
        "########################################",
        "########################################"]},
    {"name": "Лестница",
     "hint": "Батут закинет высоко — дальше по ступенькам",
     "rows": [
        "........................................",
        "........................................",
        "..........................ooo..E........",
        ".........................=========......",
        "........................................",
        "...................ooo..................",
        "..................======................",
        "........................................",
        "............ooo.........................",
        "............=====.......................",
        "........................................",
        "........................................",
        "..@...o..J............o.......o.........",
        "########################################",
        "########################################"]},
    {"name": "Коридор",
     "hint": "Платформы едут. Не зевай над пропастью",
     "rows": [
        "........................................",
        "........................................",
        "........................................",
        "........................................",
        "........................................",
        "........................................",
        "........................................",
        "........................................",
        "..........o..o....o....o..o.............",
        "........................................",
        "............===.......===...............",
        "........................................",
        "..@o............................o..E....",
        "#####...........................########",
        "#####...........................########"],
     "movers": [{"tx": 6, "ty": 11, "tw": 3, "axis": "x", "dist": 4, "speed": 0.02, "phase": 0.0}, {"tx": 16, "ty": 11, "tw": 3, "axis": "x", "dist": 3, "speed": 0.024, "phase": 1.2}, {"tx": 25, "ty": 11, "tw": 3, "axis": "x", "dist": 4, "speed": 0.022, "phase": 2.4}]},
    {"name": "Спортзал",
     "hint": "Самолётики летают по прямой. Пригнись!",
     "rows": [
        "........................................",
        "........................................",
        "........................................",
        "........................................",
        ".............ooo........................",
        "............=======.....................",
        "........................................",
        "......v..........................v......",
        "........................................",
        "........................ooo.............",
        ".......................=====............",
        "......o.......o.......o........o........",
        "..@.......^^........J.....^^........E...",
        "########################################",
        "########################################"]},
    {"name": "Библиотека",
     "hint": "Возьми ключ — без него дверь не откроется",
     "rows": [
        "........................................",
        "........................................",
        "........................................",
        "........................................",
        "..................K.....................",
        "................=====...................",
        "........................................",
        "...........ooo..........................",
        "..........=====.........................",
        "......o..................o..............",
        ".....===................===.............",
        "........................................",
        "..@.x......o......x......o.......x..E...",
        "######..######..######..######..########",
        "######..######..######..######..########"]},
    {"name": "Крыша школы",
     "hint": "Финальный рывок. Звонок уже близко!",
     "rows": [
        "........................................",
        "........................................",
        "........................................",
        "..........v...................ooo.......",
        ".............................======.....",
        "........................................",
        "........o....ooo........................",
        ".......===...=====......................",
        "........................................",
        "..............................v.........",
        ".......................===..............",
        "........................................",
        "..@..J....^^....x....^^....J..x..o..E...",
        "#######..##########..###################",
        "#######..##########..###################"],
     "movers": [{"tx": 12, "ty": 9, "tw": 2, "axis": "y", "dist": 3, "speed": 0.02, "phase": 0.0}, {"tx": 19, "ty": 11, "tw": 3, "axis": "x", "dist": 3, "speed": 0.026, "phase": 1.6}]},
]

GEN_NAMES = ["Первый этаж", "Раздевалка", "Столовая", "Актовый зал", "Лестница",
             "Спортзал", "Коридор", "Библиотека", "Кабинет труда", "Чердак",
             "Крыша", "Школьный двор", "Рекреация", "Кабинет химии"]
GEN_HINTS = ["Этого уровня ещё никто не видел", "Сид сгенерил — тебе проходить",
             "Смотри под ноги", "Тут может быть что угодно", "Беги, не думай",
             "Звонок не ждёт"]
SEED_ABC = "ACDEFHJKLMNPRTUVWXY3479"

# ================== ТЕМЫ ==================
THEMES = {
    "yard":    {"n": "Школьный двор", "deco": "yard", "sky": ((61, 126, 196), (124, 192, 234), (207, 234, 247)),
                "ground": (138, 90, 53), "cap": (79, 176, 94), "cap2": (99, 201, 114), "grass": True,
                "plank": (192, 139, 74), "plank2": (224, 169, 95)},
    "hall":    {"n": "Коридор", "deco": "hall", "sky": ((39, 56, 77), (60, 87, 113), (108, 139, 168)),
                "ground": (106, 87, 71), "cap": (207, 216, 227), "cap2": (238, 243, 248), "grass": False,
                "plank": (169, 119, 63), "plank2": (208, 155, 85)},
    "canteen": {"n": "Столовая", "deco": "canteen", "sky": ((90, 59, 44), (138, 91, 63), (216, 176, 138)),
                "ground": (122, 79, 54), "cap": (240, 215, 184), "cap2": (255, 240, 220), "grass": False,
                "plank": (184, 130, 63), "plank2": (227, 171, 94)},
    "gym":     {"n": "Спортзал", "deco": "gym", "sky": ((58, 74, 99), (91, 111, 140), (159, 176, 198)),
                "ground": (165, 112, 60), "cap": (217, 164, 94), "cap2": (240, 192, 122), "grass": False,
                "plank": (192, 139, 74), "plank2": (224, 169, 95)},
    "library": {"n": "Библиотека", "deco": "library", "sky": ((51, 36, 28), (85, 57, 42), (138, 102, 71)),
                "ground": (93, 68, 48), "cap": (141, 106, 74), "cap2": (169, 129, 93), "grass": False,
                "plank": (156, 107, 58), "plank2": (192, 139, 74)},
    "boiler":  {"n": "Подвал", "deco": "boiler", "sky": ((16, 21, 29), (28, 38, 51), (46, 61, 79)),
                "ground": (74, 74, 82), "cap": (107, 107, 116), "cap2": (133, 133, 143), "grass": False,
                "plank": (107, 90, 67), "plank2": (138, 117, 84)},
    "roof":    {"n": "Крыша", "deco": "roof", "sky": ((43, 58, 107), (122, 90, 160), (240, 160, 106)),
                "ground": (110, 110, 120), "cap": (154, 163, 173), "cap2": (183, 192, 201), "grass": False,
                "plank": (138, 138, 148), "plank2": (169, 169, 179)},
}
THEME_BY_NAME = {
    "Звонок!": "yard", "Столовая": "canteen", "Лестница": "hall", "Коридор": "hall",
    "Спортзал": "gym", "Библиотека": "library", "Крыша школы": "roof",
    "Первый этаж": "hall", "Раздевалка": "hall", "Актовый зал": "hall", "Рекреация": "hall",
    "Кабинет труда": "boiler", "Чердак": "boiler", "Крыша": "roof", "Школьный двор": "yard",
    "Кабинет химии": "library",
}


def theme_of(defn):
    return THEMES.get(defn.get("theme") or THEME_BY_NAME.get(defn["name"], "yard"), THEMES["yard"])


# ================== МОДИФИКАТОРЫ ==================
MODS = [
    ("fast",     "Завучи не спят",     "завучи на 40% быстрее",             20, "hard"),
    ("crowd",    "Толпа на перемене",  "на каждом уровне лишние завучи",    25, "hard"),
    ("nostomp",  "Хрупкий",            "на голову завучу не прыгнуть",      25, "hard"),
    ("ice",      "Мыли полы",          "скользко, тормозить нечем",         15, "hard"),
    ("heavy",    "Тяжёлый рюкзак",     "прыжок ниже",                       15, "hard"),
    ("dark",     "Свет выключили",     "видно только вокруг себя",          30, "hard"),
    ("hungry",   "Голод",              "выход откроется на все пирожки",    20, "hard"),
    ("rush",     "Скорый звонок",      "времени на треть меньше",           20, "hard"),
    ("onelife",  "Одна жизнь",         "первое падение — конец забега",     40, "hard"),
    ("mirror",   "Зеркало",            "управление наоборот",               15, "hard"),
    ("glass",    "Стеклянные доски",   "доски рассыпаются под ногами",      25, "hard"),
    ("fastgame", "Перемена бежит",     "вся игра быстрее на 20%",           25, "hard"),
    ("nobox",    "Шкафчики пусты",     "предметов не будет",                20, "hard"),
    ("jumpy",    "Прыгучие завучи",    "завучи подпрыгивают",               20, "hard"),
    ("long",     "Долгая перемена",    "времени в полтора раза больше",    -25, "easy"),
    ("sneak",    "Новые кроссовки",    "бежишь быстрее, прыгаешь выше",    -20, "easy"),
    ("empty",    "Завуч в отпуске",    "завучей нет совсем",               -35, "easy"),
    ("dbljump",  "Двойной прыжок",     "второй прыжок в воздухе всегда",   -25, "easy"),
    ("magnet",   "Магнит",             "пирожки сами летят в руки",        -15, "easy"),
    ("startbag", "Портфель на старте", "каждый уровень начинаешь со щитом",-15, "easy"),
    ("skipclass", "Прогульщик",        "уроки пропускаются совсем",        -15, "class"),
    ("strict",   "Строгий учитель",    "на уроке меньше времени",           20, "class"),
    ("exam",     "Контрольная",        "зачёт только без единой ошибки",    20, "class"),
    ("dbllesson", "Двойной урок",      "перед каждым этажом два урока",     25, "class"),
    ("easyclass", "Любимый предмет",   "зачёт ставят почти за что угодно", -20, "class"),
    ("favorite", "Любимчик учителя",   "за зачёт +30 секунд и 200 очков",  -15, "class"),
]
MOD_BY_KEY = {m[0]: m for m in MODS}

# ================== ПРЕДМЕТЫ ==================
ITEMS = {
    "soda":  {"n": "Газировка", "d": "рывок скорости на 6 сек",  "c": (255, 107, 107), "t": 360, "w": 22},
    "gum":   {"n": "Жвачка",    "d": "двойной прыжок на 15 сек", "c": (255, 159, 243), "t": 900, "w": 20},
    "bag":   {"n": "Портфель",  "d": "держит один удар",         "c": (155, 107, 240), "t": 0,   "w": 20},
    "watch": {"n": "Часы",      "d": "+20 секунд к перемене",    "c": (139, 255, 207), "t": 0,   "w": 20},
    "pass":  {"n": "Пропуск",   "d": "завучи не видят 8 сек",    "c": (255, 209, 102), "t": 480, "w": 18},
}
ITEM_KEYS = ["soda", "gum", "bag", "watch", "pass"]

# ================== СКИНЫ ==================
SKINS = [
    ("pupil", "Школьник",      "обычный такой",       (58, 160, 232), (74, 53, 36),  "none",    0),
    ("punk",  "Двоечник",      "кепка задом наперёд", (47, 62, 86),   (192, 57, 43), "cap",     40),
    ("honor", "Отличница",     "бант и белая блузка", (244, 246, 251), (138, 90, 47), "bow",    70),
    ("nerd",  "Ботаник",       "очки и жилетка",      (122, 78, 196), (47, 36, 24),  "glasses", 100),
    ("sport", "Физрук",        "свисток на шее",      (224, 102, 58), (58, 42, 30),  "whistle", 140),
    ("work",  "Трудовик",      "роба и кепка",        (47, 143, 91),  (74, 53, 36),  "cap",     180),
    ("spy",   "Завуч",         "костюм и галстук",    (44, 62, 88),   (58, 42, 30),  "tie",     240),
    ("grad",  "Выпускник",     "лента через плечо",   (35, 48, 68),   (74, 53, 36),  "sash",    320),
    ("ghost", "Призрак школы", "поговаривают, он с 90-х", (200, 214, 229), (230, 238, 247), "none", 450),
    ("cook",  "Повариха",      "белый колпак и половник", (245, 245, 240), (190, 150, 110), "chef",  520),
    ("guard", "Охранник",      "рация и суровый взгляд",  (60, 70, 90),   (40, 40, 44),    "radio", 640),
    ("dir",   "Директор",      "костюм, которого все боятся", (30, 34, 52), (120, 120, 130), "tie", 800),
    ("king",  "Король перемен", "корона за все достижения", (250, 200, 60), (120, 80, 30),  "crown", 1200),
]
SKIN_BY_KEY = {s[0]: s for s in SKINS}

# ================== УЛУЧШЕНИЯ ==================
# (ключ, имя, что даёт, сколько уровней, цена первого уровня, надбавка за уровень)
UPGRADES = [
    ("boots",   "Кроссовки",       "+6% к скорости бега",             3, 120, 110),
    ("springs", "Пружины в кедах", "+5% к высоте прыжка",             3, 150, 130),
    ("watch",   "Наручные часы",   "+12 секунд к перемене",           3, 140, 120),
    ("magnet",  "Магнитик",        "пирожки тянутся с 60 пикселей",   3, 130, 120),
    ("wallet",  "Кошелёк",         "+25% булок за собранные пирожки", 3, 180, 160),
    ("bag",     "Крепкий портфель", "каждый этаж начинаешь со щитом", 1, 400, 0),
    ("pockets", "Большие карманы", "носишь два предмета сразу",       1, 500, 0),
    ("revive",  "Второе дыхание",  "одно падение за забег не считается", 1, 700, 0),
]
UPG_BY_KEY = {u[0]: u for u in UPGRADES}


def upg(key):
    return SAVE.stats["upg"].get(key, 0)


def upg_price(key):
    u = UPG_BY_KEY[key]
    have = upg(key)
    if have >= u[3]:
        return None
    return u[4] + u[5] * have


# ================== ЗАДАНИЯ ДНЯ ==================
# (ключ, текст, счётчик забега, сколько нужно, награда)
TASK_POOL = [
    ("pies20",  "Собрать 20 пирожков",        "pies",    20, 60),
    ("pies40",  "Собрать 40 пирожков",        "pies",    40, 110),
    ("stomp5",  "Затоптать 5 завучей",        "stomps",  5,  70),
    ("levels3", "Пройти 3 этажа",             "levels",  3,  80),
    ("levels6", "Пройти 6 этажей",            "levels",  6,  140),
    ("lesson2", "Сдать 2 урока",              "lessons", 2,  70),
    ("clean1",  "Пройти этаж подчистую",      "clean",   1,  90),
    ("nofall1", "Добежать до выхода без падений", "nofall", 1, 150),
    ("keys1",   "Найти ключ",                 "keys",    1,  60),
    ("lockers3", "Открыть 3 шкафчика",        "lockers", 3,  70),
    ("goal1",   "Забить гол мячом",           "goals",   1,  80),
    ("combo3",  "Собрать серию ×3",           "combo",   3,  80),
]
TASK_BY_KEY = {t[0]: t for t in TASK_POOL}


# ================== ДОСТИЖЕНИЯ ==================
# (ключ, имя, описание, счётчик, сколько нужно, награда в булках)
ACHS = [
    ("first",    "Первая перемена",  "добежать до выхода",          "runs",       1,    25),
    ("regular",  "Завсегдатай",      "пять забегов до конца",       "runs",       5,    60),
    ("hardcore", "Хардкорщик",       "пройти хардкор",              "hard_runs",  1,    120),
    ("floors",   "Марафонец",        "десять этажей в бесконечном", "max_floor",  10,   90),
    ("sweet",    "Сладкоежка",       "собрать 250 пирожков",        "pies",       250,  50),
    ("baker",    "Кондитер",         "собрать 1000 пирожков",       "pies",       1000, 150),
    ("stomper",  "Прыгун",           "затоптать 50 завучей",        "stomps",     50,   70),
    ("striker",  "Футболист",        "выбить завуча мячом",         "goals",      1,    40),
    ("ringer",   "Звонарь",          "нажать звонок пять раз",      "bells",      5,    40),
    ("clean",    "Чистюля",          "пять уровней подчистую",      "clean",      5,    70),
    ("student",  "Зубрила",          "сдать десять уроков",         "lessons_ok", 10,   80),
    ("loser",    "Двоечник",         "завалить пять уроков",        "lessons_bad", 5,   30),
    ("styler",   "Модник",           "купить три скина",            "skins",      3,    60),
    ("collect",  "Коллекционер",     "купить все скины",            "skins",      9,    250),
    ("risky",    "Рисковый",         "забег с множителем от 2.0",   "best_mult",  200,  120),
    ("clumsy",   "Неваляшка",        "упасть пятьдесят раз",        "falls",      50,   40),
    ("swift",    "Скороход",         "забег быстрее пяти минут",    "fast_run",   1,    110),
    ("user",     "Гурман",           "использовать 25 предметов",   "items",      25,   60),
    ("walker",   "Старожил",         "пройти 50 уровней",           "levels",     50,   100),
    ("rich",     "Богач",            "накопить 500 булок",          "buns",       500,  80),
    ("hops",     "Кузнечик",         "тысяча прыжков",              "jumps",      1000, 60),
    ("springy",  "Батутист",         "сто раз на батуте",           "pads",       100,  70),
    ("nosy",     "Любопытный",       "открыть 25 шкафчиков",        "lockers",    25,   60),
    ("keeper",   "Ключник",          "найти десять ключей",         "keys",       10,   70),
    ("combo",    "Пирожковая серия", "собрать ×5 подряд",           "max_combo",  5,    90),
    ("quizzer",  "Знаток",           "25 верных ответов",           "quiz_ok",    25,   80),
    ("nofall",   "Ни разу не упал",  "пройти забег без падений",    "no_fall",    1,    150),
    ("glassy",   "Стеклобой",        "проломить 50 досок",          "glass",      50,   70),
    ("spender",  "Транжира",         "потратить 1000 булок",        "spent",      1000, 90),
    ("seeder",   "Сидовод",          "пять забегов по сиду",        "seed_runs",  5,    70),
    ("endless",  "Без конца",        "три забега в бесконечном",    "end_runs",   3,    80),
    ("tower",    "Небоскрёб",        "25 этажей в бесконечном",     "max_floor",  25,   200),
    ("hard5",    "Железный",         "пять хардкорных забегов",     "hard_runs",  5,    220),
    ("stomp2",   "Гроза завучей",    "затоптать 200 завучей",       "stomps",     200,  160),
    ("goal10",   "Бомбардир",        "десять голов мячом",          "goals",      10,   120),
    ("ringer2",  "Колокольчик",      "нажать звонок 25 раз",        "bells",      25,   90),
    ("risky2",   "Безумец",          "забег с множителем от 2.5",   "best_mult",  250,  260),
    ("modman",   "Коллекция правил", "забег с пятью модификаторами", "mod_run",   1,    110),
    ("veteran",  "Ветеран школы",    "пройти 200 уровней",          "levels",     200,  400),
    ("days3",    "Постоянный",       "заходить три дня подряд",     "days",       3,    90),
    ("days7",    "Каждую перемену",  "заходить неделю подряд",      "days",       7,    260),
    ("shopper",  "Первая покупка",   "купить улучшение",            "upg_total",  1,    40),
    ("tuned",    "Прокачанный",      "пять уровней улучшений",      "upg_total",  5,    120),
    ("maxed",    "Всё своё ношу",    "выкупить все улучшения",      "upg_total",  18,   400),
    ("tasker",   "Дежурный",         "выполнить 5 заданий дня",     "tasks_done", 5,    100),
    ("tasker2",  "Староста",         "выполнить 25 заданий дня",    "tasks_done", 25,   300),
    ("shopaholic", "Богатый ученик", "потратить 5000 булок",        "spent",      5000, 350),
]

# ================== ВИКТОРИНА ==================
QUIZ = [
    ("Сколько будет 7 × 8?", ["56", "54", "48"], 0),
    ("Столица Франции?", ["Париж", "Лион", "Марсель"], 0),
    ("Сколько материков на Земле?", ["6", "5", "7"], 0),
    ("H2O — это…", ["вода", "соль", "воздух"], 0),
    ("Кто написал «Му-му»?", ["Тургенев", "Толстой", "Гоголь"], 0),
    ("Сколько будет 144 ÷ 12?", ["12", "14", "11"], 0),
    ("Самая большая планета?", ["Юпитер", "Сатурн", "Земля"], 0),
    ("Сколько ног у паука?", ["8", "6", "10"], 0),
    ("Столица Японии?", ["Токио", "Киото", "Осака"], 0),
    ("Сколько дней в високосном году?", ["366", "365", "364"], 0),
    ("Какой газ мы вдыхаем для дыхания?", ["кислород", "азот", "гелий"], 0),
    ("15% от 200 — это…", ["30", "25", "35"], 0),
    ("Кто открыл Америку?", ["Колумб", "Магеллан", "Кук"], 0),
    ("Сколько секунд в часе?", ["3600", "60", "1440"], 0),
    ("Самое глубокое озеро?", ["Байкал", "Ладожское", "Онежское"], 0),
    ("Луна — это…", ["спутник Земли", "планета", "звезда"], 0),
    ("Сколько будет 9²?", ["81", "72", "99"], 0),
    ("Какая часть речи «быстро»?", ["наречие", "глагол", "союз"], 0),
    ("Сколько букв в русском алфавите?", ["33", "32", "34"], 0),
    ("Столица Италии?", ["Рим", "Милан", "Венеция"], 0),
]


# ================== СИДЫ ==================
# Точно тот же генератор, что и в браузерной версии: один код — одна школа.
M32 = 0xFFFFFFFF


def imul(a, b):
    r = (a * b) & M32
    return r - 0x100000000 if r > 0x7FFFFFFF else r


def hash_seed(text):
    h = 2166136261
    for ch in str(text).upper():
        h = (h ^ ord(ch)) & M32
        h = imul(h, 16777619) & M32
    return h & M32


def mulberry(a):
    state = [a & M32]

    def rnd():
        state[0] = (state[0] + 0x6D2B79F5) & M32
        a0 = state[0]
        t = imul(a0 ^ (a0 >> 15), 1 | a0) & M32
        t = ((t + imul(t ^ (t >> 7), 61 | t)) & M32) ^ t
        return ((t ^ (t >> 14)) & M32) / 4294967296.0
    return rnd


def random_seed():
    return "".join(random.choice(SEED_ABC) for _ in range(5))


def day_seed():
    t = time.localtime()
    r = mulberry(hash_seed("den/%d-%d-%d" % (t.tm_year, t.tm_mon, t.tm_mday)))
    return "".join(SEED_ABC[int(r() * len(SEED_ABC))] for _ in range(5))


def clean_seed(text):
    out = ""
    for ch in str(text or "").upper():
        if ch.isdigit() or ("A" <= ch <= "Z"):
            out += ch
        if len(out) >= 8:
            break
    return out


def irnd(rnd, a, b):
    return a + int(rnd() * (b - a + 1))


def pick_of(rnd, arr):
    return arr[int(rnd() * len(arr))]


def gen_level(rnd, idx, name, with_key):
    """Тот же алгоритм, что в index.html: слева направо вдоль земли."""
    w_all, h_all = 40 + idx * 2, 15
    g = [["." for _ in range(w_all)] for _ in range(h_all)]
    movers, plats = [], []
    for x in range(w_all):
        g[13][x] = "#"
        g[14][x] = "#"
    g[12][2] = "@"
    end_col, col = w_all - 4, 6

    def coins(row, frm, n):
        for k in range(n):
            if 2 < frm + k < w_all - 2 and g[row][frm + k] == ".":
                g[row][frm + k] = "o"

    def carve(frm, w):
        for k in range(w):
            g[13][frm + k] = "."
            g[14][frm + k] = "."

    pool = ["flat", "coins", "platform", "locker"]
    if idx >= 1:
        pool += ["pit", "enemy"]
    if idx >= 2:
        pool += ["spikes", "enemy", "platform", "ball", "bell"]
    if idx >= 3:
        pool += ["pad", "pit"]
    if idx >= 4:
        pool += ["mover", "fly", "spikes"]
    if idx >= 5:
        pool += ["mover", "fly", "enemy"]

    while col < end_col - 6:
        f = pick_of(rnd, pool)
        if f == "flat":
            col += irnd(rnd, 3, 5)
        elif f == "coins":
            coins(12, col, irnd(rnd, 2, 3))
            col += 5
        elif f in ("pit", "mover"):
            mover = (f == "mover")
            w = irnd(rnd, 4, 5) if mover else irnd(rnd, 2, 3 if idx >= 3 else 2)
            if col + w > end_col - 6:
                col += 3
                continue
            carve(col, w)
            if mover:
                movers.append({"tx": col, "ty": 11, "tw": 3, "axis": "x",
                               "dist": max(2, w - 3), "speed": 0.018 + rnd() * 0.008,
                               "phase": rnd() * 6.28})
                coins(10, col + 1, 2)
            elif rnd() < 0.5:
                coins(11, col, w)
            col += w + 4
        elif f == "spikes":
            w = irnd(rnd, 1, 2)
            for i in range(w):
                g[12][col + i] = "^"
            col += w + 4
        elif f == "enemy":
            g[12][col] = "x"
            col += 6
        elif f == "locker":
            g[12][col] = "?"
            col += 4
        elif f == "ball":
            g[12][col] = "m"
            col += 4
        elif f == "bell":
            g[12][col] = "B"
            col += 4
        elif f == "fly":
            g[irnd(rnd, 7, 9)][col] = "v"
            col += 4
        elif f == "platform":
            w, row = irnd(rnd, 3, 5), irnd(rnd, 10, 11)
            for i in range(w):
                g[row][col + i] = "="
            coins(row - 1, col + 1, min(w - 1, irnd(rnd, 1, 3)))
            plats.append((col + w // 2, row - 1))
            col += w + 2
        elif f == "pad":
            g[12][col] = "J"
            prow, pw = irnd(rnd, 5, 6), irnd(rnd, 3, 4)
            px = max(1, col + irnd(rnd, -1, 1))
            for i in range(pw):
                if px + i < w_all - 1:
                    g[prow][px + i] = "="
            coins(prow - 1, px, min(pw, 3))
            plats.append((px + 1, prow - 1))
            col += pw + 3

    g[12][end_col] = "E"

    if with_key:
        if plats:
            px, py = plats[int(rnd() * len(plats))]
            g[py][px] = "K"
        else:
            for x in range(end_col // 2, end_col - 2):
                if g[12][x] == "." and g[13][x] == "#":
                    g[12][x] = "K"
                    break

    got = sum(row.count("o") for row in g)
    tries = 0
    while got < 6 and tries < 200:
        tries += 1
        x = irnd(rnd, 4, end_col - 2)
        if g[12][x] == "." and g[13][x] == "#":
            g[12][x] = "o"
            got += 1

    for x in range(w_all):                      # всё на земле должно стоять на твёрдом
        if g[12][x] in "@Ex^JKo?mB" and g[13][x] != "#":
            g[13][x] = "#"
            g[14][x] = "#"

    return {"name": name, "hint": pick_of(rnd, GEN_HINTS),
            "rows": ["".join(r) for r in g], "movers": movers}


def gen_levels(seed):
    rnd = mulberry(hash_seed(seed))
    names = list(GEN_NAMES)
    key_level = irnd(rnd, 2, 5)
    out = []
    for i in range(7):
        if names:
            name = names.pop(int(rnd() * len(names)))
        else:
            name = "Этаж %d" % (i + 1)
        out.append(gen_level(rnd, i, name, i == key_level))
    return out


# ================== СОХРАНЕНИЕ ==================
def fresh_stats():
    return {"runs": 0, "hard_runs": 0, "pies": 0, "buns": 0, "stomps": 0, "items": 0,
            "clean": 0, "falls": 0, "best": 0, "levels": 0, "lessons_ok": 0,
            "lessons_bad": 0, "goals": 0, "bells": 0, "max_floor": 0, "best_mult": 0,
            "fast_run": 0, "jumps": 0, "pads": 0, "lockers": 0, "keys": 0,
            "max_combo": 0, "quiz_ok": 0, "no_fall": 0, "glass": 0, "spent": 0,
            "seed_runs": 0, "end_runs": 0, "mod_run": 0, "days": 1, "last_day": "",
            "upg_total": 0, "tasks_done": 0, "bought": 0,
            "owned": ["pupil"], "achs": [], "wear": {}, "upg": {}}


def fresh_settings():
    return {"vol": 2, "shake": 2, "hints": 1, "fancy": 1}


def fresh_daily():
    return {"day": "", "reward": 0, "tasks": []}


class Save(object):
    """Всё, что живёт между запусками: статистика, рекорды, моды, настройки."""

    def __init__(self):
        self.stats = fresh_stats()
        self.records = {}
        self.mods = {}
        self.settings = fresh_settings()
        self.skin = "pupil"
        self.seed = random_seed()
        self.src = "classic"
        self.daily = fresh_daily()
        self.start_item = None
        self.load()

    def load(self):
        try:
            with open(SAVE_PATH, encoding="utf-8") as f:
                raw = json.load(f)
        except Exception:
            return
        base = fresh_stats()
        for k, v in (raw.get("stats") or {}).items():
            if k in base and isinstance(v, type(base[k])):
                self.stats[k] = v
        self.records = raw.get("records") or {}
        self.mods = {k: True for k in (raw.get("mods") or []) if k in MOD_BY_KEY}
        for k, v in (raw.get("settings") or {}).items():
            if k in self.settings:
                self.settings[k] = int(v)
        self.skin = raw.get("skin", "pupil")
        if self.skin not in SKIN_BY_KEY or self.skin not in self.stats["owned"]:
            self.skin = "pupil"
        self.seed = clean_seed(raw.get("seed")) or random_seed()
        self.src = raw.get("src", "classic")
        d = raw.get("daily")
        if isinstance(d, dict):
            self.daily = {"day": d.get("day", ""), "reward": int(d.get("reward", 0)),
                          "tasks": [t for t in (d.get("tasks") or []) if t.get("k") in TASK_BY_KEY]}
        it = raw.get("start_item")
        self.start_item = it if it in ITEMS else None
        self.stats["upg"] = {k: int(v) for k, v in (self.stats.get("upg") or {}).items()
                             if k in UPG_BY_KEY}

    def save(self):
        try:
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump({"stats": self.stats, "records": self.records,
                           "mods": sorted(self.mods.keys()), "settings": self.settings,
                           "skin": self.skin, "seed": self.seed, "src": self.src,
                           "daily": self.daily, "start_item": self.start_item},
                          f, ensure_ascii=False)
        except Exception:
            pass

    def day_streak(self):
        t = time.localtime()
        today = "%d-%d-%d" % (t.tm_year, t.tm_mon, t.tm_mday)
        if self.stats["last_day"] != today:
            y = time.localtime(time.time() - 86400)
            yest = "%d-%d-%d" % (y.tm_year, y.tm_mon, y.tm_mday)
            self.stats["days"] = self.stats["days"] + 1 if self.stats["last_day"] == yest else 1
            self.stats["last_day"] = today
        if self.daily.get("day") != today:          # новый день — новые задания
            rnd = mulberry(hash_seed("zadaniya/" + today))
            pool = list(TASK_POOL)
            picked = []
            for _ in range(3):
                if not pool:
                    break
                picked.append(pool.pop(int(rnd() * len(pool))))
            self.daily = {"day": today,
                          "reward": 50 + 25 * min(7, self.stats["days"]),
                          "tasks": [{"k": t[0], "have": 0, "taken": False} for t in picked]}
        self.save()


SAVE = Save()


def mod(key):
    return bool(SAVE.mods.get(key))


def mod_count():
    return len(SAVE.mods)


def mod_mult():
    total = sum(m[3] for m in MODS if SAVE.mods.get(m[0]))
    return max(0.1, 1 + total / 100.0)


def owns(key):
    return key in SAVE.stats["owned"]


def rec_key(mode, src, seed):
    return mode + ("_" + seed if src == "seed" else "")


# ================== ПАНЕЛЬ РАЗРАБОТЧИКА ==================
# Кода в файле нет: сверяется тот же отпечаток, что и в браузерной версии,
# так что код у обеих версий один и тот же.
DEV_SALT = "peremena/zvonok/2026"
DEV_HASH = "812e048c"


def code_hash(text):
    h = 2166136261
    text = DEV_SALT + "|" + text + "|" + DEV_SALT
    for ch in text:
        h = imul(h ^ ord(ch), 16777619) & M32
    for _ in range(150000):
        h ^= h >> 15
        h = imul(h, 2246822519) & M32
        h = ((h << 7) | (h >> 25)) & M32
    return "%08x" % h


# ================== ЗВУК ==================
class Sfx(object):
    """Пищалки собираются прямо в памяти — никаких файлов рядом с игрой."""

    RATE = 22050

    def __init__(self):
        self.ok = False
        self.cache = {}
        try:
            pygame.mixer.pre_init(self.RATE, -16, 1, 512)
            pygame.mixer.init()
            self.ok = True
        except Exception:
            self.ok = False

    def _wave(self, freq, dur, kind, vol, slide):
        key = (int(freq), round(dur, 3), kind, round(vol, 3), int(slide))
        snd = self.cache.get(key)
        if snd is not None:
            return snd
        n = max(1, int(self.RATE * dur))
        buf = array("h", [0]) * n
        phase = 0.0
        for i in range(n):
            k = i / float(n)
            f = freq + slide * k
            phase += 2 * math.pi * f / self.RATE
            if kind == "square":
                s = 1.0 if math.sin(phase) >= 0 else -1.0
            elif kind == "saw":
                s = ((phase / math.pi) % 2.0) - 1.0
            else:
                s = math.sin(phase)
            env = min(1.0, (1 - k) * 3.0)          # затухание к концу
            buf[i] = int(max(-1.0, min(1.0, s * env * vol)) * 22000)
        snd = pygame.mixer.Sound(buffer=buf.tobytes())
        self.cache[key] = snd
        return snd

    def tone(self, freq, dur=0.1, kind="square", vol=0.4, slide=0):
        if not self.ok or SAVE.settings["vol"] == 0:
            return
        try:
            s = self._wave(freq, dur, kind, vol, slide)
            s.set_volume(0.45 if SAVE.settings["vol"] == 1 else 0.9)
            s.play()
        except Exception:
            pass

    def jump(self):  self.tone(420, 0.13, "square", 0.35, 260)
    def coin(self, combo=1): self.tone(760 + combo * 110, 0.08, "square", 0.3)
    def stomp(self): self.tone(210, 0.14, "square", 0.5, -120)
    def hurt(self):  self.tone(300, 0.3, "saw", 0.45, -220)
    def pad(self):   self.tone(260, 0.2, "sine", 0.5, 700)
    def key(self):   self.tone(700, 0.12, "sine", 0.4, 350)
    def door(self):  self.tone(523, 0.18, "sine", 0.4, 520)
    def win(self):   self.tone(523, 0.3, "sine", 0.45, 800)
    def fail(self):  self.tone(330, 0.35, "square", 0.4, -180)
    def box(self):   self.tone(380, 0.1, "square", 0.35, 180)
    def bell(self):  self.tone(1200, 0.25, "square", 0.4, -320)
    def click(self): self.tone(520, 0.05, "square", 0.25, 120)


SFX = Sfx()


# ================== РАЗБОР УРОВНЯ ==================
def roll_item(rnd):
    total = sum(ITEMS[k]["w"] for k in ITEM_KEYS)
    r = rnd() * total
    for k in ITEM_KEYS:
        r -= ITEMS[k]["w"]
        if r <= 0:
            return k
    return "soda"


class Level(object):
    def __init__(self, defn, diff):
        self.name = defn["name"]
        self.hint = defn.get("hint", "")
        self.theme = theme_of(defn)
        rows = list(defn["rows"])
        self.w = max(len(r) for r in rows)
        self.h = len(rows)
        self.grid = [list(r.ljust(self.w, ".")) for r in rows]
        self.coins, self.spikes, self.enemies, self.pads = [], [], [], []
        self.lockers, self.balls, self.bells, self.movers = [], [], [], []
        self.key = None
        self.door = None
        self.door_hit = None
        self.start = (2 * TS, 12 * TS)
        self.crack, self.broke = {}, {}
        self.need_key = False
        rnd = mulberry(hash_seed(self.name))

        for cy in range(self.h):
            for cx in range(self.w):
                ch = self.grid[cy][cx]
                x, y = cx * TS, cy * TS
                if ch == "@":
                    self.start = (x + 2, y + 4)
                    self.grid[cy][cx] = "."
                elif ch == "o":
                    self.coins.append({"x": x + 8, "y": y + 8, "w": 16, "h": 16,
                                       "got": False, "ph": rnd() * 6.28})
                    self.grid[cy][cx] = "."
                elif ch == "^":
                    self.spikes.append(pygame.Rect(x + 2, y + 16, TS - 4, 16))
                    self.grid[cy][cx] = "."
                elif ch in "xv":
                    fly = (ch == "v")
                    if not mod("empty"):
                        self.enemies.append(self.make_enemy(x + 3, y + (4 if not fly else 6), fly, diff))
                    self.grid[cy][cx] = "."
                elif ch == "J":
                    self.pads.append({"x": x + 2, "y": y + 18, "w": TS - 4, "h": 14, "t": 0})
                    self.grid[cy][cx] = "."
                elif ch == "K":
                    self.key = {"x": x + 8, "y": y + 10, "w": 16, "h": 16, "got": False, "ph": 0.0}
                    self.need_key = True
                    self.grid[cy][cx] = "."
                elif ch == "?":
                    if not mod("nobox"):
                        self.lockers.append({"x": x + 3, "y": y + 4, "w": 26, "h": 28,
                                             "open": False, "t": 0, "item": None})
                    self.grid[cy][cx] = "."
                elif ch == "m":
                    self.balls.append({"x": x + 10, "y": y + 14, "w": 14, "h": 14,
                                       "vx": 0.0, "vy": 0.0, "cool": 0})
                    self.grid[cy][cx] = "."
                elif ch == "B":
                    self.bells.append({"x": x + 6, "y": y + 2, "w": 20, "h": 24, "used": False})
                    self.grid[cy][cx] = "."
                elif ch == "E":
                    self.door = pygame.Rect(x + 3, y - 14, 26, 46)
                    self.door_hit = pygame.Rect(x, 0, TS, y + TS)
                    self.grid[cy][cx] = "."

        for m in defn.get("movers", []):
            self.movers.append({"ox": m["tx"] * TS, "oy": m["ty"] * TS,
                                "x": float(m["tx"] * TS), "y": float(m["ty"] * TS),
                                "w": m["tw"] * TS, "h": 14, "axis": m["axis"],
                                "dist": m["dist"] * TS, "speed": m["speed"],
                                "t": m.get("phase", 0.0), "dx": 0.0, "dy": 0.0})

        if mod("crowd"):                       # «Толпа на перемене» — лишние завучи
            extra = 2
            for cx in range(6, self.w - 6):
                if extra <= 0:
                    break
                if self.grid[12][cx] == "." and self.grid[13][cx] == "#":
                    if self.door and abs(cx * TS - self.door.centerx) < TS * 3:
                        continue
                    self.enemies.append(self.make_enemy(cx * TS + 3, 12 * TS + 4, False, diff))
                    extra -= 1

        for lk in self.lockers:
            lk["item"] = roll_item(mulberry(hash_seed(self.name + "#" + str(int(lk["x"])))))
        self.coin_total = len(self.coins)

    @staticmethod
    def make_enemy(x, y, fly, diff):
        speed = (1.5 * diff["fly"] if fly else 0.85 * diff["enemy"]) * (1.4 if mod("fast") else 1.0)
        return {"x": float(x), "y": float(y), "w": 28 if fly else 26, "h": 18 if fly else 28,
                "vx": speed, "vy": 0.0, "fly": fly, "home_x": float(x),
                "range": 999999 if fly else TS * diff["range"], "dead": False, "dead_t": 0,
                "froze": 0, "base": y, "ph": 0.0}

    def solid_at(self, cx, cy):
        if cy < 0 or cy >= self.h or cx < 0 or cx >= self.w:
            return ""
        ch = self.grid[cy][cx]
        if ch == "=" and self.broke.get((cx, cy), 0) > 0:
            return ""
        return ch if ch in SOLID else ""


def rect_of(obj):
    return pygame.Rect(int(obj["x"]), int(obj["y"]), int(obj["w"]), int(obj["h"]))


def overlap(a, b):
    return (a["x"] < b["x"] + b["w"] and a["x"] + a["w"] > b["x"] and
            a["y"] < b["y"] + b["h"] and a["y"] + a["h"] > b["y"])


def clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)


# ================== СОСТОЯНИЕ ИГРЫ ==================
class Game(object):
    def __init__(self):
        self.diff = DIFFS["normal"]
        self.pick = "normal"
        self.state = "menu"
        self.back = None
        self.levels = []
        self.level_index = 0
        self.level = None
        self.player = None
        self.cam = 0.0
        self.lead = 0.0
        self.tick = 0
        self.time_left = 600.0
        self.coins = 0
        self.coins_max = 0
        self.deaths = 0
        self.floor = 1
        self.combo = 0
        self.combo_t = 0
        self.combo_pts = 0
        self.bonus_pts = 0
        self.all_pies = 0
        self.has_key = False
        self.item = None
        self.item2 = None
        self.shield = False
        self.invul = 0
        self.revive_left = 0
        self.task_seen = set()
        self.buff = {"soda": 0, "gum": 0, "pass": 0}
        self.parts, self.pops, self.rings, self.trail = [], [], [], []
        self.hit_stop = 0
        self.shake = 0.0
        self.flash = 0
        self.toast_text = ""
        self.toast_t = 0
        self.ach_queue = []
        self.ach_show = None
        self.ach_t = 0
        self.lesson = None
        self.lesson_left = 0
        self.record = False
        self.wallet_paid = 0
        self.item2 = None
        self.revive_left = 0
        self.task_seen = set()
        self.best = None
        self.score_shown = 0.0
        self.erng = None
        self.mod_tab = "hard"
        self.rec_tab = "stats"
        self.shop_tab = "skins"
        self.shop_page = 0
        self.dev_on = False
        self.dev_god = False
        self.cheated = False
        self.code = ""
        self.code_bad = 0
        self.code_lock = 0
        self.code_tries = 0
        self.secret_hits = 0
        self.secret_t = 0
        self.confirm = None
        self.confirm_t = 0
        self.item2 = None
        self.revive_left = 0
        self.wallet_paid = 0
        self.task_seen = set()
        self.ach_page = 0
        self.seed_in = ""
        self.buttons = []
        self.hot = None
        self.hot_t = 0
        self.mouse = (-999, -999)
        self.set_levels()

    # ---------- уровни ----------
    def set_levels(self):
        if SAVE.src == "seed":
            self.levels = gen_levels(SAVE.seed)
        else:
            self.levels = [dict(l) for l in CAMPAIGN]

    def time_limit(self):
        t = self.diff["time"]
        if mod("rush"):
            t *= 0.67
        if mod("long"):
            t *= 1.5
        return int(round(t)) + 12 * upg("watch")

    def one_life(self):
        return self.diff.get("one_life") or mod("onelife")

    def run_max(self):
        v = RUN_MAX * (1.18 if mod("sneak") else 1.0) * (1 + 0.06 * upg("boots"))
        if self.buff["soda"] > 0:
            v *= 1.45
        return v

    def jump_v(self):
        return (JUMP_V * (0.92 if mod("heavy") else 1.0) * (1.06 if mod("sneak") else 1.0)
                * (1 + 0.05 * upg("springs")))

    def magnet_range(self):
        return max(120 if mod("magnet") else 0, 60 * upg("magnet"))

    def can_double(self):
        return mod("dbljump") or self.buff["gum"] > 0

    # ---------- забег ----------
    def start_run(self, mode):
        self.diff = DIFFS.get(mode, DIFFS["normal"])
        self.pick = self.diff["key"]
        if self.diff.get("endless"):
            SAVE.src = "seed"
        self.set_levels()
        if self.diff.get("endless"):
            self.erng = mulberry(hash_seed(SAVE.seed + "/endless"))
        self.level_index = 0
        self.floor = 1
        self.coins = 0
        self.deaths = 0
        self.combo = self.combo_t = self.combo_pts = self.bonus_pts = self.all_pies = 0
        self.item = None
        self.item2 = None
        self.shield = False
        self.invul = 0
        self.revive_left = upg("revive")
        self.task_seen = set()
        self.buff = {"soda": 0, "gum": 0, "pass": 0}
        self.parts, self.pops, self.rings, self.trail = [], [], [], []
        self.record = False
        self.wallet_paid = 0
        self.score_shown = 0.0
        self.time_left = float(self.time_limit())
        self.coins_max = sum(Level(d, self.diff).coin_total for d in self.levels)
        self.load_level(0)
        if SAVE.start_item:                       # купленный в магазине стартовый предмет
            self.item = SAVE.start_item
            SAVE.start_item = None
            SAVE.save()
            self.toast("В руках: " + ITEMS[self.item]["n"])
        self.state = "play"
        if not mod("skipclass"):
            self.start_lesson()

    def load_level(self, idx):
        self.level_index = idx
        self.level = Level(self.levels[idx], self.diff)
        self.has_key = not self.level.need_key
        self.spawn_player()

    def spawn_player(self):
        if mod("startbag") or upg("bag"):
            self.shield = True
        sx, sy = self.level.start
        self.player = {"x": float(sx), "y": float(sy), "w": 20, "h": 28, "vx": 0.0, "vy": 0.0,
                       "dir": 1, "grounded": False, "coyote": 0, "jump_buf": 0, "anim": 0.0,
                       "sqx": 1.0, "sqy": 1.0, "dead": False, "dead_t": 0, "standing": None,
                       "spawn_t": 18, "jumping": False, "air": 0, "fall": 0.0}
        self.cam = self.cam_target()

    def cam_target(self):
        if not self.level or not self.player:
            return self.cam
        p = self.player
        want = clamp(p["vx"] * 17, -74, 74)
        self.lead += (want - self.lead) * 0.05
        return clamp(p["x"] + p["w"] / 2 - VW / 2 + self.lead, 0, max(0, self.level.w * TS - VW))

    def endless_push(self):
        n = len(self.levels)
        idx = min(6, 1 + n // 3)
        name = GEN_NAMES[int(self.erng() * len(GEN_NAMES))] + " " + str(n + 1)
        self.levels.append(gen_level(self.erng, idx, name, self.erng() < 0.25))
        self.coins_max += Level(self.levels[n], self.diff).coin_total

    def next_level(self):
        self.stat("levels")
        self.task_bump("levels")
        wear = SAVE.stats["wear"]
        wear[SAVE.skin] = wear.get(SAVE.skin, 0) + 1
        if upg("wallet") and self.coins:                  # кошелёк доплачивает за этаж
            extra = int(self.coins * 0.25 * upg("wallet")) - self.wallet_paid
            if extra > 0:
                SAVE.stats["buns"] += extra
                self.wallet_paid += extra
                self.pop(self.player["x"] + 10, self.player["y"] - 26,
                         "+%d булок" % extra, GOLD, 13)
        if self.diff.get("endless") and self.floor > SAVE.stats["max_floor"]:
            SAVE.stats["max_floor"] = self.floor
        if int(mod_mult() * 100) > SAVE.stats["best_mult"]:
            SAVE.stats["best_mult"] = int(mod_mult() * 100)
        if self.coins_left() == 0 and self.level.coin_total > 0:
            self.bonus_pts += 50
            self.all_pies += 1
            self.stat("clean")
            self.task_bump("clean")
            self.toast("Все пирожки на уровне! +50")
            self.pop(self.player["x"] + 10, self.player["y"] - 10, "+50 ЧИСТО", MINT, 15)
        SFX.door()
        self.save_and_check()
        if self.diff.get("endless"):
            self.time_left += self.diff["bonus"]
            self.floor += 1
            if self.level_index + 1 >= len(self.levels):
                self.endless_push()
            self.state = "clear"
            self.clear_t = 40
            return
        if self.level_index + 1 >= len(self.levels):
            self.finish_run()
            return
        self.state = "clear"
        self.clear_t = 40

    def after_clear(self):
        self.load_level(self.level_index + 1)
        self.state = "play"
        self.item = self.item
        if not mod("skipclass"):
            self.start_lesson()

    def finish_run(self):
        self.state = "win"
        SFX.win()
        self.stat("runs")
        if self.diff.get("one_life"):
            self.stat("hard_runs")
        if self.diff.get("endless"):
            self.stat("end_runs")
        if SAVE.src == "seed":
            self.stat("seed_runs")
        if self.deaths == 0:
            self.stat("no_fall")
            self.task_bump("nofall")
        if mod_count() >= 5:
            self.stat("mod_run")
        if (self.diff["time"] - self.time_left) < 300:
            SAVE.stats["fast_run"] = 1
        score = self.run_score()
        key = rec_key(self.diff["key"], SAVE.src, SAVE.seed)
        best = SAVE.records.get(key)
        self.best = best
        if score > SAVE.stats["best"]:
            SAVE.stats["best"] = score
        if not self.cheated and (not best or score > best.get("score", 0)):
            SAVE.records[key] = {"score": score, "time": self.diff["time"] - self.time_left}
            self.record = True
        self.save_and_check()

    def go_over(self, why):
        self.state = "over"
        self.over_why = why
        score = self.run_score()
        if score > SAVE.stats["best"]:
            SAVE.stats["best"] = score
        self.save_and_check()

    # ---------- очки ----------
    def coins_left(self):
        return sum(1 for c in self.level.coins if not c["got"])

    def door_open(self):
        if self.level.need_key and not self.has_key:
            return False
        if mod("hungry") and self.coins_left() > 0:
            return False
        return True

    def run_points(self):
        done = len(self.levels) if self.state == "win" else self.level_index
        return max(0, done * 100 + self.coins * 10 + self.combo_pts + self.bonus_pts +
                   int(self.time_left) * 2 - self.deaths * 20)

    def run_score(self):
        return int(round(self.run_points() * mod_mult()))

    # ---------- статистика ----------
    def stat(self, key, n=1):
        SAVE.stats[key] = SAVE.stats.get(key, 0) + n

    def task_bump(self, kind, n=1):
        """Задания дня считаются по ходу забегов и копятся до полуночи."""
        hit = False
        for t in SAVE.daily.get("tasks", []):
            tpl = TASK_BY_KEY.get(t["k"])
            if not tpl or tpl[2] != kind or t["taken"]:
                continue
            before = t["have"]
            if kind == "combo":
                t["have"] = max(t["have"], n)
            else:
                t["have"] = min(tpl[3], t["have"] + n)
            if before < tpl[3] <= t["have"]:
                self.toast("Задание дня выполнено: " + tpl[1])
                SFX.key()
            hit = True
        if hit:
            SAVE.save()

    def claim_task(self, key):
        for t in SAVE.daily.get("tasks", []):
            tpl = TASK_BY_KEY.get(t["k"])
            if t["k"] != key or not tpl or t["taken"] or t["have"] < tpl[3]:
                continue
            t["taken"] = True
            SAVE.stats["buns"] += tpl[4]
            self.stat("tasks_done")
            self.toast("+%d булок за задание" % tpl[4])
            SFX.win()
            self.save_and_check()
            return

    def dev_digit(self, d):
        if self.code_lock > 0 or len(self.code) >= 4:
            return
        self.code += d
        SFX.tone(600 + len(self.code) * 80, 0.05, "square", 0.25)
        if len(self.code) < 4:
            return
        if code_hash(self.code) == DEV_HASH:
            self.dev_on = True
            self.state = "admin"
            self.code = ""
            self.code_tries = 0
            self.toast("Доступ разработчика открыт")
            SFX.win()
        else:
            self.code = ""
            self.code_bad = 45
            self.code_tries += 1
            self.shake_by(10)
            if self.code_tries >= 3:
                self.code_tries = 0
                self.code_lock = 600
            SFX.hurt()

    def dev_confirm(self, key, msg):
        if self.confirm == key and self.confirm_t > 0:
            self.confirm = None
            self.confirm_t = 0
            return True
        self.confirm = key
        self.confirm_t = 180
        self.toast(msg)
        SFX.hurt()
        return False

    def dev_do(self, what):
        if what not in ("reset", "wipe"):
            self.cheated = True
        if what.startswith("buns"):
            n = int(what[4:])
            SAVE.stats["buns"] += n
            SAVE.save()
            self.toast("+%d булок" % n)
        elif what == "skins":
            for sk in SKINS:
                if not owns(sk[0]):
                    SAVE.stats["owned"].append(sk[0])
            SAVE.save()
            self.toast("Все скины открыты")
        elif what == "upg":
            for u in UPGRADES:
                SAVE.stats["upg"][u[0]] = u[3]
            SAVE.stats["upg_total"] = sum(u[3] for u in UPGRADES)
            SAVE.save()
            self.toast("Все улучшения выданы")
        elif what == "achs":
            for a in ACHS:
                if a[0] not in SAVE.stats["achs"]:
                    SAVE.stats["achs"].append(a[0])
                    SAVE.stats["buns"] += a[5]
            SAVE.save()
            self.toast("Все достижения выданы")
        elif what.startswith("item_"):
            k = what[5:]
            if self.item is None:
                self.item = k
            else:
                self.item2 = k
            self.toast("Выдано: " + ITEMS[k]["n"])
        elif what == "time":
            self.time_left += 60
            self.toast("+60 секунд")
        elif what == "coins":
            if self.level:
                for c in self.level.coins:
                    if not c["got"]:
                        c["got"] = True
                        self.coins += 1
                        self.stat("pies")
                        self.stat("buns")
                SAVE.save()
                self.toast("Все пирожки собраны")
        elif what == "skip":
            if self.state == "admin" and self.back in ("play", "paused") and self.level:
                self.state = "play"
                self.back = None
                self.next_level()
                self.toast("Этаж пропущен")
            else:
                self.toast("Работает только во время забега")
        elif what == "god":
            self.dev_god = not self.dev_god
            self.toast("Бессмертие включено" if self.dev_god else "Бессмертие выключено")
        elif what == "shield":
            self.shield = True
            self.toast("Портфель выдан")
        elif what == "tasks":
            for t in SAVE.daily.get("tasks", []):
                tpl = TASK_BY_KEY.get(t["k"])
                if tpl:
                    t["have"] = tpl[3]
            SAVE.save()
            self.toast("Задания дня выполнены")
        elif what == "reset":
            if not self.dev_confirm("reset", "Сбросить статистику? Нажми ещё раз"):
                return
            SAVE.stats = fresh_stats()
            SAVE.skin = "pupil"
            SAVE.start_item = None
            SAVE.save()
            self.toast("Статистика сброшена")
        elif what == "wipe":
            if not self.dev_confirm("wipe", "Стереть ВЕСЬ прогресс? Нажми ещё раз"):
                return
            SAVE.stats = fresh_stats()
            SAVE.records = {}
            SAVE.mods = {}
            SAVE.skin = "pupil"
            SAVE.start_item = None
            SAVE.daily = fresh_daily()
            SAVE.seed = random_seed()
            SAVE.src = "classic"
            self.dev_god = False
            self.ach_queue = []
            self.ach_t = 0
            SAVE.day_streak()
            SAVE.save()
            self.set_levels()
            self.toast("Прогресс стёрт полностью")
            SFX.bell()

    def claim_daily(self):
        if SAVE.daily.get("reward", 0) <= 0:
            return
        n = SAVE.daily["reward"]
        SAVE.daily["reward"] = 0
        SAVE.stats["buns"] += n
        self.toast("Награда за день: +%d булок" % n)
        SFX.win()
        self.save_and_check()

    def ach_value(self, slot):
        if slot == "skins":
            return len(SAVE.stats["owned"])
        return SAVE.stats.get(slot, 0)

    def save_and_check(self):
        SAVE.save()
        got = 0
        for a in ACHS:
            key, name, _desc, slot, need, prize = a
            if key in SAVE.stats["achs"] or self.ach_value(slot) < need:
                continue
            SAVE.stats["achs"].append(key)
            SAVE.stats["buns"] += prize
            self.ach_queue.append(a)
            got += 1
        if len(self.ach_queue) > 3:
            extra = len(self.ach_queue) - 3
            del self.ach_queue[3:]
            self.toast("и ещё %d достижени%s" % (extra, "я" if extra < 5 else "й"))
        if got:
            SAVE.save()
            SFX.key()

    # ---------- эффекты ----------
    def toast(self, text):
        self.toast_text = text
        self.toast_t = 130

    def puff(self, x, y, n, col, spd=2.5):
        if not SAVE.settings["fancy"]:
            n = max(2, n // 2)
        for _ in range(n):
            self.parts.append({"x": x, "y": y, "vx": random.uniform(-spd, spd),
                               "vy": random.uniform(-spd, spd * 0.4), "life": random.randint(18, 38),
                               "max": 38, "col": col, "s": random.randint(2, 5)})

    def ring(self, x, y, col, r=26):
        self.rings.append({"x": x, "y": y, "t": 0, "life": 18, "col": col, "r": r})

    def pop(self, x, y, text, col=GOLD, size=13):
        self.pops.append({"x": x, "y": y, "str": text, "col": col, "s": size, "t": 0, "life": 44})

    def hitstop(self, n):
        self.hit_stop = max(self.hit_stop, n)

    def shake_by(self, v):
        self.shake = max(self.shake, v)

    # ---------- физика ----------
    def collide_tiles(self, e, axis):
        lv = self.level
        hit = False
        x0 = int(math.floor(e["x"] / TS))
        x1 = int(math.floor((e["x"] + e["w"] - 1) / TS))
        y0 = int(math.floor(e["y"] / TS))
        y1 = int(math.floor((e["y"] + e["h"] - 1) / TS))
        for cy in range(y0, y1 + 1):
            for cx in range(x0, x1 + 1):
                ch = lv.solid_at(cx, cy)
                if not ch:
                    continue
                if ch == "=":                      # доска: снизу пролетаем насквозь
                    if axis == "x" or e["vy"] <= 0:
                        continue
                    if e["y"] + e["h"] - e["vy"] > cy * TS + 4:
                        continue
                hit = True
                if axis == "x":
                    if e["vx"] > 0:
                        e["x"] = min(e["x"], cx * TS - e["w"])
                    elif e["vx"] < 0:
                        e["x"] = max(e["x"], (cx + 1) * TS)
                    e["vx"] = 0
                    e["hit_wall"] = True
                else:
                    if e["vy"] > 0:
                        e["y"] = cy * TS - e["h"]
                        e["grounded"] = True
                    elif e["vy"] < 0:
                        e["y"] = (cy + 1) * TS
                    e["vy"] = 0
        return hit

    def collide_movers(self, e, axis):
        for m in self.level.movers:
            if not (e["x"] < m["x"] + m["w"] and e["x"] + e["w"] > m["x"] and
                    e["y"] < m["y"] + m["h"] and e["y"] + e["h"] > m["y"]):
                continue
            if axis == "x":
                if e["vx"] > 0:
                    e["x"] = m["x"] - e["w"]
                elif e["vx"] < 0:
                    e["x"] = m["x"] + m["w"]
                e["vx"] = 0
            else:
                if e["vy"] > 0 and e["y"] + e["h"] - e["vy"] <= m["y"] + 6:
                    e["y"] = m["y"] - e["h"]
                    e["vy"] = 0
                    e["grounded"] = True
                    e["standing"] = m
                elif e["vy"] < 0:
                    e["y"] = m["y"] + m["h"]
                    e["vy"] = 0

    def update_movers(self):
        for m in self.level.movers:
            m["t"] += m["speed"]
            off = math.sin(m["t"]) * m["dist"]
            nx = m["ox"] + (off if m["axis"] == "x" else 0)
            ny = m["oy"] + (off if m["axis"] == "y" else 0)
            m["dx"], m["dy"] = nx - m["x"], ny - m["y"]
            m["x"], m["y"] = nx, ny

    def hurt_player(self):
        self.hitstop(7)
        if self.shield:
            self.shield = False
            self.invul = 80
            self.player["vy"] = -7
            self.player["vx"] = -3 * self.player["dir"]
            self.puff(self.player["x"] + 10, self.player["y"] + 14, 14, (155, 107, 240), 3)
            self.toast("Портфель принял удар")
            SFX.box()
            return
        self.kill_player()

    def kill_player(self, silent=False):
        p = self.player
        if p["dead"]:
            return
        if self.dev_god and not silent:
            self.invul = 60
            p["vy"] = -6
            return
        if not silent and self.revive_left > 0:          # «Второе дыхание»
            self.revive_left -= 1
            self.invul = 90
            sx, sy = self.level.start
            p["x"], p["y"] = float(sx), float(sy)
            p["vx"] = p["vy"] = 0.0
            p["fall"] = 0.0
            self.cam = self.cam_target()
            self.toast("Второе дыхание! Падение не засчитано")
            self.ring(p["x"] + 10, p["y"] + 14, MINT, 60)
            self.puff(p["x"] + 10, p["y"] + 14, 18, MINT, 3.2)
            SFX.win()
            return
        p["dead"] = True
        p["dead_t"] = 0
        p["vy"] = -7
        p["vx"] = 0
        if not silent:
            self.deaths += 1
            self.stat("falls")
        self.shake_by(14)
        self.puff(p["x"] + 10, p["y"] + 14, 22, (255, 107, 107), 4.5)
        self.ring(p["x"] + 10, p["y"] + 14, (255, 107, 107), 46)
        if not silent:
            self.hitstop(6)
            SFX.hurt()

    def use_item(self):
        if not self.item:
            return
        k = self.item
        self.item = self.item2                    # второй карман подаёт следующий
        self.item2 = None
        self.stat("items")
        if k == "soda":
            self.buff["soda"] = ITEMS[k]["t"]
        elif k == "gum":
            self.buff["gum"] = ITEMS[k]["t"]
        elif k == "pass":
            self.buff["pass"] = ITEMS[k]["t"]
        elif k == "bag":
            self.shield = True
        elif k == "watch":
            self.time_left += 20
        self.toast(ITEMS[k]["n"] + " — " + ITEMS[k]["d"])
        self.puff(self.player["x"] + 10, self.player["y"] + 14, 12, ITEMS[k]["c"], 2.4)
        SFX.box()

    def ring_bell(self):
        p = self.player
        for b in self.level.bells:
            if b["used"]:
                continue
            if overlap({"x": p["x"], "y": p["y"], "w": p["w"], "h": p["h"]}, b):
                b["used"] = True
                self.stat("bells")
                for e in self.level.enemies:
                    e["froze"] = 240
                self.toast("Звонок! Завучи замерли")
                self.ring(b["x"] + 10, b["y"] + 12, GOLD, 90)
                SFX.bell()
                return True
        return False

    def update_player(self):
        p, lv = self.player, self.level
        if not p or not lv:
            return
        if p["dead"]:
            p["dead_t"] += 1
            p["vy"] = min(p["vy"] + GRAV, MAXFALL)
            p["y"] += p["vy"]
            if p["dead_t"] > 46:
                if self.one_life():
                    self.go_over("dead")
                    SFX.fail()
                else:
                    self.spawn_player()
            return
        if p["spawn_t"] > 0:
            p["spawn_t"] -= 1

        if p["standing"]:
            p["x"] += p["standing"]["dx"]
            p["y"] += p["standing"]["dy"]
        p["standing"] = None
        p["grounded"] = False
        p["hit_wall"] = False

        ix = (1 if KEYS["right"] else 0) - (1 if KEYS["left"] else 0)
        if mod("mirror"):
            ix = -ix
        slip = mod("ice")
        acc = 0.42 if slip else 0.85
        if ix:
            p["vx"] += acc * ix
            p["dir"] = ix
        else:
            p["vx"] *= 0.975 if (p["grounded"] and slip) else 0.80
            if abs(p["vx"]) < 0.06:
                p["vx"] = 0.0
        p["vx"] = clamp(p["vx"], -self.run_max(), self.run_max())

        p["vy"] = min(p["vy"] + GRAV, MAXFALL)
        if p["coyote"] > 0:
            p["coyote"] -= 1
        if p["jump_buf"] > 0:
            p["jump_buf"] -= 1

        if p["jump_buf"] > 0 and p["coyote"] > 0:
            p["vy"] = self.jump_v()
            p["jump_buf"] = 0
            p["coyote"] = 0
            p["jumping"] = True
            p["sqx"], p["sqy"] = 0.78, 1.28
            self.puff(p["x"] + 10, p["y"] + p["h"], 6, WHITE, 1.8)
            self.ring(p["x"] + 10, p["y"] + p["h"], (255, 255, 255), 16)
            self.stat("jumps")
            SFX.jump()
        elif p["jump_buf"] > 0 and not p["grounded"] and p["air"] > 0 and self.can_double():
            p["vy"] = self.jump_v() * 0.92
            p["jump_buf"] = 0
            p["air"] -= 1
            p["jumping"] = True
            p["sqx"], p["sqy"] = 0.8, 1.25
            self.puff(p["x"] + 10, p["y"] + p["h"], 10, (255, 159, 243), 2.4)
            self.stat("jumps")
            SFX.jump()
        if p["jumping"] and not KEYS["jump"] and p["vy"] < -4.2:
            p["vy"] = -4.2
            p["jumping"] = False

        p["x"] += p["vx"]
        self.collide_tiles(p, "x")
        self.collide_movers(p, "x")
        was_air = not p["grounded"]
        p["y"] += p["vy"]
        self.collide_tiles(p, "y")
        self.collide_movers(p, "y")

        if p["grounded"]:
            p["jumping"] = False
            p["air"] = 1 if self.can_double() else 0
            p["coyote"] = self.diff["coyote"]
            if was_air and p["fall"] > 7:
                hard = min(1.0, (p["fall"] - 7) / 6.0)
                p["sqx"], p["sqy"] = 1.22 + 0.2 * hard, 0.8 - 0.14 * hard
                self.puff(p["x"] + 10, p["y"] + p["h"], 6 + int(10 * hard), WHITE, 1.6 + 1.6 * hard)
                self.ring(p["x"] + 10, p["y"] + p["h"], (255, 255, 255), 20 + 22 * hard)
                self.shake_by(3 + 4 * hard)
                if hard > 0.4:
                    SFX.tone(150, 0.07, "square", 0.25 * hard, -60)
            elif p["sqy"] > 1:
                p["sqx"], p["sqy"] = 1.22, 0.8
                self.puff(p["x"] + 10, p["y"] + p["h"], 5, WHITE, 1.6)
            p["fall"] = 0.0
        else:
            p["fall"] = max(p["fall"], p["vy"])
        p["sqx"] += (1 - p["sqx"]) * 0.18
        p["sqy"] += (1 - p["sqy"]) * 0.18
        p["anim"] += abs(p["vx"]) * 0.22

        if SAVE.settings["fancy"] and abs(p["vx"]) > 3.4 and p["grounded"] and self.tick % 3 == 0:
            self.trail.append({"x": p["x"], "y": p["y"], "w": p["w"], "h": p["h"],
                               "col": SKYBLUE, "life": 10, "max": 10})

        if mod("glass") and p["grounded"]:                  # «Стеклянные доски»
            fy = int((p["y"] + p["h"] + 1) // TS)
            for cc in range(int((p["x"] + 2) // TS), int((p["x"] + p["w"] - 2) // TS) + 1):
                if 0 <= fy < lv.h and 0 <= cc < lv.w and lv.grid[fy][cc] == "=":
                    if (cc, fy) not in lv.crack and (cc, fy) not in lv.broke:
                        lv.crack[(cc, fy)] = 34

        for pad in lv.pads:
            if pad["t"] > 0:
                pad["t"] -= 1
            if p["vy"] >= 0 and overlap(p, pad) and p["y"] + p["h"] <= pad["y"] + 14:
                p["y"] = pad["y"] - p["h"]
                p["vy"] = PAD_V
                p["coyote"] = 0
                p["jumping"] = False
                p["fall"] = 0
                pad["t"] = 14
                p["sqx"], p["sqy"] = 0.7, 1.4
                self.puff(pad["x"] + pad["w"] / 2, pad["y"], 10, (126, 247, 192), 3)
                self.ring(pad["x"] + pad["w"] / 2, pad["y"], (126, 247, 192), 34)
                self.shake_by(4)
                self.stat("pads")
                SFX.pad()

        body = {"x": p["x"] + 3, "y": p["y"] + 4, "w": p["w"] - 6, "h": p["h"] - 4}
        if self.invul <= 0:
            for sp in lv.spikes:
                if overlap(body, {"x": sp.x, "y": sp.y, "w": sp.w, "h": sp.h}):
                    self.hurt_player()
                    return

        if p["y"] > lv.h * TS + 40:
            self.kill_player()
            return

        for c in lv.coins:
            if c["got"]:
                continue
            c["ph"] += 0.09
            mr = self.magnet_range()
            if mr > 0:
                dx = (p["x"] + p["w"] / 2) - (c["x"] + 8)
                dy = (p["y"] + p["h"] / 2) - (c["y"] + 8)
                dist = math.hypot(dx, dy)
                if 1 < dist < mr:
                    c["x"] += dx / dist * 3.4
                    c["y"] += dy / dist * 3.4
            if overlap(p, c):
                c["got"] = True
                self.coins += 1
                self.stat("pies")
                self.stat("buns")
                self.combo = min(5, self.combo + 1) if self.combo_t > 0 else 1
                self.combo_t = 110
                self.combo_pts += 10 * (self.combo - 1)
                if self.combo > SAVE.stats["max_combo"]:
                    SAVE.stats["max_combo"] = self.combo
                if self.combo > 1:
                    self.toast("×%d подряд" % self.combo)
                self.task_bump("pies")
                self.task_bump("combo", self.combo)
                self.pop(c["x"] + 8, c["y"] + 2, "+%d" % (10 * self.combo),
                         MINT if self.combo > 1 else GOLD, 12 + self.combo)
                self.puff(c["x"] + 8, c["y"] + 8, 10, GOLD, 2.6)
                self.ring(c["x"] + 8, c["y"] + 8, GOLD, 18)
                SFX.coin(self.combo)

        for lk in lv.lockers:
            free = (self.item is None) or (upg("pockets") and self.item2 is None)
            if lk["open"] or not free:
                continue
            if not overlap(p, lk):
                continue
            lk["open"] = True
            lk["t"] = 16
            if self.item is None:
                self.item = lk["item"]
            else:
                self.item2 = lk["item"]
            self.stat("lockers")
            self.task_bump("lockers")
            got = lk["item"]
            self.toast(ITEMS[got]["n"] + " — " + ITEMS[got]["d"])
            self.pop(lk["x"] + 13, lk["y"], ITEMS[got]["n"], ITEMS[got]["c"], 12)
            self.puff(lk["x"] + 13, lk["y"] + 14, 12, ITEMS[got]["c"], 2.6)
            SFX.box()

        if lv.key and not lv.key["got"]:
            lv.key["ph"] += 0.08
            if overlap(p, lv.key):
                lv.key["got"] = True
                self.has_key = True
                self.flash = 12
                self.stat("keys")
                self.task_bump("keys")
                self.pop(lv.key["x"] + 8, lv.key["y"], "КЛЮЧ!", (255, 224, 102), 14)
                self.puff(lv.key["x"] + 8, lv.key["y"] + 7, 16, (255, 224, 102), 3)
                self.ring(lv.key["x"] + 8, lv.key["y"] + 7, (255, 224, 102), 40)
                self.hitstop(4)
                SFX.key()

        for en in lv.enemies:
            if en["dead"] or not overlap(body, en):
                continue
            if self.buff["pass"] > 0 or self.invul > 0:
                continue
            if not en["fly"] and not mod("nostomp") and p["vy"] > 1.2 and (p["y"] + p["h"]) - en["y"] < 18:
                en["dead"] = True
                en["dead_t"] = 0
                self.stat("stomps")
                self.task_bump("stomps")
                p["vy"] = -8.4
                p["sqx"], p["sqy"] = 1.2, 0.82
                p["fall"] = 0
                self.shake_by(9)
                self.pop(en["x"] + 13, en["y"], "БАМ!", WHITE, 15)
                self.puff(en["x"] + 13, en["y"] + 14, 16, (200, 214, 229), 3.4)
                self.ring(en["x"] + 13, en["y"] + 14, WHITE, 34)
                self.hitstop(5)
                SFX.stomp()
            else:
                self.hurt_player()
                return

        if lv.door_hit and self.door_open():
            if (p["x"] < lv.door_hit.right and p["x"] + p["w"] > lv.door_hit.left and
                    p["y"] < lv.door_hit.bottom and p["y"] + p["h"] > lv.door_hit.top):
                self.ring(lv.door.centerx, lv.door.y + 20, MINT, 60)
                self.hitstop(6)
                self.next_level()

    def update_enemies(self):
        lv = self.level
        p = self.player
        for en in lv.enemies:
            if en["dead"]:
                en["dead_t"] += 1
                continue
            if en["froze"] > 0:
                en["froze"] -= 1
                continue
            if en["fly"]:
                en["ph"] += 0.05
                en["x"] += en["vx"]
                if en["x"] < 0 or en["x"] + en["w"] > lv.w * TS:
                    en["vx"] *= -1
                en["y"] = en["base"] + math.sin(en["ph"]) * 14
                continue
            en["vy"] = min(en["vy"] + GRAV, MAXFALL)
            en["x"] += en["vx"]
            en["hit_wall"] = False
            self.collide_tiles(en, "x")
            if en.get("hit_wall") or abs(en["x"] - en["home_x"]) > en["range"]:
                en["vx"] *= -1
                en["x"] += en["vx"] * 2
            en["grounded"] = False
            en["y"] += en["vy"]
            self.collide_tiles(en, "y")
            if mod("jumpy") and en["grounded"] and random.random() < 0.012:
                en["vy"] = -8.0
            ahead = int((en["x"] + (en["w"] if en["vx"] > 0 else 0)) // TS)
            below = int((en["y"] + en["h"] + 2) // TS)
            if en["grounded"] and not lv.solid_at(ahead, below):
                en["vx"] *= -1

    def update_balls(self):
        lv, p = self.level, self.player
        if not p:
            return
        for bl in lv.balls:
            if bl["cool"] > 0:
                bl["cool"] -= 1
            bl["vy"] = min(bl["vy"] + GRAV * 0.8, 12)
            bl["x"] += bl["vx"]
            self.collide_tiles(bl, "x")
            bl["grounded"] = False
            bl["y"] += bl["vy"]
            self.collide_tiles(bl, "y")
            if bl.get("grounded"):
                bl["vx"] *= 0.94
            if abs(bl["vx"]) < 0.05:
                bl["vx"] = 0.0
            if bl["cool"] <= 0 and overlap(p, bl):
                d = 1 if (p["x"] + p["w"] / 2) < (bl["x"] + bl["w"] / 2) else -1
                bl["vx"] = d * (4 + abs(p["vx"]) * 1.3)
                bl["vy"] = -3
                bl["cool"] = 10
                SFX.tone(300, 0.06, "square", 0.3, 120)
            for en in lv.enemies:
                if en["dead"] or abs(bl["vx"]) < 1.5:
                    continue
                if overlap(bl, en):
                    en["dead"] = True
                    en["dead_t"] = 0
                    self.bonus_pts += 20
                    self.stat("goals")
                    self.task_bump("goals")
                    self.pop(en["x"] + 13, en["y"], "ГОООЛ! +20", GOLD, 15)
                    self.puff(en["x"] + 13, en["y"] + 14, 16, GOLD, 3.4)
                    self.shake_by(8)
                    SFX.stomp()

    def tick_glass(self):
        lv = self.level
        for k in list(lv.crack.keys()):
            lv.crack[k] -= 1
            if lv.crack[k] <= 0:
                del lv.crack[k]
                lv.broke[k] = 220
                self.puff(k[0] * TS + 16, k[1] * TS + 7, 10, (214, 161, 90), 2.6)
                self.stat("glass")
                SFX.tone(200, 0.1, "square", 0.3, -90)
        for k in list(lv.broke.keys()):
            lv.broke[k] -= 1
            if lv.broke[k] <= 0:
                del lv.broke[k]

    def update_parts(self):
        for q in self.parts[:]:
            q["x"] += q["vx"]
            q["y"] += q["vy"]
            q["vy"] += 0.14
            q["vx"] *= 0.98
            q["life"] -= 1
            if q["life"] <= 0:
                self.parts.remove(q)
        for o in self.pops[:]:
            o["t"] += 1
            o["y"] -= 1.35 - min(1.0, o["t"] / 22.0)
            if o["t"] >= o["life"]:
                self.pops.remove(o)
        for r in self.rings[:]:
            r["t"] += 1
            if r["t"] >= r["life"]:
                self.rings.remove(r)
        for t in self.trail[:]:
            t["life"] -= 1
            if t["life"] <= 0:
                self.trail.remove(t)

    # ---------- общий шаг ----------
    def update(self, dt):
        self.tick += 1
        if self.hit_stop > 0:
            self.hit_stop -= 1
            self.shake *= 0.92
            return
        if self.shake > 0:
            self.shake *= 0.88
        if self.flash > 0:
            self.flash -= 1
        if self.toast_t > 0:
            self.toast_t -= 1
        if self.hot_t > 0:
            self.hot_t -= 1
        if self.code_bad > 0:
            self.code_bad -= 1
        if self.code_lock > 0:
            self.code_lock -= 1
        if self.secret_t > 0:
            self.secret_t -= 1
        if self.confirm_t > 0:
            self.confirm_t -= 1
            if self.confirm_t == 0:
                self.confirm = None
        if self.invul > 0:
            self.invul -= 1
        if self.ach_t > 0:
            self.ach_t -= 1
        elif self.ach_queue:
            self.ach_show = self.ach_queue.pop(0)
            self.ach_t = 150

        if self.state == "lesson":
            self.lesson_update()
            self.update_parts()
            return
        if self.state == "clear":
            self.clear_t -= 1
            if self.clear_t <= 0:
                self.after_clear()
            self.update_parts()
            return
        if self.state != "play":
            self.update_parts()
            return

        if self.combo_t > 0:
            self.combo_t -= 1
            if self.combo_t == 0:
                self.combo = 0
        for k in self.buff:
            if self.buff[k] > 0:
                self.buff[k] -= 1
        self.tick_glass()
        self.update_balls()
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            self.go_over("bell")
            SFX.bell()
            self.shake_by(20)
            return
        self.update_movers()
        self.update_player()
        self.update_enemies()
        self.update_parts()
        self.cam += (self.cam_target() - self.cam) * 0.14

    # ---------- уроки ----------
    def start_lesson(self):
        self.lesson_left = 2 if mod("dbllesson") else 1
        self.open_lesson()

    def open_lesson(self):
        kind = random.choice(["quiz", "quiz", "sleep", "copy", "dict", "canteen", "pushups"])
        strict = mod("strict")
        subject = random.choice(["Математика", "Русский язык", "История", "Физика",
                                 "Биология", "География", "Литература", "Геометрия"])
        if kind == "quiz":
            qs = random.sample(QUIZ, 3)
            mixed = []
            for q, opts, right in qs:
                order = list(range(3))
                random.shuffle(order)                 # ответы не стоят на одном месте
                mixed.append({"q": q, "opts": [opts[i] for i in order],
                              "r": order.index(right)})
            need = 3 if mod("exam") else (1 if mod("easyclass") else 2)
            self.lesson = {"kind": "quiz", "subject": subject, "qs": mixed, "qi": 0,
                           "right": 0, "need": need, "pick": -1, "pick_t": 0,
                           "limit": (6 if strict else 9) * 60, "done": False, "end_t": 0}
        elif kind == "sleep":
            self.lesson = {"kind": "sleep", "subject": subject, "eye": 100.0,
                           "limit": (16 if strict else 22) * 60, "done": False,
                           "end_t": 0, "need": 0}
        elif kind == "copy":
            self.lesson = {"kind": "copy", "subject": subject, "phase": "away",
                           "t": 90, "fill": 0.0, "strikes": 0,
                           "max_strikes": 1 if mod("exam") else (4 if mod("easyclass") else 3),
                           "limit": (18 if strict else 26) * 60, "done": False, "end_t": 0}
        elif kind == "dict":
            need = 12 if mod("exam") else (6 if mod("easyclass") else 8)
            self.lesson = {"kind": "dict", "subject": subject, "arrows": [], "hits": 0,
                           "miss": 0, "need": need, "spawn": 0, "shown": 0,
                           "limit": (16 if strict else 22) * 60, "done": False, "end_t": 0}
        elif kind == "canteen":
            need = 12 if mod("exam") else (5 if mod("easyclass") else 8)
            self.lesson = {"kind": "canteen", "subject": "Большая перемена", "drops": [],
                           "tray": VW / 2.0, "got": 0, "need": need, "left": need + 6,
                           "spawn": 0, "limit": (16 if strict else 24) * 60,
                           "done": False, "end_t": 0}
        else:
            need = 16 if mod("exam") else (9 if mod("easyclass") else 13)
            self.lesson = {"kind": "pushups", "subject": "Физкультура", "reps": 0,
                           "need": need, "nxt": "left", "down": 0,
                           "limit": (16 if strict else 22) * 60, "done": False, "end_t": 0}
        self.state = "lesson"

    def lesson_answer(self, n):
        L = self.lesson
        if not L or L["kind"] != "quiz" or L["done"] or L["pick_t"] > 0:
            return
        if L["qi"] >= len(L["qs"]):
            return
        q = L["qs"][L["qi"]]
        L["pick"] = n
        L["pick_t"] = 45
        if n == q["r"]:
            L["right"] += 1
            self.stat("quiz_ok")
            SFX.coin()
        else:
            self.shake_by(5)
            SFX.hurt()

    def lesson_press(self, what="jump"):
        L = self.lesson
        if not L or L["done"]:
            return
        if L["kind"] == "sleep" and what == "jump":
            L["eye"] = min(100.0, L["eye"] + 7)
            self.puff(VW / 2, 330, 3, MINT, 2)
            SFX.tone(420 + int(L["eye"]), 0.04, "square", 0.2)
        elif L["kind"] == "dict" and what in ("left", "right"):
            best, bd = None, 999
            for a in L["arrows"]:
                d = abs(a["x"] - 400)
                if d < bd:
                    best, bd = a, d
            if best and bd < 46 and best["dir"] == what:
                L["arrows"].remove(best)
                L["hits"] += 1
                self.puff(400, 300, 6, MINT, 2.4)
                SFX.coin()
                if L["hits"] >= L["need"]:
                    self.lesson_end(True)
            else:
                L["miss"] += 1
                self.shake_by(5)
                SFX.hurt()
        elif L["kind"] == "pushups" and what in ("left", "right"):
            if what == L["nxt"]:
                L["reps"] += 1
                L["down"] = 12
                L["nxt"] = "right" if what == "left" else "left"
                self.puff(VW / 2, 330, 4, MINT, 2)
                SFX.tone(300 + (L["reps"] % 6) * 30, 0.06, "square", 0.25, 80)
                if L["reps"] >= L["need"]:
                    self.lesson_end(True)
            else:
                self.shake_by(5)
                SFX.hurt()

    def lesson_update(self):
        L = self.lesson
        if not L:
            self.state = "play"
            return
        if L["done"]:
            L["end_t"] -= 1
            if L["end_t"] <= 0:
                self.lesson_left -= 1
                if self.lesson_left > 0:
                    self.open_lesson()
                else:
                    self.lesson = None
                    self.state = "play"
            return
        L["limit"] -= 1
        if L["kind"] == "quiz":
            if L["pick_t"] > 0:
                L["pick_t"] -= 1
                if L["pick_t"] == 0:
                    L["qi"] += 1
                    L["pick"] = -1
                    L["limit"] = (6 if mod("strict") else 9) * 60
                    if L["qi"] >= len(L["qs"]):
                        self.lesson_end(L["right"] >= L["need"])
                return
            if L["limit"] <= 0:
                L["pick"] = -1
                L["pick_t"] = 20
        elif L["kind"] == "sleep":
            L["eye"] -= 0.22 if mod("strict") else 0.16
            if L["eye"] <= 0:
                self.lesson_end(False)
            elif L["limit"] <= 0:
                self.lesson_end(True)
        elif L["kind"] == "copy":
            L["t"] -= 1
            if L["t"] <= 0:                       # учитель то пишет, то оборачивается
                if L["phase"] == "away":
                    L["phase"] = "turn"
                    L["t"] = 26 if mod("strict") else 34
                elif L["phase"] == "turn":
                    L["phase"] = "watch"
                    L["t"] = random.randint(60, 130)
                else:
                    L["phase"] = "away"
                    L["t"] = random.randint(70, 150)
            if KEYS["jump"]:
                if L["phase"] == "away":
                    L["fill"] = min(100.0, L["fill"] + (0.42 if mod("strict") else 0.55))
                    if self.tick % 6 == 0:
                        self.puff(VW / 2 + 40, 250, 2, SKYBLUE, 1.6)
                elif L["phase"] == "watch":
                    L["strikes"] += 1
                    L["fill"] = max(0.0, L["fill"] - 6)
                    self.shake_by(6)
                    SFX.hurt()
                    if L["strikes"] >= L["max_strikes"] * 12:
                        self.lesson_end(False)
            if L["fill"] >= 100:
                self.lesson_end(True)
            elif L["limit"] <= 0:
                self.lesson_end(False)
        elif L["kind"] == "dict":
            L["spawn"] -= 1
            if L["spawn"] <= 0 and L["shown"] < L["need"] + 4:
                L["shown"] += 1
                L["spawn"] = 48 if mod("strict") else 62
                L["arrows"].append({"x": -40.0, "dir": random.choice(["left", "right"])})
            for a in L["arrows"][:]:
                a["x"] += 3.6 if mod("strict") else 3.0
                if a["x"] > VW + 40:
                    L["arrows"].remove(a)
                    L["miss"] += 1
            if L["limit"] <= 0 or (L["shown"] >= L["need"] + 4 and not L["arrows"]):
                self.lesson_end(L["hits"] >= L["need"])
        elif L["kind"] == "canteen":
            if KEYS["left"]:
                L["tray"] -= 6.5
            if KEYS["right"]:
                L["tray"] += 6.5
            L["tray"] = clamp(L["tray"], 60, VW - 60)
            L["spawn"] -= 1
            if L["spawn"] <= 0 and L["left"] > 0:
                L["left"] -= 1
                L["spawn"] = 34 if mod("strict") else 44
                bad = random.random() < (0.3 if mod("strict") else 0.18)
                L["drops"].append({"x": random.uniform(70, VW - 70), "y": -20.0,
                                   "bad": bad, "v": random.uniform(2.6, 4.0)})
            for d in L["drops"][:]:
                d["y"] += d["v"]
                if abs(d["x"] - L["tray"]) < 52 and 352 < d["y"] < 386:
                    L["drops"].remove(d)
                    if d["bad"]:
                        L["got"] = max(0, L["got"] - 1)
                        self.shake_by(5)
                        SFX.hurt()
                    else:
                        L["got"] += 1
                        self.puff(d["x"], 360, 6, GOLD, 2.4)
                        SFX.coin()
                        if L["got"] >= L["need"]:
                            self.lesson_end(True)
                elif d["y"] > VH:
                    L["drops"].remove(d)
            if L["limit"] <= 0 or (L["left"] <= 0 and not L["drops"]):
                self.lesson_end(L["got"] >= L["need"])
        elif L["kind"] == "pushups":
            if L["down"] > 0:
                L["down"] -= 1
            if L["limit"] <= 0:
                self.lesson_end(L["reps"] >= L["need"])

    def lesson_end(self, ok):
        L = self.lesson
        L["done"] = True
        L["ok"] = ok
        L["end_t"] = 110
        if ok:
            bonus = 30 if mod("favorite") else 15
            pts = 200 if mod("favorite") else 100
            self.time_left += bonus
            self.bonus_pts += pts
            self.stat("lessons_ok")
            self.task_bump("lessons")
            SFX.win()
        else:
            self.time_left = max(1, self.time_left - 10)
            self.stat("lessons_bad")
            SFX.fail()
        self.save_and_check()


KEYS = {"left": False, "right": False, "jump": False}


# ================== РИСОВАНИЕ ==================
FONTS = {}
TEXT_CACHE = {}
SURF_CACHE = {}
FONT_NAME = None


def pick_font():
    global FONT_NAME
    for name in ("dejavusans", "liberationsans", "freesans", "arial", "segoeui", "verdana"):
        if name in pygame.font.get_fonts():
            FONT_NAME = name
            return
    FONT_NAME = None


def font(size, bold=True):
    key = (int(size), bold)
    f = FONTS.get(key)
    if f is None:
        if FONT_NAME:
            f = pygame.font.SysFont(FONT_NAME, int(size), bold=bold)
        else:
            f = pygame.font.Font(None, int(size * 1.25))
        FONTS[key] = f
    return f


def text_surf(msg, size, col, bold=True):
    key = (msg, int(size), col, bold)
    s = TEXT_CACHE.get(key)
    if s is None:
        s = font(size, bold).render(msg, True, col)
        if len(TEXT_CACHE) > 900:
            TEXT_CACHE.clear()
        TEXT_CACHE[key] = s
    return s


def draw_text(dst, msg, x, y, size, col, align="left", bold=True, shadow=False):
    s = text_surf(msg, size, col, bold)
    r = s.get_rect()
    if align == "center":
        r.midtop = (int(x), int(y))
    elif align == "right":
        r.topright = (int(x), int(y))
    else:
        r.topleft = (int(x), int(y))
    if shadow:
        dst.blit(text_surf(msg, size, (0, 0, 0), bold), (r.x + 2, r.y + 2))
    dst.blit(s, r)
    return r


def fit_text(dst, msg, x, y, size, col, max_w, align="left", bold=True):
    while size > 8 and text_surf(msg, size, col, bold).get_width() > max_w:
        size -= 1
    return draw_text(dst, msg, x, y, size, col, align, bold)


def rrect(dst, col, rect, rad=10, width=0):
    pygame.draw.rect(dst, col, rect, width, border_radius=int(rad))


def vgrad(key, w, h, top, bottom):
    """Вертикальный градиент кэшируется картинкой — как в браузерной версии."""
    s = SURF_CACHE.get(key)
    if s is not None:
        return s
    s = pygame.Surface((w, h)).convert()
    for i in range(h):
        k = i / float(max(1, h - 1))
        col = tuple(int(top[j] + (bottom[j] - top[j]) * k) for j in range(3))
        pygame.draw.line(s, col, (0, i), (w, i))
    SURF_CACHE[key] = s
    return s


def sky_surface(theme):
    key = "sky" + theme["n"]
    s = SURF_CACHE.get(key)
    if s is not None:
        return s
    s = pygame.Surface((VW, VH)).convert()
    a, b, c = theme["sky"]
    half = int(VH * 0.45)
    for i in range(VH):
        if i < half:
            k = i / float(half)
            col = tuple(int(a[j] + (b[j] - a[j]) * k) for j in range(3))
        else:
            k = (i - half) / float(VH - half)
            col = tuple(int(b[j] + (c[j] - b[j]) * k) for j in range(3))
        pygame.draw.line(s, col, (0, i), (VW, i))
    SURF_CACHE[key] = s
    return s


def day_tint():
    h = time.localtime().tm_hour
    if 5 <= h < 9:
        return (255, 196, 120, 40)
    if 17 <= h < 20:
        return (255, 150, 80, 50)
    if h >= 20 or h < 5:
        return (20, 32, 80, 105)
    return None


def deco_surface(theme, w):
    """Задник уровня: рисуется один раз на всю ширину и потом просто копируется."""
    key = "deco%s_%d" % (theme["n"], w)
    s = SURF_CACHE.get(key)
    if s is not None:
        return s
    s = pygame.Surface((w, VH), pygame.SRCALPHA)
    deco = theme["deco"]
    rnd = mulberry(hash_seed(theme["n"]))
    if deco == "yard":
        pygame.draw.circle(s, (255, 244, 189), (int(w * 0.82), 78), 26)
        for i in range(w // 380 + 2):
            x = i * 380 + 40
            pygame.draw.rect(s, (95, 127, 168), (x, VH - 340, 250, 190))
            pygame.draw.rect(s, (78, 107, 145), (x - 14, VH - 358, 278, 22))
            for wy in range(4):
                for wx in range(5):
                    pygame.draw.rect(s, (255, 240, 180, 140),
                                     (x + 22 + wx * 44, VH - 314 + wy * 42, 26, 26))
        pygame.draw.rect(s, (210, 236, 247, 128), (0, VH - 150, w, 150))
        for i in range(w // 170 + 2):
            x = i * 170 + 60
            pygame.draw.rect(s, (107, 74, 47), (x - 6, VH - 120, 12, 70))
            col = (63, 155, 90) if i % 2 else (53, 138, 79)
            pygame.draw.circle(s, col, (x, VH - 126), 34)
            pygame.draw.circle(s, col, (x - 26, VH - 110), 24)
            pygame.draw.circle(s, col, (x + 26, VH - 110), 24)
    elif deco == "hall":
        pygame.draw.rect(s, (62, 90, 117), (0, 0, w, VH - 120))
        pygame.draw.rect(s, (77, 109, 140), (0, VH - 260, w, 140))
        for i in range(w // 300 + 2):
            x = i * 300 + 30
            pygame.draw.rect(s, (107, 74, 47), (x, VH - 320, 74, 170), border_radius=4)
            pygame.draw.rect(s, (125, 91, 60), (x + 5, VH - 315, 64, 160), border_radius=3)
            pygame.draw.rect(s, (232, 238, 247), (x + 22, VH - 306, 30, 18), border_radius=2)
            draw_text(s, str(101 + i % 18), x + 37, VH - 304, 11, (43, 56, 80), "center")
        for i in range(w // 150 + 2):
            x = i * 150 + 20
            if i % 2:
                continue
            pygame.draw.rect(s, (94, 127, 156), (x, VH - 250, 58, 100), border_radius=3)
            pygame.draw.rect(s, (44, 58, 73), (x + 8, VH - 238, 12, 3))
            pygame.draw.rect(s, (44, 58, 73), (x + 38, VH - 238, 12, 3))
    elif deco == "canteen":
        pygame.draw.rect(s, (200, 168, 135), (0, 0, w, VH - 130))
        for i in range(w // 48 + 2):
            for r in range(4):
                col = (230, 211, 186) if (i + r) % 2 else (220, 198, 169)
                pygame.draw.rect(s, col, (i * 48, 40 + r * 46, 44, 42))
        for i in range(w // 520 + 2):
            x = i * 520 + 40
            pygame.draw.rect(s, (154, 167, 180), (x, VH - 300, 260, 26), border_radius=4)
            pygame.draw.rect(s, (125, 139, 153), (x + 8, VH - 274, 244, 124))
        for i in range(w // 210 + 2):
            x = i * 210 + 20
            pygame.draw.rect(s, (185, 131, 74), (x, VH - 206, 150, 12), border_radius=3)
            pygame.draw.rect(s, (138, 97, 53), (x + 16, VH - 194, 10, 56))
            pygame.draw.rect(s, (138, 97, 53), (x + 124, VH - 194, 10, 56))
    elif deco == "gym":
        pygame.draw.rect(s, (109, 127, 150), (0, 0, w, VH - 130))
        pygame.draw.rect(s, (125, 143, 166), (0, VH - 280, w, 150))
        for i in range(w // 240 + 2):
            if i % 2:
                continue
            x = i * 240 + 30
            pygame.draw.rect(s, (201, 160, 106), (x, VH - 360, 10, 210))
            pygame.draw.rect(s, (201, 160, 106), (x + 96, VH - 360, 10, 210))
            for r in range(9):
                pygame.draw.rect(s, (217, 180, 126), (x + 10, VH - 350 + r * 23, 86, 7))
    elif deco == "library":
        pygame.draw.rect(s, (74, 52, 39), (0, 0, w, VH - 120))
        cols = [(192, 57, 43), (47, 143, 91), (47, 111, 159), (201, 160, 76), (122, 78, 196)]
        for i in range(w // 176 + 2):
            x = i * 176 + 10
            pygame.draw.rect(s, (93, 68, 48), (x, VH - 390, 160, 250))
            pygame.draw.rect(s, (62, 45, 32), (x + 6, VH - 384, 148, 238))
            for r in range(5):
                by = VH - 380 + r * 47
                pygame.draw.rect(s, (107, 79, 56), (x + 6, by + 38, 148, 6))
                for q in range(11):
                    hh = 22 + int(rnd() * 14)
                    pygame.draw.rect(s, cols[int(rnd() * len(cols))],
                                     (x + 10 + q * 13, by + 38 - hh, 10, hh))
    elif deco == "boiler":
        pygame.draw.rect(s, (27, 36, 48), (0, 0, w, VH - 120))
        for i in range(w // 64 + 2):
            for r in range(7):
                col = (36, 48, 64) if (i + r) % 2 else (32, 43, 57)
                pygame.draw.rect(s, col, (i * 64 + (16 if r % 2 else 0), 30 + r * 52, 60, 48))
        for i in range(w // 190 + 2):
            x = i * 190 + 20
            pygame.draw.rect(s, (74, 85, 104), (x, VH - 300, 24, 160), border_radius=6)
    else:                                            # крыша
        pygame.draw.circle(s, (255, 217, 160), (int(w * 0.75), 150), 34)
        for i in range(w // 150 + 2):
            hh = 60 + int(rnd() * 120)
            x = i * 150
            pygame.draw.rect(s, (61, 63, 107), (x, VH - 180 - hh, 110, hh + 60))
            for wy in range(hh // 26):
                for wx in range(3):
                    if rnd() > 0.45:
                        pygame.draw.rect(s, (255, 220, 150, 90),
                                         (x + 16 + wx * 32, VH - 170 - hh + wy * 26, 16, 14))
        for i in range(w // 260 + 2):
            x = i * 260 + 30
            pygame.draw.line(s, (57, 69, 92), (x + 30, VH - 150), (x + 30, VH - 260), 3)
            pygame.draw.rect(s, (74, 85, 104), (x + 120, VH - 200, 56, 50), border_radius=5)
    SURF_CACHE[key] = s
    return s


def tiles_surface(lv):
    """Плитки уровня статичны — рисуем их один раз и потом копируем кусок."""
    key = "tiles%s_%d_%d" % (lv.name, lv.w, id(lv) % 100000)
    s = SURF_CACHE.get(key)
    if s is not None:
        return s
    th = lv.theme
    s = pygame.Surface((lv.w * TS, lv.h * TS), pygame.SRCALPHA)
    for cy in range(lv.h):
        for cx in range(lv.w):
            ch = lv.grid[cy][cx]
            if ch not in SOLID:
                continue
            x, y = cx * TS, cy * TS
            open_top = not (cy > 0 and lv.grid[cy - 1][cx] in SOLID)
            if ch == "#":
                pygame.draw.rect(s, th["ground"], (x, y, TS, TS))
                pygame.draw.rect(s, (0, 0, 0, 30), (x, y + TS - 6, TS, 6))
                pygame.draw.rect(s, (255, 255, 255, 18), (x + 3, y + 3, TS - 6, 4))
                pygame.draw.rect(s, (0, 0, 0, 46), (x, y, TS, TS), 1)
                if open_top:
                    pygame.draw.rect(s, th["cap"], (x, y, TS, 9))
                    pygame.draw.rect(s, th["cap2"], (x, y, TS, 4))
                    if th.get("grass"):
                        pygame.draw.rect(s, th["cap"], (x + 4, y - 4, 4, 5))
                        pygame.draw.rect(s, th["cap"], (x + 15, y - 6, 4, 7))
                        pygame.draw.rect(s, th["cap"], (x + 25, y - 3, 4, 4))
            else:
                pygame.draw.rect(s, th["plank"], (x, y, TS, 14))
                pygame.draw.rect(s, th["plank2"], (x, y, TS, 5))
                pygame.draw.rect(s, (0, 0, 0, 50), (x, y + 11, TS, 3))
    if len(SURF_CACHE) > 40:
        for k in [k for k in SURF_CACHE if k.startswith("tiles")][:-6]:
            del SURF_CACHE[k]
    SURF_CACHE[key] = s
    return s


def draw_pie(dst, x, y, s=1.0):
    pygame.draw.ellipse(dst, (232, 163, 61), (x - 11 * s, y - 8 * s, 22 * s, 16 * s))
    pygame.draw.ellipse(dst, (247, 198, 107), (x - 10 * s, y - 8 * s, 18 * s, 12 * s))


def draw_character(dst, x, y, w, h, skin_key, face=1, anim=0.0, alpha=255):
    """Человечек: тот же набор деталей, что и в браузерной версии."""
    sk = SKIN_BY_KEY.get(skin_key, SKINS[0])
    _k, _n, _d, shirt, hair, acc, _price = sk
    body = pygame.Surface((w + 16, h + 18), pygame.SRCALPHA)
    ox, oy = 8, 10
    step = math.sin(anim) * 3
    pygame.draw.ellipse(body, (0, 0, 0, 60), (ox + 1, oy + h - 3, w - 2, 6))
    pygame.draw.rect(body, (214, 69, 65), (ox + 2, oy + h - 8 + step, 7, 6), border_radius=2)
    pygame.draw.rect(body, (214, 69, 65), (ox + w - 9, oy + h - 8 - step, 7, 6), border_radius=2)
    pygame.draw.rect(body, (47, 62, 86), (ox + 3, oy + h - 16, w - 6, 10), border_radius=2)
    pygame.draw.rect(body, shirt, (ox + 2, oy + 9, w - 4, h - 22), border_radius=4)
    pygame.draw.circle(body, (240, 205, 170), (ox + w // 2, oy + 6), 7)
    pygame.draw.rect(body, hair, (ox + w // 2 - 7, oy - 1, 14, 6), border_radius=3)
    eye = ox + w // 2 + (2 if face > 0 else -4)
    pygame.draw.rect(body, (30, 34, 46), (eye, oy + 4, 2, 3))
    if acc == "cap":
        pygame.draw.rect(body, (192, 57, 43), (ox + w // 2 - 8, oy - 4, 16, 6), border_radius=3)
    elif acc == "bow":
        pygame.draw.circle(body, (255, 105, 180), (ox + w // 2 - 6, oy - 2), 4)
    elif acc == "glasses":
        pygame.draw.rect(body, (40, 44, 58), (ox + w // 2 - 6, oy + 3, 12, 4), 1)
    elif acc == "whistle":
        pygame.draw.circle(body, (255, 209, 102), (ox + w // 2 + 4, oy + 14), 3)
    elif acc == "tie":
        pygame.draw.rect(body, (192, 57, 43), (ox + w // 2 - 1, oy + 10, 3, 9))
    elif acc == "sash":
        pygame.draw.line(body, (255, 209, 102), (ox + 3, oy + 10), (ox + w - 4, oy + 20), 4)
    if alpha < 255:
        body.set_alpha(alpha)
    dst.blit(body, (int(x - ox), int(y - oy)))


def draw_world(surf, g):
    lv = g.level
    th = lv.theme
    cam = int(g.cam)
    shake_k = [0, 0.5, 1][SAVE.settings["shake"]]
    sh = g.shake * shake_k
    ox = int(random.uniform(-sh, sh)) if sh > 0.4 else 0
    oy = int(random.uniform(-sh, sh)) if sh > 0.4 else 0

    surf.blit(sky_surface(th), (0, 0))
    deco = deco_surface(th, max(VW * 2, lv.w * TS))
    surf.blit(deco, (-int(cam * 0.4), 0))
    if th["deco"] in ("yard", "roof"):
        tint = day_tint()
        if tint:
            layer = pygame.Surface((VW, VH), pygame.SRCALPHA)
            layer.fill(tint)
            surf.blit(layer, (0, 0))

    def sx(x):
        return int(x) - cam + ox

    surf.blit(tiles_surface(lv), (-cam + ox, oy), (0, 0, lv.w * TS, lv.h * TS))

    for m in lv.movers:
        pygame.draw.rect(surf, (214, 161, 90), (sx(m["x"]), int(m["y"]) + oy, m["w"], m["h"]),
                         border_radius=6)
        pygame.draw.rect(surf, (240, 194, 127), (sx(m["x"]), int(m["y"]) + oy, m["w"], 5),
                         border_radius=4)
    for sp in lv.spikes:
        for i in range(3):
            bx = sx(sp.x) + i * 9
            pygame.draw.polygon(surf, (206, 217, 230),
                                [(bx, sp.y + sp.h + oy), (bx + 5, sp.y + oy), (bx + 10, sp.y + sp.h + oy)])
    for pad in lv.pads:
        k = 6 if pad["t"] > 0 else 0
        pygame.draw.rect(surf, (126, 247, 192),
                         (sx(pad["x"]), int(pad["y"]) + k + oy, pad["w"], pad["h"] - k), border_radius=5)
    for b in lv.bells:
        col = (120, 130, 140) if b["used"] else GOLD
        pygame.draw.rect(surf, col, (sx(b["x"]), int(b["y"]) + oy, b["w"], b["h"]), border_radius=5)
        draw_text(surf, "B", sx(b["x"]) + 10, int(b["y"]) + 4 + oy, 12, INK, "center")
    for lk in lv.lockers:
        col = (94, 127, 156) if not lk["open"] else (70, 95, 118)
        pygame.draw.rect(surf, col, (sx(lk["x"]), int(lk["y"]) + oy, lk["w"], lk["h"]), border_radius=3)
        pygame.draw.line(surf, (30, 40, 52), (sx(lk["x"]) + 13, int(lk["y"]) + 3 + oy),
                         (sx(lk["x"]) + 13, int(lk["y"]) + lk["h"] - 3 + oy), 1)
    for bl in lv.balls:
        pygame.draw.circle(surf, WHITE, (sx(bl["x"]) + 7, int(bl["y"]) + 7 + oy), 7)
        pygame.draw.circle(surf, (40, 50, 65), (sx(bl["x"]) + 7, int(bl["y"]) + 7 + oy), 7, 2)
    for c in lv.coins:
        if c["got"]:
            continue
        draw_pie(surf, sx(c["x"]) + 8, int(c["y"] + math.sin(c["ph"]) * 3) + 8 + oy, 0.8)
    if lv.key and not lv.key["got"]:
        kx, ky = sx(lv.key["x"]), int(lv.key["y"] + math.sin(lv.key["ph"]) * 3) + oy
        pygame.draw.circle(surf, (255, 224, 102), (kx + 6, ky + 6), 6)
        pygame.draw.rect(surf, (255, 224, 102), (kx + 5, ky + 6, 3, 12))
        pygame.draw.rect(surf, (255, 224, 102), (kx + 5, ky + 14, 7, 3))
    if lv.door:
        d = lv.door
        opened = g.door_open()
        pygame.draw.rect(surf, (107, 74, 47), (sx(d.x), d.y + oy, d.w, d.h), border_radius=4)
        pygame.draw.rect(surf, (139, 101, 66) if opened else (80, 60, 45),
                         (sx(d.x) + 3, d.y + 4 + oy, d.w - 6, d.h - 8), border_radius=3)
        pygame.draw.circle(surf, GOLD if opened else (120, 110, 90),
                           (sx(d.x) + d.w - 7, d.y + d.h // 2 + oy), 3)
        if not opened:
            draw_text(surf, "закрыто", sx(d.centerx), d.y - 16 + oy, 10, RED, "center")
    for en in lv.enemies:
        ex, ey = sx(en["x"]), int(en["y"]) + oy
        if en["dead"]:
            if en["dead_t"] < 30:
                pygame.draw.ellipse(surf, (150, 160, 175),
                                    (ex, ey + en["h"] - 6, en["w"], 8))
            continue
        col = (90, 110, 140) if not en["fly"] else (230, 235, 245)
        if en["froze"] > 0:
            col = (120, 170, 210)
        if en["fly"]:
            pygame.draw.polygon(surf, col, [(ex, ey + 9), (ex + 28, ey), (ex + 20, ey + 18)])
        else:
            pygame.draw.rect(surf, col, (ex, ey, en["w"], en["h"]), border_radius=4)
            pygame.draw.rect(surf, (230, 200, 170), (ex + 4, ey - 6, 18, 10), border_radius=4)
            pygame.draw.rect(surf, (40, 48, 62), (ex + 7, ey - 3, 3, 3))
            pygame.draw.rect(surf, (40, 48, 62), (ex + 15, ey - 3, 3, 3))
        if g.buff["pass"] > 0:
            draw_text(surf, "?", ex + 10, ey - 22, 13, SKYBLUE, "center")

    for t in g.trail:
        alpha = int(255 * (t["life"] / float(t["max"])) * 0.3)
        layer = pygame.Surface((t["w"], t["h"]), pygame.SRCALPHA)
        layer.fill((t["col"][0], t["col"][1], t["col"][2], alpha))
        surf.blit(layer, (sx(t["x"]), int(t["y"]) + oy))

    for q in g.parts:
        a = max(0, min(255, int(255 * q["life"] / float(q["max"]))))
        layer = pygame.Surface((q["s"], q["s"]), pygame.SRCALPHA)
        layer.fill((q["col"][0], q["col"][1], q["col"][2], a))
        surf.blit(layer, (sx(q["x"]), int(q["y"]) + oy))

    p = g.player
    if p:
        blink = p["spawn_t"] > 0 and (g.tick // 3) % 2 == 0
        if not blink:
            alpha = 255
            if g.invul > 0 and (g.tick // 4) % 2 == 0:
                alpha = 130
            draw_character(surf, sx(p["x"]), int(p["y"]) + oy, p["w"], p["h"],
                           SAVE.skin, p["dir"], p["anim"], alpha)
        if g.shield:
            pygame.draw.circle(surf, (155, 107, 240), (sx(p["x"]) + 10, int(p["y"]) + 14 + oy), 22, 2)

    for r in g.rings:
        k = r["t"] / float(r["life"])
        rad = int(6 + r["r"] * k)
        a = int(180 * (1 - k))
        if rad > 0 and a > 0:
            layer = pygame.Surface((rad * 2 + 4, rad * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(layer, (r["col"][0], r["col"][1], r["col"][2], a),
                               (rad + 2, rad + 2), rad, max(1, int(3 * (1 - k)) + 1))
            surf.blit(layer, (sx(r["x"]) - rad - 2, int(r["y"]) - rad - 2 + oy))

    for o in g.pops:
        k = o["t"] / float(o["life"])
        size = o["s"] * (0.6 + 0.5 * min(1.0, o["t"] / 7.0))
        col = o["col"]
        s = text_surf(o["str"], int(size), col)
        if k > 0.7:
            s = s.copy()
            s.set_alpha(int(255 * (1 - k) / 0.3))
        surf.blit(s, (sx(o["x"]) - s.get_width() // 2, int(o["y"]) + oy))

    if mod("dark") and p:
        dark = pygame.Surface((VW, VH), pygame.SRCALPHA)
        dark.fill((5, 9, 18, 235))
        lx, ly = sx(p["x"]) + 10, int(p["y"]) + 14
        for rad, a in ((200, 235), (150, 190), (110, 120), (70, 40), (40, 0)):
            pygame.draw.circle(dark, (5, 9, 18, a), (lx, ly), rad)
        surf.blit(dark, (0, 0))
    if g.flash > 0:
        layer = pygame.Surface((VW, VH), pygame.SRCALPHA)
        layer.fill((255, 240, 180, int(g.flash / 12.0 * 90)))
        surf.blit(layer, (0, 0))


# ================== ИНТЕРФЕЙС ==================
def panel(surf, w, h, accent=SKYBLUE):
    x, y = VW // 2 - w // 2, VH // 2 - h // 2
    rr = pygame.Surface((w, h), pygame.SRCALPHA)
    rrect(rr, (10, 17, 33, 252), (0, 0, w, h), 22)
    top = pygame.Surface((w, h // 2), pygame.SRCALPHA)
    top.fill((90, 130, 190, 26))
    rr.blit(top, (0, 0))
    surf.blit(rr, (x, y))
    rrect(surf, (255, 255, 255, 40), (x, y, w, h), 22, 2)
    pygame.draw.line(surf, accent, (x + 28, y + 2), (x + w - 28, y + 2), 2)
    return x, y


def ui_button(surf, g, bid, x, y, w, h, label, sub=None, sel=False, size=18,
              col=WHITE, tint=None, dim=False):
    hov = (not dim) and pygame.Rect(x, y, w, h).collidepoint(g.mouse)
    hot = (g.hot == bid and g.hot_t > 0)
    tint = tint or (MINT if sel else SKYBLUE)
    r = pygame.Rect(x, y + (1 if hot else 0), w, h)
    layer = pygame.Surface((w, h), pygame.SRCALPHA)
    base = 80 if sel else (62 if hov else 40)
    rrect(layer, (255, 255, 255, base), (0, 0, w, h), 14)
    rrect(layer, (255, 255, 255, 56), (6, 3, w - 12, min(12, int(h * 0.3))), 8)
    if dim:
        layer.set_alpha(80)
    surf.blit(layer, r.topleft)
    rrect(surf, tint if (sel or hov) else (255, 255, 255, 70), r, 14, 3 if sel else 1)
    ty = r.y + (h // 2 - size // 2 - (7 if sub else 0))
    draw_text(surf, label, r.centerx, ty, size, col, "center")
    if sub:
        draw_text(surf, sub, r.centerx, r.y + h // 2 + 6, 12, (226, 238, 255), "center", bold=False)
    g.buttons.append((bid, pygame.Rect(x, y, w, h)))
    return r


def icon_button(surf, g, bid, x, y, s, kind):
    hov = pygame.Rect(x, y, s, s).collidepoint(g.mouse)
    layer = pygame.Surface((s, s), pygame.SRCALPHA)
    rrect(layer, (255, 255, 255, 70 if hov else 40), (0, 0, s, s), 12)
    surf.blit(layer, (x, y))
    rrect(surf, (255, 255, 255, 90), (x, y, s, s), 12, 1)
    cx, cy = x + s // 2, y + s // 2
    if kind == "sound":
        pygame.draw.polygon(surf, (234, 246, 255),
                            [(cx - 8, cy - 4), (cx - 3, cy - 4), (cx + 3, cy - 9),
                             (cx + 3, cy + 9), (cx - 3, cy + 4), (cx - 8, cy + 4)])
        if SAVE.settings["vol"] == 0:
            pygame.draw.line(surf, (234, 246, 255), (cx + 6, cy - 5), (cx + 12, cy + 5), 2)
            pygame.draw.line(surf, (234, 246, 255), (cx + 12, cy - 5), (cx + 6, cy + 5), 2)
        else:
            pygame.draw.arc(surf, (234, 246, 255), (cx + 1, cy - 8, 14, 16), -0.9, 0.9, 2)
    elif kind == "gear":
        pygame.draw.circle(surf, (234, 246, 255), (cx, cy), 6, 2)
        for i in range(6):
            a = i * math.pi / 3
            pygame.draw.line(surf, (234, 246, 255),
                             (cx + math.cos(a) * 8, cy + math.sin(a) * 8),
                             (cx + math.cos(a) * 12, cy + math.sin(a) * 12), 2)
    elif kind == "pause":
        if g.state == "paused":
            pygame.draw.polygon(surf, (234, 246, 255),
                                [(cx - 5, cy - 8), (cx + 9, cy), (cx - 5, cy + 8)])
        else:
            pygame.draw.rect(surf, (234, 246, 255), (cx - 7, cy - 8, 5, 16))
            pygame.draw.rect(surf, (234, 246, 255), (cx + 2, cy - 8, 5, 16))
    g.buttons.append((bid, pygame.Rect(x, y, s, s)))


def fmt_time(sec):
    sec = max(0, int(math.ceil(sec)))
    return "%d:%02d" % (sec // 60, sec % 60)


DAY_LINES = ["сегодня точно успеешь", "физрук опять забыл ключи от зала",
             "в столовой снова компот", "завуч сегодня добрый… наверное",
             "звонок для учителя, но бежим всё равно", "кто-то закрыл шкафчик изнутри",
             "в библиотеке слышно каждый шаг", "на крыше сегодня ветрено",
             "уборщица только помыла полы", "последний урок — самый длинный",
             "булки в буфете ещё тёплые", "директор идёт по коридору"]


def day_line():
    t = time.localtime()
    r = mulberry(hash_seed("fraza/%d%d%d" % (t.tm_year, t.tm_mon, t.tm_mday)))
    return DAY_LINES[int(r() * len(DAY_LINES))]


def best_of(g, mode):
    return SAVE.records.get(rec_key(mode, SAVE.src, SAVE.seed))


def draw_menu(surf, g):
    surf.blit(sky_surface(THEMES["yard"]), (0, 0))
    surf.blit(deco_surface(THEMES["yard"], VW * 2), (-60, 0))
    veil = pygame.Surface((VW, VH), pygame.SRCALPHA)
    veil.fill((4, 10, 22, 150))
    surf.blit(veil, (0, 0))
    panel(surf, 700, 360, GOLD)
    draw_text(surf, "ПЕРЕМЕНА", VW // 2, 76, 40, (255, 243, 196), "center", shadow=True)
    g.buttons.append(("secret", pygame.Rect(270, 70, 260, 46)))   # четыре нажатия — DEV
    if g.dev_on:
        ui_button(surf, g, "dev_open", 64, 84, 66, 26, "DEV", size=11, tint=RED)
    draw_text(surf, day_line(), VW // 2, 124, 12, SKYBLUE, "center", bold=False)

    modes = [("normal", "ОБЫЧНЫЙ"), ("hard", "ХАРДКОР"), ("endless", "БЕСКОНЕЧНЫЙ")]
    for i, (k, name) in enumerate(modes):
        d = DIFFS[k]
        ui_button(surf, g, "mode_" + k, 122 + i * 189, 146, 178, 56, name, d["tag"],
                  sel=(g.pick == k), size=15 if k != "endless" else 13,
                  tint=RED if k == "hard" else (None if k != "endless" else (201, 160, 255)))
        b = best_of(g, k)
        draw_text(surf, ("рекорд %d" % b["score"]) if b else "ещё не пройден",
                  211 + i * 189, 210, 11, MINT if b else (140, 160, 190), "center", bold=False)

    ui_button(surf, g, "src_classic", 122, 232, 150, 36, "КЛАССИКА", size=13,
              sel=(SAVE.src == "classic"))
    ui_button(surf, g, "src_seed", 282, 232, 150, 36, "СИД " + SAVE.seed, size=13,
              sel=(SAVE.src == "seed"))
    ui_button(surf, g, "seed_open", 442, 232, 110, 36, "ВВЕСТИ", size=13, tint=MINT)
    ui_button(surf, g, "mods_open", 562, 232, 116, 36,
              ("МОДЫ · %d" % mod_count()) if mod_count() else "МОДЫ", size=13,
              sel=mod_count() > 0, tint=WARM)

    ui_button(surf, g, "shop_open", 122, 280, 160, 46, "МАГАЗИН",
              "%d булок" % SAVE.stats["buns"], size=15, tint=(255, 159, 243))
    ready = sum(1 for t in SAVE.daily.get("tasks", [])
                if not t["taken"] and t["have"] >= TASK_BY_KEY[t["k"]][3])
    ui_button(surf, g, "records_open", 292, 280, 150, 46, "КАБИНЕТ",
              ("задания · %d!" % ready) if ready else "рекорды и задания", size=15,
              tint=MINT if ready else None)
    ui_button(surf, g, "play", 452, 280, 226, 46, "ИГРАТЬ ×%.2f" % mod_mult(), size=19, sel=True)
    if SAVE.daily.get("reward", 0) > 0:
        ui_button(surf, g, "claim_day", 122, 332, 250, 30,
                  "ЗАБРАТЬ +%d ЗА ДЕНЬ %d" % (SAVE.daily["reward"], SAVE.stats["days"]),
                  size=12, sel=True, tint=GOLD)

    if SAVE.settings["hints"] and SAVE.daily.get("reward", 0) <= 0:
        draw_text(surf, "← →  бежать · ПРОБЕЛ прыжок · E предмет · P пауза · M звук",
                  VW // 2, 342, 11, (150, 175, 205), "center", bold=False)
    icon_button(surf, g, "sound", 700, 78, 36, "sound")
    icon_button(surf, g, "settings", 700, 120, 36, "gear")


def draw_hud(surf, g):
    bar = pygame.Surface((VW - 20, 40), pygame.SRCALPHA)
    rrect(bar, (9, 16, 32, 150), (0, 0, VW - 20, 40), 12)
    surf.blit(bar, (10, 10))
    full = max(1, g.time_limit())
    frac = clamp(g.time_left / full, 0, 1)
    low = g.time_left < (60 if g.diff["key"] == "hard" else 120)
    col = RED if (low and g.tick % 30 < 15) else (255, 208, 208) if low else (234, 246, 255)
    rrect(surf, (255, 255, 255, 40), (22, 36, 200, 7), 4)
    rrect(surf, (255, 107, 107) if low else MINT, (22, 36, max(6, int(200 * frac)), 7), 4)
    draw_text(surf, fmt_time(g.time_left), 30, 16, 21, col)
    draw_text(surf, "до звонка", 110, 22, 11, (190, 210, 235), bold=False)

    draw_text(surf, g.level.name, VW // 2, 14, 17, WHITE, "center")
    if g.diff.get("endless"):
        draw_text(surf, "этаж %d" % g.floor, VW // 2, 34, 12, (201, 160, 255), "center")
    else:
        n = len(g.levels)
        for i in range(n):
            c = MINT if i < g.level_index else (GOLD if i == g.level_index else (255, 255, 255, 60))
            pygame.draw.circle(surf, c[:3], (VW // 2 - n * 5 + i * 10 + 4, 39),
                               4 if i == g.level_index else 3)

    draw_pie(surf, VW - 152, 30, 0.85)
    draw_text(surf, "%d / %d" % (g.coins, g.coins_max), VW - 134, 20, 19, (255, 217, 138))
    info = g.diff["name"]
    if mod_count():
        info += "  ×%.2f" % mod_mult()
    if SAVE.src == "seed":
        info += "  сид " + SAVE.seed
    if g.deaths:
        info += "  падений %d" % g.deaths
    draw_text(surf, info, VW - 24, 40, 11, (255, 190, 190) if g.diff["key"] == "hard" else (190, 210, 235),
              "right", bold=False)

    if g.combo > 1 and g.combo_t > 0:
        cw, cx, cy = 128, VW // 2 - 64, 58
        rrect(surf, (9, 16, 32), (cx, cy, cw, 22), 8)
        rrect(surf, (139, 255, 207, 60), (cx, cy, int(cw * clamp(g.combo_t / 110.0, 0, 1)), 22), 8)
        rrect(surf, MINT, (cx, cy, cw, 22), 8, 1)
        draw_text(surf, "СЕРИЯ ×%d" % g.combo, VW // 2, cy + 5, 12, MINT, "center")

    slot = pygame.Surface((196, 46), pygame.SRCALPHA)
    rrect(slot, (9, 16, 32, 140), (0, 0, 196, 46), 12)
    surf.blit(slot, (14, 56))
    if g.item:
        it = ITEMS[g.item]
        pygame.draw.rect(surf, it["c"], (26, 68, 22, 22), border_radius=5)
        draw_text(surf, it["n"], 58, 62, 14, WHITE)
        draw_text(surf, "E — применить", 58, 80, 10, (190, 210, 235), bold=False)
    else:
        draw_text(surf, "руки пусты", 26, 62, 13, (150, 170, 200))
        draw_text(surf, "ищи шкафчики", 26, 80, 10, (130, 150, 180), bold=False)

    if g.level.hint and SAVE.settings["hints"] and g.tick < 360:
        hint = pygame.Surface((len(g.level.hint) * 9 + 30, 26), pygame.SRCALPHA)
        rrect(hint, (9, 16, 32, 160), (0, 0, hint.get_width(), 26), 9)
        surf.blit(hint, (VW // 2 - hint.get_width() // 2, VH - 42))
        draw_text(surf, g.level.hint, VW // 2, VH - 36, 13, (225, 238, 255), "center")

    icon_button(surf, g, "pause", VW - 58, 58, 44, "pause")
    icon_button(surf, g, "sound", VW - 112, 58, 44, "sound")


def draw_mods(surf, g):
    veil = pygame.Surface((VW, VH), pygame.SRCALPHA)
    veil.fill((4, 10, 22, 200))
    surf.blit(veil, (0, 0))
    panel(surf, 780, 468)
    draw_text(surf, "МОДИФИКАТОРЫ", VW // 2, 18, 24, (255, 243, 196), "center", shadow=True)
    draw_text(surf, "ОЧКИ × %.2f   ·   включено %d из %d" % (mod_mult(), mod_count(), len(MODS)),
              VW // 2, 46, 14, WARM if mod_count() else (170, 190, 215), "center")
    tabs = [("hard", "СЛОЖНЕЕ"), ("easy", "ПРОЩЕ"), ("class", "УРОКИ")]
    for i, (k, name) in enumerate(tabs):
        n = sum(1 for m in MODS if m[4] == k and SAVE.mods.get(m[0]))
        ui_button(surf, g, "tab_" + k, 130 + i * 184, 66, 172, 32,
                  name + (" · %d" % n if n else ""), size=13, sel=(g.mod_tab == k))
    lst = [m for m in MODS if m[4] == g.mod_tab]
    rows = max(1, (len(lst) + 1) // 2)
    step = min(72, (414 - 106) / rows)
    ch = min(64, step - 8)
    top = 106 + max(0, (414 - 106 - rows * step) / 2)
    for i, m in enumerate(lst):
        x = 400 if i % 2 else 30
        y = int(top + (i // 2) * step)
        on = SAVE.mods.get(m[0], False)
        tint = WARM if m[3] > 0 else MINT
        card = pygame.Surface((350, int(ch)), pygame.SRCALPHA)
        rrect(card, (255, 255, 255, 40 if on else 16), (0, 0, 350, int(ch)), 12)
        surf.blit(card, (x, y))
        rrect(surf, tint if on else (255, 255, 255, 46), (x, y, 350, int(ch)), 12, 2 if on else 1)
        rrect(surf, tint if on else (255, 255, 255, 30), (x + 11, y + ch / 2 - 10, 20, 20), 6)
        if on:
            pygame.draw.lines(surf, INK, False,
                              [(x + 16, y + ch / 2), (x + 20, y + ch / 2 + 4), (x + 27, y + ch / 2 - 5)], 3)
        fit_text(surf, m[1], x + 42, y + ch / 2 - 14, 14, WHITE if on else (220, 232, 250), 220)
        fit_text(surf, m[2], x + 42, y + ch / 2 + 3, 11, (180, 200, 228), 220, bold=False)
        draw_text(surf, ("+%d%%" if m[3] > 0 else "%d%%") % m[3], x + 338, y + ch / 2 - 8, 14,
                  tint, "right")
        g.buttons.append(("mod_" + m[0], pygame.Rect(x, y, 350, int(ch))))
    ui_button(surf, g, "mods_clear", 214, 428, 170, 36, "ВСЁ ВЫКЛ", size=14)
    ui_button(surf, g, "back", 416, 428, 170, 36, "НАЗАД", size=14, sel=True)


def seg_row(surf, g, key, label, opts, y):
    draw_text(surf, label, 44, y + 8, 13, (225, 238, 255))
    w = 336 // len(opts) - 6
    for i, (val, name) in enumerate(opts):
        ui_button(surf, g, "set_%s_%d" % (key, val), 384 + i * (w + 6), y, w, 32, name,
                  size=12, sel=(SAVE.settings[key] == val), tint=MINT)


def draw_settings(surf, g):
    veil = pygame.Surface((VW, VH), pygame.SRCALPHA)
    veil.fill((4, 10, 22, 205))
    surf.blit(veil, (0, 0))
    panel(surf, 760, 400)
    draw_text(surf, "НАСТРОЙКИ", VW // 2, 52, 24, (228, 243, 255), "center", shadow=True)
    seg_row(surf, g, "vol", "Звук", [(0, "выкл"), (1, "тише"), (2, "громко")], 110)
    seg_row(surf, g, "shake", "Тряска экрана", [(0, "выкл"), (1, "слабо"), (2, "обычно")], 158)
    seg_row(surf, g, "hints", "Подсказки", [(0, "выкл"), (1, "вкл")], 206)
    seg_row(surf, g, "fancy", "Красивости", [(0, "выкл"), (1, "вкл")], 254)
    draw_text(surf, "сохраняется в %s" % SAVE_PATH, 44, 304, 11, (150, 170, 200), bold=False)
    ui_button(surf, g, "set_reset", 44, 330, 210, 40, "По умолчанию", size=14)
    ui_button(surf, g, "full", 268, 330, 210, 40, "Весь экран (F)", size=14)
    ui_button(surf, g, "back", 492, 330, 224, 40, "ГОТОВО", size=16, sel=True)


SEED_KEYS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def draw_seed(surf, g):
    veil = pygame.Surface((VW, VH), pygame.SRCALPHA)
    veil.fill((4, 10, 22, 210))
    surf.blit(veil, (0, 0))
    panel(surf, 700, 450)
    draw_text(surf, "СИД", VW // 2, 36, 26, (228, 243, 255), "center", shadow=True)
    draw_text(surf, "одинаковый сид — одинаковая школа · можно набрать на клавиатуре, Enter — готово",
              VW // 2, 70, 11, (170, 195, 225), "center", bold=False)
    bx, bw = VW // 2 - 210, 420
    rrect(surf, (0, 0, 0), (bx, 92, bw, 46), 12)
    rrect(surf, SKYBLUE, (bx, 92, bw, 46), 12, 2)
    shown = g.seed_in or ""
    draw_text(surf, shown or "введи сид", VW // 2, 102, 24,
              WHITE if shown else (120, 140, 170), "center")
    if shown and g.tick % 60 < 34:
        tw = text_surf(shown, 24, WHITE).get_width()
        pygame.draw.rect(surf, MINT, (VW // 2 + tw // 2 + 5, 100, 3, 26))
    ui_button(surf, g, "seed_del", bx + bw + 12, 96, 54, 38, "<", size=18)
    for i, ch in enumerate(SEED_KEYS):
        ui_button(surf, g, "sk_" + ch, 66 + (i % 9) * 74, 152 + (i // 9) * 48, 66, 40, ch, size=18)
    ui_button(surf, g, "seed_rnd", 66, 350, 150, 40, "СЛУЧАЙНЫЙ", size=13)
    ui_button(surf, g, "seed_day", 224, 350, 150, 40, "СИД ДНЯ", size=13, tint=GOLD)
    ui_button(surf, g, "seed_copy", 382, 350, 150, 40, "ЗАПОМНИТЬ", size=13)
    ui_button(surf, g, "back", 540, 350, 136, 40, "ОТМЕНА", size=13)
    ui_button(surf, g, "seed_ok", 224, 398, 308, 42, "ИГРАТЬ ПО ЭТОМУ СИДУ", size=15, sel=True)


ITEM_PRICE = {"soda": 50, "gum": 55, "bag": 70, "watch": 60, "pass": 65}
SHOP_TABS = [("skins", "СКИНЫ"), ("upg", "УЛУЧШЕНИЯ"), ("items", "ПРЕДМЕТЫ")]


def shop_skins(surf, g):
    page = g.shop_page
    per = 12
    total_pages = (len(SKINS) + per - 1) // per
    for j, sk in enumerate(SKINS[page * per:page * per + per]):
        key, name, desc, _shirt, _hair, _acc, price = sk
        cx, cy = 26 + (j % 4) * 188, 96 + (j // 4) * 82
        has, on = owns(key), (SAVE.skin == key)
        card = pygame.Surface((180, 76), pygame.SRCALPHA)
        rrect(card, (139, 255, 207, 40) if on else (255, 255, 255, 26 if has else 12),
              (0, 0, 180, 76), 12)
        surf.blit(card, (cx, cy))
        rrect(surf, MINT if on else (SKYBLUE if has else (255, 255, 255, 45)),
              (cx, cy, 180, 76), 12, 3 if on else 1)
        draw_character(surf, cx + 14, cy + 26, 20, 28, key, 1, 0.0, 255 if has else 110)
        fit_text(surf, name, cx + 54, cy + 10, 13, WHITE if has else (205, 220, 245), 116)
        fit_text(surf, desc, cx + 54, cy + 28, 9, (180, 200, 228), 116, bold=False)
        if has:
            draw_text(surf, "НАДЕТ" if on else "надеть", cx + 54, cy + 46, 12,
                      MINT if on else SKYBLUE)
            draw_text(surf, "%d ур." % SAVE.stats["wear"].get(key, 0), cx + 130, cy + 48, 10,
                      (170, 190, 220), bold=False)
        else:
            draw_pie(surf, cx + 62, cy + 54, 0.55)
            draw_text(surf, str(price), cx + 74, cy + 45, 14,
                      (255, 217, 138) if SAVE.stats["buns"] >= price else (255, 150, 150))
        g.buttons.append(("skin_" + key, pygame.Rect(cx, cy, 180, 76)))
    if total_pages > 1:
        ui_button(surf, g, "shop_prev", 250, 348, 60, 32, "<", size=15)
        ui_button(surf, g, "shop_next", 490, 348, 60, 32, ">", size=15)
        draw_text(surf, "%d/%d" % (page + 1, total_pages), VW // 2, 356, 13,
                  (200, 220, 245), "center")


def shop_upgrades(surf, g):
    for i, u in enumerate(UPGRADES):
        key, name, desc, maxlv, _p, _st = u
        y = 92 + i * 38
        have = upg(key)
        row = pygame.Surface((724, 34), pygame.SRCALPHA)
        rrect(row, (139, 255, 207, 26) if have >= maxlv else (255, 255, 255, 14),
              (0, 0, 724, 34), 9)
        surf.blit(row, (38, y))
        draw_text(surf, name, 50, y + 8, 14, WHITE if have else (215, 230, 250))
        fit_text(surf, desc, 232, y + 10, 11, (185, 205, 232), 240, bold=False)
        for k in range(maxlv):                      # шкала уровней
            col = MINT if k < have else (255, 255, 255, 60)
            rrect(surf, col, (490 + k * 18, y + 12, 13, 11), 3)
        price = upg_price(key)
        if price is None:
            draw_text(surf, "куплено", 700, y + 9, 13, MINT, "right")
        else:
            can = SAVE.stats["buns"] >= price
            ui_button(surf, g, "buy_" + key, 590, y + 1, 168, 32,
                      "%d булок" % price, size=13, sel=can,
                      tint=MINT if can else RED, col=WHITE if can else (255, 190, 190))
    draw_text(surf, "улучшения работают во всех режимах и не мешают рекордам",
              VW // 2, 400, 11, (170, 195, 225), "center", bold=False)


def shop_items(surf, g):
    draw_text(surf, "Купленный предмет окажется в руках в начале следующего забега",
              VW // 2, 92, 12, (200, 220, 245), "center", bold=False)
    for i, k in enumerate(ITEM_KEYS):
        it = ITEMS[k]
        cx, cy = 40 + (i % 3) * 240, 124 + (i // 3) * 104
        price = ITEM_PRICE[k]
        picked = (SAVE.start_item == k)
        card = pygame.Surface((224, 92), pygame.SRCALPHA)
        rrect(card, (139, 255, 207, 40) if picked else (255, 255, 255, 18), (0, 0, 224, 92), 12)
        surf.blit(card, (cx, cy))
        rrect(surf, MINT if picked else (255, 255, 255, 50), (cx, cy, 224, 92), 12,
              3 if picked else 1)
        pygame.draw.rect(surf, it["c"], (cx + 14, cy + 16, 26, 26), border_radius=6)
        draw_text(surf, it["n"], cx + 52, cy + 14, 15, WHITE)
        fit_text(surf, it["d"], cx + 52, cy + 34, 10, (185, 205, 232), 160, bold=False)
        if picked:
            draw_text(surf, "уже в портфеле", cx + 52, cy + 60, 12, MINT)
        else:
            draw_pie(surf, cx + 22, cy + 68, 0.6)
            draw_text(surf, str(price), cx + 36, cy + 59, 14,
                      (255, 217, 138) if SAVE.stats["buns"] >= price else (255, 150, 150))
        g.buttons.append(("item_" + k, pygame.Rect(cx, cy, 224, 92)))
    if SAVE.start_item:
        draw_text(surf, "на старте: " + ITEMS[SAVE.start_item]["n"], VW // 2, 352, 13,
                  MINT, "center")
    if upg("pockets"):
        draw_text(surf, "карманы большие — в забеге поместится ещё один предмет",
                  VW // 2, 380, 11, (170, 195, 225), "center", bold=False)


def draw_shop(surf, g):
    veil = pygame.Surface((VW, VH), pygame.SRCALPHA)
    veil.fill((4, 10, 22, 205))
    surf.blit(veil, (0, 0))
    panel(surf, 780, 450, (255, 159, 243))
    draw_text(surf, "МАГАЗИН", VW // 2, 22, 26, (255, 227, 251), "center", shadow=True)
    draw_pie(surf, 596, 36, 0.8)
    draw_text(surf, "%d булок" % SAVE.stats["buns"], 612, 26, 16, (255, 217, 138))
    for i, (k, name) in enumerate(SHOP_TABS):
        ui_button(surf, g, "shoptab_" + k, 30 + i * 176, 46, 168, 30, name, size=13,
                  sel=(g.shop_tab == k), tint=(255, 159, 243))
    if g.shop_tab == "upg":
        shop_upgrades(surf, g)
    elif g.shop_tab == "items":
        shop_items(surf, g)
    else:
        shop_skins(surf, g)
    ui_button(surf, g, "back", 315, 412, 170, 34, "НАЗАД", size=14, sel=True)


def draw_tasks(surf, g):
    tasks = SAVE.daily.get("tasks", [])
    draw_text(surf, "Задания меняются каждый день в полночь", VW // 2, 108, 12,
              (190, 210, 235), "center", bold=False)
    for i, t in enumerate(tasks):
        tpl = TASK_BY_KEY.get(t["k"])
        if not tpl:
            continue
        y = 140 + i * 62
        done = t["have"] >= tpl[3]
        row = pygame.Surface((640, 52), pygame.SRCALPHA)
        rrect(row, (139, 255, 207, 30) if done else (255, 255, 255, 14), (0, 0, 640, 52), 10)
        surf.blit(row, (80, y))
        rrect(surf, MINT if done else (255, 255, 255, 40), (80, y, 640, 52), 10, 1)
        draw_text(surf, tpl[1], 100, y + 8, 15, WHITE if done else (215, 230, 250))
        frac = clamp(t["have"] / float(tpl[3]), 0, 1)
        rrect(surf, (255, 255, 255, 40), (100, y + 34, 300, 8), 4)
        rrect(surf, MINT if done else SKYBLUE, (100, y + 34, max(4, int(300 * frac)), 8), 4)
        draw_text(surf, "%d / %d" % (min(t["have"], tpl[3]), tpl[3]), 412, y + 30, 12,
                  (200, 220, 245), bold=False)
        if t["taken"]:
            draw_text(surf, "получено", 700, y + 18, 13, MINT, "right")
        elif done:
            ui_button(surf, g, "task_" + t["k"], 540, y + 10, 160, 32,
                      "+%d булок" % tpl[4], size=13, sel=True)
        else:
            draw_text(surf, "+%d булок" % tpl[4], 700, y + 18, 13, (255, 217, 138), "right")
    if not tasks:
        draw_text(surf, "сегодня заданий нет — загляни завтра", VW // 2, 200, 15,
                  (200, 220, 245), "center")
    draw_text(surf, "Серия дней: %d   ·   выполнено заданий всего: %d"
              % (SAVE.stats["days"], SAVE.stats["tasks_done"]),
              VW // 2, 356, 12, (190, 210, 235), "center", bold=False)
    if SAVE.daily.get("reward", 0) > 0:
        ui_button(surf, g, "claim_day", 290, 376, 220, 34,
                  "ЗАБРАТЬ +%d ЗА ДЕНЬ" % SAVE.daily["reward"], size=13, sel=True, tint=GOLD)


def draw_code(surf, g):
    veil = pygame.Surface((VW, VH), pygame.SRCALPHA)
    veil.fill((4, 10, 22, 215))
    surf.blit(veil, (0, 0))
    panel(surf, 430, 372, RED)
    draw_text(surf, "ДОСТУП", VW // 2, 78, 28, (255, 217, 217), "center", shadow=True)
    draw_text(surf, "введи код разработчика", VW // 2, 116, 12, (200, 220, 245),
              "center", bold=False)
    for i in range(4):
        col = GOLD if i < len(g.code) else (255, 255, 255, 60)
        pygame.draw.circle(surf, col[:3], (VW // 2 + int((i - 1.5) * 30), 152), 8)
    if g.code_lock > 0:
        draw_text(surf, "пауза %d сек" % int(math.ceil(g.code_lock / 60.0)), VW // 2, 172, 13,
                  RED, "center")
    elif g.code_bad > 0:
        draw_text(surf, "неверный код", VW // 2, 172, 13, RED, "center")
    keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "del", "0", "esc"]
    for i, k in enumerate(keys):
        kx = VW // 2 - 125 + (i % 3) * 86
        ky = 192 + (i // 3) * 54
        label = "<" if k == "del" else ("ОТМЕНА" if k == "esc" else k)
        bid = "code_del" if k == "del" else ("back" if k == "esc" else "num_" + k)
        ui_button(surf, g, bid, kx, ky, 78, 46, label, size=12 if k == "esc" else 20,
                  dim=(g.code_lock > 0 and k != "esc"))


def draw_admin(surf, g):
    veil = pygame.Surface((VW, VH), pygame.SRCALPHA)
    veil.fill((4, 10, 22, 215))
    surf.blit(veil, (0, 0))
    panel(surf, 760, 462, RED)
    draw_text(surf, "ПАНЕЛЬ РАЗРАБОТЧИКА", VW // 2, 22, 22, (255, 217, 217), "center", shadow=True)
    draw_text(surf, "выданное здесь помечает забег: рекорд не сохранится", VW // 2, 50, 11,
              (200, 220, 245), "center", bold=False)

    draw_text(surf, "БУЛКИ И ОТКРЫТИЯ", 40, 72, 10, WARM)
    ui_button(surf, g, "dev_buns100", 40, 88, 172, 38, "+100 булок", size=14)
    ui_button(surf, g, "dev_buns1000", 218, 88, 172, 38, "+1000 булок", size=14)
    ui_button(surf, g, "dev_skins", 396, 88, 172, 38, "Все скины", size=14)
    ui_button(surf, g, "dev_upg", 574, 88, 172, 38, "Все улучшения", size=13)

    draw_text(surf, "ПРЕДМЕТ В РУКИ", 40, 138, 10, MINT)
    for i, k in enumerate(ITEM_KEYS):
        ui_button(surf, g, "dev_item_" + k, 40 + i * 146, 154, 136, 38, ITEMS[k]["n"], size=13)

    draw_text(surf, "ЗАБЕГ", 40, 204, 10, SKYBLUE)
    ui_button(surf, g, "dev_time", 40, 220, 172, 38, "+60 секунд", size=14)
    ui_button(surf, g, "dev_coins", 218, 220, 172, 38, "Все пирожки", size=14)
    ui_button(surf, g, "dev_skip", 396, 220, 172, 38, "Пропустить этаж", size=13)
    ui_button(surf, g, "dev_shield", 574, 220, 172, 38, "Выдать портфель", size=13)

    draw_text(surf, "ПРОГРЕСС", 40, 270, 10, GOLD)
    ui_button(surf, g, "dev_achs", 40, 286, 226, 38,
              "Достижения %d/%d" % (len(SAVE.stats["achs"]), len(ACHS)), size=13)
    ui_button(surf, g, "dev_tasks", 282, 286, 226, 38, "Выполнить задания дня", size=13)
    ui_button(surf, g, "dev_god", 524, 286, 222, 38,
              "Бессмертие: ВКЛ" if g.dev_god else "Бессмертие: выкл", size=13,
              sel=g.dev_god, tint=MINT)

    draw_text(surf, "ОПАСНОЕ", 40, 336, 10, RED)
    ui_button(surf, g, "dev_reset", 40, 352, 340, 38,
              "Точно? Нажми ещё раз" if (g.confirm == "reset" and g.confirm_t > 0)
              else "Сбросить статистику", size=13, tint=RED,
              sel=(g.confirm == "reset" and g.confirm_t > 0))
    ui_button(surf, g, "dev_wipe", 396, 352, 350, 38,
              "Точно? Нажми ещё раз" if (g.confirm == "wipe" and g.confirm_t > 0)
              else "Стереть весь прогресс", size=13, tint=RED,
              sel=(g.confirm == "wipe" and g.confirm_t > 0))

    line = "булок %d   ·   скинов %d/%d   ·   улучшений %d/18" % (
        SAVE.stats["buns"], len(SAVE.stats["owned"]), len(SKINS), SAVE.stats["upg_total"])
    if g.cheated:
        line += "   ·   забег помечен"
    draw_text(surf, line, VW // 2, 400, 12, (200, 220, 245), "center", bold=False)
    ui_button(surf, g, "back", 300, 420, 200, 38, "ЗАКРЫТЬ", size=16, sel=True)


def draw_records(surf, g):
    veil = pygame.Surface((VW, VH), pygame.SRCALPHA)
    veil.fill((4, 10, 22, 200))
    surf.blit(veil, (0, 0))
    panel(surf, 760, 440)
    draw_text(surf, "КАБИНЕТ", VW // 2, 30, 24, (228, 243, 255), "center", shadow=True)
    done = len(SAVE.stats["achs"])
    ui_button(surf, g, "rec_stats", 140, 64, 180, 32, "СТАТИСТИКА", size=13,
              sel=(g.rec_tab == "stats"))
    ui_button(surf, g, "rec_achs", 330, 64, 200, 32, "ДОСТИЖЕНИЯ · %d/%d" % (done, len(ACHS)),
              size=11, sel=(g.rec_tab == "achs"), tint=GOLD)
    ready = sum(1 for t in SAVE.daily.get("tasks", [])
                if not t["taken"] and t["have"] >= TASK_BY_KEY[t["k"]][3])
    ui_button(surf, g, "rec_tasks", 542, 64, 180, 32,
              "ЗАДАНИЯ" + (" · %d!" % ready if ready else ""), size=12,
              sel=(g.rec_tab == "tasks"), tint=MINT)
    per_page = 22
    pages = (len(ACHS) + per_page - 1) // per_page
    if g.rec_tab == "tasks":
        draw_tasks(surf, g)
    elif g.rec_tab == "stats":
        rows = [("Забегов до конца", "runs"), ("Из них хардкор", "hard_runs"),
                ("Уровней пройдено", "levels"), ("Пирожков собрано", "pies"),
                ("Булок в кармане", "buns"), ("Завучей затоптано", "stomps"),
                ("Голов мячом", "goals"), ("Предметов использовано", "items"),
                ("Уроков сдано", "lessons_ok"), ("Уроков завалено", "lessons_bad"),
                ("Прыжков", "jumps"), ("Падений", "falls")]
        for i, (name, key) in enumerate(rows):
            x = 60 if i < 6 else 410
            y = 122 + (i % 6) * 26
            draw_text(surf, name, x, y, 12, (200, 220, 245), bold=False)
            draw_text(surf, str(SAVE.stats.get(key, 0)), x + 290, y - 1, 13, WHITE, "right")
        draw_text(surf, "ЛУЧШИЕ ЗАБЕГИ", 60, 300, 10, GOLD)
        for i, (k, name) in enumerate([("normal", "Обычный"), ("hard", "Хардкор"),
                                       ("endless", "Бесконечный")]):
            b = best_of(g, k)
            draw_text(surf, name, 60 + i * 230, 322, 12, (200, 220, 245), bold=False)
            draw_text(surf, ("%d очков" % b["score"]) if b else "нет", 60 + i * 230, 342, 13,
                      MINT if b else (140, 160, 190))
        draw_text(surf, "Лучший счёт %d   ·   этажей %d   ·   дней %d   ·   улучшений %d/18" %
                  (SAVE.stats["best"], SAVE.stats["max_floor"], SAVE.stats["days"],
                   SAVE.stats["upg_total"]),
                  VW // 2, 380, 12, (190, 210, 235), "center", bold=False)
    else:
        if pages > 1:
            ui_button(surf, g, "ach_prev", 614, 64, 42, 32, "<", size=14)
            ui_button(surf, g, "ach_next", 662, 64, 42, 32, ">", size=14)
            draw_text(surf, "%d/%d" % (g.ach_page + 1, pages), 726, 72, 12,
                      (190, 210, 235), "center")
        start = g.ach_page * per_page
        for j, a in enumerate(ACHS[start:start + per_page]):
            key, name, desc, slot, need, prize = a
            ok = key in SAVE.stats["achs"]
            ax = 44 if j < 11 else 404
            ay = 104 + (j % 11) * 26
            val = g.ach_value(slot)
            row = pygame.Surface((352, 23), pygame.SRCALPHA)
            rrect(row, (139, 255, 207, 30) if ok else (255, 255, 255, 10), (0, 0, 352, 23), 7)
            if not ok and val > 0:
                rrect(row, (159, 216, 255, 40), (0, 0, int(352 * min(1.0, val / float(need))), 23), 7)
            surf.blit(row, (ax, ay))
            rrect(surf, MINT if ok else (255, 255, 255, 40), (ax + 7, ay + 6, 11, 11), 3)
            prog = ("+%d" % prize) if ok else "%d/%d" % (min(val, need), need)
            pw = text_surf(prog, 11, WHITE).get_width()
            fit_text(surf, name, ax + 25, ay + 5, 11, WHITE if ok else (210, 225, 248), 118)
            fit_text(surf, desc, ax + 146, ay + 6, 10, (180, 200, 228), 184 - pw, bold=False)
            draw_text(surf, prog, ax + 344, ay + 5, 11,
                      (255, 217, 138) if ok else (170, 190, 220), "right")
    ui_button(surf, g, "back", 320, 400, 170, 34, "НАЗАД", size=14, sel=True)


def hint_plate(surf, msg, y, size=14):
    w = text_surf(msg, size, WHITE).get_width() + 30
    plate = pygame.Surface((w, size + 16), pygame.SRCALPHA)
    rrect(plate, (6, 12, 24, 170), (0, 0, w, size + 16), 9)
    surf.blit(plate, (VW // 2 - w // 2, y))
    draw_text(surf, msg, VW // 2, y + 7, size, WHITE, "center")


def draw_lesson(surf, g):
    L = g.lesson
    surf.blit(vgrad("class", VW, VH, (75, 100, 120), (125, 106, 82)), (0, 0))
    pygame.draw.rect(surf, (107, 87, 68), (0, VH - 120, VW, 120))
    pygame.draw.rect(surf, (125, 103, 80), (0, VH - 120, VW, 8))
    rrect(surf, (122, 91, 60), (116, 62, VW - 232, 196), 8)
    rrect(surf, (47, 83, 72), (126, 72, VW - 252, 176), 5)
    pygame.draw.rect(surf, (138, 97, 53), (80, VH - 118, VW - 160, 16), border_radius=4)
    pygame.draw.rect(surf, (107, 74, 42), (130, VH - 102, 14, 60))
    pygame.draw.rect(surf, (107, 74, 42), (VW - 144, VH - 102, 14, 60))
    # учитель: на «списать» он то пишет на доске, то оборачивается
    away = (L["kind"] == "copy" and L["phase"] == "away")
    pygame.draw.polygon(surf, (58, 74, 99), [(176, 352), (204, 352), (199, 318), (181, 318)])
    pygame.draw.rect(surf, (140, 160, 185), (178, 296, 24, 24), border_radius=4)
    pygame.draw.circle(surf, (240, 205, 170) if not away else (150, 110, 80), (190, 288), 10)
    if not away:
        pygame.draw.circle(surf, (40, 48, 62), (186, 288), 2)
        pygame.draw.circle(surf, (40, 48, 62), (194, 288), 2)
        if L["kind"] == "copy" and L["phase"] == "watch":
            draw_text(surf, "!", 190, 258, 20, RED, "center")

    head = pygame.Surface((380, 34), pygame.SRCALPHA)
    rrect(head, (9, 16, 32, 160), (0, 0, 380, 34), 12)
    surf.blit(head, (VW // 2 - 190, 10))
    draw_text(surf, "УРОК · " + L["subject"].upper(), VW // 2, 18, 15, GOLD, "center")

    if L["done"]:
        p = pygame.Surface((520, 190), pygame.SRCALPHA)
        rrect(p, (9, 16, 32, 235), (0, 0, 520, 190), 18)
        surf.blit(p, (VW // 2 - 260, 150))
        ok = L.get("ok")
        draw_text(surf, "ЗАЧЁТ!" if ok else "НЕЗАЧЁТ", VW // 2, 175, 34,
                  MINT if ok else RED, "center", shadow=True)
        draw_text(surf, "Учитель отпустил пораньше" if ok else "Задержали после урока",
                  VW // 2, 226, 15, WHITE, "center")
        bonus = (30 if mod("favorite") else 15) if ok else -10
        draw_text(surf, "%+d секунд к перемене" % bonus, VW // 2, 254, 15,
                  MINT if ok else RED, "center")
        draw_text(surf, "бежим на перемену…", VW // 2, 288, 13, (200, 220, 245), "center", bold=False)
        return

    if L["kind"] == "quiz":
        qi = min(L["qi"], len(L["qs"]) - 1)
        q = L["qs"][qi]
        draw_text(surf, "Вопрос %d из %d   ·   верных %d, нужно %d"
                  % (qi + 1, len(L["qs"]), L["right"], L["need"]),
                  VW // 2, 92, 13, (210, 228, 250), "center", bold=False)
        fit_text(surf, q["q"], VW // 2, 128, 21, WHITE, 540, "center")
        for i, opt in enumerate(q["opts"]):
            y = 196 + i * 54
            sel = (L["pick"] == i)
            right = (L["pick_t"] > 0 and i == q["r"])
            tint = MINT if right else (RED if (sel and not right) else SKYBLUE)
            ui_button(surf, g, "ans%d" % i, 240, y, 400, 44, "%d. %s" % (i + 1, opt),
                      size=16, sel=right or sel, tint=tint)
        bar = clamp(L["limit"] / float((6 if mod("strict") else 9) * 60), 0, 1)
        rrect(surf, (255, 255, 255, 40), (180, VH - 52, 440, 8), 4)
        rrect(surf, GOLD if bar > 0.3 else RED, (180, VH - 52, int(440 * bar), 8), 4)
    elif L["kind"] == "copy":
        col = MINT if L["phase"] == "away" else (GOLD if L["phase"] == "turn" else RED)
        word = {"away": "СПИСЫВАЙ!", "turn": "ОСТОРОЖНО…", "watch": "НЕ ПИШИ!"}[L["phase"]]
        draw_text(surf, "Контрольная. У соседа всё решено.", VW // 2 + 40, 96, 15,
                  (230, 240, 255), "center")
        draw_text(surf, word, VW // 2 + 40, 130, 34, col, "center", shadow=True)
        draw_text(surf, "держи ПРОБЕЛ, пока учитель у доски", VW // 2 + 40, 182, 13,
                  (200, 220, 245), "center", bold=False)
        rrect(surf, (255, 255, 255, 40), (240, 300, 330, 20), 7)
        rrect(surf, MINT, (243, 303, max(4, int(324 * L["fill"] / 100.0)), 14), 6)
        draw_text(surf, "СПИСАНО %d%%" % int(L["fill"]), 405, 302, 12, INK, "center")
        left = max(0, L["max_strikes"] - L["strikes"] // 12)
        draw_text(surf, "замечаний осталось: %d" % left, VW // 2, 334, 12,
                  RED if left <= 1 else (200, 220, 245), "center")
    elif L["kind"] == "dict":
        draw_text(surf, "Диктант. Успевай записывать за учителем.", VW // 2 + 40, 96, 15,
                  (230, 240, 255), "center")
        draw_text(surf, "записано %d из %d" % (L["hits"], L["need"]), VW // 2 + 40, 124, 14,
                  MINT if L["hits"] >= L["need"] else (220, 235, 255), "center")
        rrect(surf, (255, 255, 255, 30), (370, 268, 60, 64), 10)
        rrect(surf, GOLD, (370, 268, 60, 64), 10, 2)
        for ar in L["arrows"]:
            x = int(ar["x"])
            pts = ([(x + 16, 284), (x - 8, 300), (x + 16, 316)] if ar["dir"] == "left"
                   else [(x - 16, 284), (x + 8, 300), (x - 16, 316)])
            pygame.draw.polygon(surf, SKYBLUE if abs(x - 400) > 46 else MINT, pts)
        hint_plate(surf, "жми ← и → по очереди", VH - 74)
    elif L["kind"] == "canteen":
        draw_text(surf, "Большая перемена. Лови булки, тряпки — мимо!", VW // 2, 96, 15,
                  (230, 240, 255), "center")
        draw_text(surf, "поймано %d · нужно %d" % (L["got"], L["need"]), VW // 2, 124, 14,
                  MINT if L["got"] >= L["need"] else (220, 235, 255), "center")
        for d in L["drops"]:
            if d["bad"]:
                pygame.draw.rect(surf, (120, 140, 160),
                                 (int(d["x"]) - 10, int(d["y"]) - 8, 20, 16), border_radius=4)
            else:
                draw_pie(surf, int(d["x"]), int(d["y"]), 0.9)
        tx = int(L["tray"])
        pygame.draw.rect(surf, (200, 214, 229), (tx - 52, 358, 104, 12), border_radius=5)
        pygame.draw.rect(surf, (150, 168, 188), (tx - 46, 370, 92, 6), border_radius=3)
        hint_plate(surf, "двигай поднос ← →", VH - 74)
    elif L["kind"] == "pushups":
        draw_text(surf, "Физра. Отжимания: жми ← и → строго по очереди.", VW // 2, 96, 15,
                  (230, 240, 255), "center")
        draw_text(surf, "%d из %d" % (L["reps"], L["need"]), VW // 2, 124, 20,
                  MINT if L["reps"] >= L["need"] else GOLD, "center")
        dy = 16 if L["down"] > 0 else 0
        pygame.draw.rect(surf, (58, 74, 99), (VW // 2 - 60, 290 + dy, 120, 18), border_radius=8)
        pygame.draw.circle(surf, (240, 205, 170), (VW // 2 + 66, 296 + dy), 12)
        pygame.draw.line(surf, (58, 74, 99), (VW // 2 - 50, 308 + dy), (VW // 2 - 50, 332), 6)
        pygame.draw.line(surf, (58, 74, 99), (VW // 2 + 40, 308 + dy), (VW // 2 + 40, 332), 6)
        nxt = "← ЛЕВАЯ" if L["nxt"] == "left" else "ПРАВАЯ →"
        draw_text(surf, nxt, VW // 2, 340, 18, SKYBLUE, "center")
        bar = clamp(L["limit"] / float((16 if mod("strict") else 22) * 60), 0, 1)
        rrect(surf, (255, 255, 255, 40), (240, VH - 52, 330, 8), 4)
        rrect(surf, GOLD if bar > 0.3 else RED, (240, VH - 52, int(330 * bar), 8), 4)
    else:
        draw_text(surf, "Последний урок. Главное — не уснуть.", VW // 2, 104, 15,
                  (230, 240, 255), "center")
        eye = max(0.0, L["eye"])
        lid = int(VH * 0.45 * (1 - eye / 100.0))
        if lid > 0:
            pygame.draw.rect(surf, (6, 10, 20), (0, 0, VW, lid))
            pygame.draw.rect(surf, (6, 10, 20), (0, VH - lid, VW, lid))
        rrect(surf, (9, 16, 32), (240, 300, 330, 26), 9)
        rrect(surf, MINT if eye > 35 else RED, (243, 303, max(4, int(324 * eye / 100.0)), 20), 7)
        draw_text(surf, "БОДРОСТЬ %d%%" % int(eye), 405, 306, 13, INK, "center")
        plate = pygame.Surface((240, 30), pygame.SRCALPHA)
        rrect(plate, (6, 12, 24, 160), (0, 0, 240, 30), 9)
        surf.blit(plate, (VW // 2 - 120, 344))
        draw_text(surf, "жми ПРОБЕЛ почаще", VW // 2, 350, 16, WHITE, "center")
        draw_text(surf, "продержись %d сек" % int(math.ceil(L["limit"] / 60.0)),
                  VW // 2, 382, 13, (200, 220, 245), "center", bold=False)


def draw_banner(surf, g, title, sub, col):
    p = pygame.Surface((560, 150), pygame.SRCALPHA)
    rrect(p, (9, 16, 32, 230), (0, 0, 560, 150), 18)
    surf.blit(p, (VW // 2 - 280, 150))
    draw_text(surf, title, VW // 2, 172, 38, col, "center", shadow=True)
    draw_text(surf, sub, VW // 2, 230, 15, WHITE, "center")


def rank_of(used, coins, deaths):
    if deaths == 0 and coins > 40:
        return "ОТЛИЧНИК", MINT
    if deaths <= 2:
        return "ХОРОШИСТ", SKYBLUE
    if deaths <= 5:
        return "ТРОЕЧНИК, НО ЖИВОЙ", GOLD
    return "ЗАВУЧ ЗАПОМНИЛ ТЕБЯ", RED


def draw_end(surf, g):
    veil = pygame.Surface((VW, VH), pygame.SRCALPHA)
    veil.fill((4, 10, 22, 170) if g.state == "win" else (40, 6, 14, 180))
    surf.blit(veil, (0, 0))
    panel(surf, 620, 430, MINT if g.state == "win" else RED)
    win = (g.state == "win")
    used = g.diff["time"] - g.time_left
    draw_text(surf, "УСПЕЛ!" if win else "НЕ УСПЕЛ",
              VW // 2, 78, 44, MINT if win else RED, "center", shadow=True)
    if win:
        sub = "И это на ХАРДКОРЕ. Уважение." if g.diff["key"] == "hard" else \
              "Звонок ещё не прозвенел, а ты уже герой перемены."
    else:
        sub = "Звонок прозвенел без тебя." if getattr(g, "over_why", "") == "bell" else \
              "Одна жизнь — один шанс."
    draw_text(surf, sub, VW // 2, 128, 15, (219, 232, 255), "center")
    draw_text(surf, "Время %s   ·   пирожков %d/%d   ·   падений %d"
              % (fmt_time(used), g.coins, g.coins_max, g.deaths),
              VW // 2, 162, 14, (219, 232, 255), "center", bold=False)
    target = g.run_score()
    g.score_shown += (target - g.score_shown) * 0.14
    if target - g.score_shown < 1:
        g.score_shown = target
    draw_text(surf, "%d ОЧКОВ" % int(g.score_shown), VW // 2, 196, 34,
              (255, 243, 196), "center", shadow=True)
    draw_text(surf, "%d × %.2f" % (g.run_points(), mod_mult()), VW // 2, 238, 12,
              (200, 220, 245), "center", bold=False)
    if win:
        name, col = rank_of(used, g.coins, g.deaths)
        draw_text(surf, name, VW // 2, 266, 22, col, "center")
    if g.record:
        draw_text(surf, "★ новый рекорд ★", VW // 2, 300, 14, GOLD, "center")
    elif g.best and g.best.get("score"):
        draw_text(surf, "рекорд: %d очков" % g.best["score"], VW // 2, 300, 13,
                  (200, 220, 245), "center", bold=False)
    if SAVE.src == "seed":
        draw_text(surf, "сид " + SAVE.seed, VW // 2, 322, 13, SKYBLUE, "center", bold=False)
    ui_button(surf, g, "again", 190, 348, 180, 50, "ЕЩЁ РАЗ", size=17, sel=True)
    ui_button(surf, g, "shop_open", 380, 348, 100, 50, "МАГАЗИН", size=13)
    ui_button(surf, g, "menu", 490, 348, 120, 50, "В МЕНЮ", size=15)


def draw_paused(surf, g):
    veil = pygame.Surface((VW, VH), pygame.SRCALPHA)
    veil.fill((4, 10, 22, 170))
    surf.blit(veil, (0, 0))
    panel(surf, 520, 320)
    draw_text(surf, "ПАУЗА", VW // 2, 140, 40, (228, 243, 255), "center", shadow=True)
    ui_button(surf, g, "resume", 250, 200, 300, 60, "ПРОДОЛЖИТЬ", size=21, sel=True)
    ui_button(surf, g, "restart", 250, 272, 142, 52, "СНАЧАЛА", size=16)
    ui_button(surf, g, "menu", 408, 272, 142, 52, "В МЕНЮ", size=16)
    icon_button(surf, g, "settings", 164, 206, 36, "gear")
    icon_button(surf, g, "sound", 164, 248, 36, "sound")
    if g.dev_on:
        ui_button(surf, g, "dev_open", 560, 206, 76, 30, "DEV", size=12, tint=RED)


def draw_clear(surf, g):
    veil = pygame.Surface((VW, VH), pygame.SRCALPHA)
    veil.fill((4, 10, 22, 120))
    surf.blit(veil, (0, 0))
    draw_banner(surf, g, "ЭТАЖ ПРОЙДЕН", "бежим дальше…", MINT)


def draw_toast(surf, g):
    """Подсказка живёт в левом нижнем углу — там её ничто не перекрывает."""
    if g.toast_t <= 0 or not g.toast_text:
        return
    s = text_surf(g.toast_text, 14, (255, 217, 138))
    w = s.get_width() + 30
    x, y = 16, VH - 40
    plate = pygame.Surface((w, 30), pygame.SRCALPHA)
    rrect(plate, (9, 16, 32, 225), (0, 0, w, 30), 10)
    if g.toast_t < 30:
        plate.set_alpha(int(255 * g.toast_t / 30.0))
        s = s.copy()
        s.set_alpha(int(255 * g.toast_t / 30.0))
    surf.blit(plate, (x, y))
    surf.blit(s, (x + 15, y + 7))


def draw_ach(surf, g):
    if g.ach_t <= 0 or not g.ach_show:
        return
    key, name, desc, slot, need, prize = g.ach_show
    k = min(1.0, (150 - g.ach_t) / 12.0)
    x, y = VW // 2 - 190, int(16 - (1 - k) * 40)
    card = pygame.Surface((380, 54), pygame.SRCALPHA)
    rrect(card, (9, 16, 32, 240), (0, 0, 380, 54), 14)
    surf.blit(card, (x, y))
    rrect(surf, GOLD, (x, y, 380, 54), 14, 2)
    pygame.draw.polygon(surf, GOLD, [(x + 30, y + 14), (x + 38, y + 30),
                                     (x + 30, y + 44), (x + 22, y + 30)])
    draw_text(surf, "ДОСТИЖЕНИЕ", x + 54, y + 10, 10, (255, 209, 102))
    draw_text(surf, name, x + 54, y + 24, 15, WHITE)
    draw_text(surf, "+%d" % prize, x + 364, y + 20, 15, (255, 217, 138), "right")


# ================== КНОПКИ И ВВОД ==================
def do_button(g, bid):
    g.hot, g.hot_t = bid, 9
    SFX.click()
    if bid.startswith("mode_"):
        g.pick = bid[5:]
    elif bid == "play":
        g.start_run(g.pick)
    elif bid == "again":
        g.start_run(g.diff["key"])
    elif bid == "menu":
        g.state = "menu"
        SAVE.save()
    elif bid == "resume":
        g.state = "play"
    elif bid == "restart":
        g.start_run(g.diff["key"])
    elif bid == "pause":
        g.state = "paused" if g.state == "play" else ("play" if g.state == "paused" else g.state)
    elif bid == "sound":
        SAVE.settings["vol"] = 0 if SAVE.settings["vol"] else 2
        SAVE.save()
        SFX.coin()
    elif bid == "settings":
        g.back = g.state
        g.state = "settings"
    elif bid == "set_reset":
        SAVE.settings = fresh_settings()
        SAVE.save()
        g.toast("Настройки по умолчанию")
    elif bid.startswith("set_"):
        key, _, val = bid[4:].rpartition("_")
        if key in SAVE.settings:
            SAVE.settings[key] = int(val)
            SAVE.save()
    elif bid == "full":
        try:
            pygame.display.toggle_fullscreen()
        except pygame.error:
            g.toast("Полный экран недоступен")
    elif bid == "mods_open":
        g.back = g.state
        g.state = "mods"
    elif bid == "mods_clear":
        SAVE.mods.clear()
        SAVE.save()
    elif bid.startswith("tab_"):
        g.mod_tab = bid[4:]
    elif bid.startswith("mod_"):
        k = bid[4:]
        if SAVE.mods.pop(k, None) is None:
            SAVE.mods[k] = True
        SAVE.save()
        g.set_levels()
    elif bid == "src_classic":
        SAVE.src = "classic"
        SAVE.save()
        g.set_levels()
    elif bid == "src_seed":
        SAVE.src = "seed"
        SAVE.save()
        g.set_levels()
    elif bid == "seed_open":
        g.back = g.state
        g.state = "seedin"
        g.seed_in = SAVE.seed
    elif bid == "seed_ok":
        if g.seed_in:
            SAVE.seed = clean_seed(g.seed_in)
            SAVE.src = "seed"
            SAVE.save()
            g.set_levels()
            g.toast("Сид " + SAVE.seed)
        g.state = g.back or "menu"
    elif bid == "seed_del":
        g.seed_in = g.seed_in[:-1]
    elif bid == "seed_rnd":
        g.seed_in = random_seed()
    elif bid == "seed_day":
        g.seed_in = day_seed()
        g.toast("Сид дня: " + g.seed_in)
    elif bid == "seed_copy":
        g.toast("Сид " + (g.seed_in or SAVE.seed) + " — запиши его")
    elif bid.startswith("sk_"):
        if len(g.seed_in) < 8:
            g.seed_in += bid[3:]
    elif bid in ("skins_open", "shop_open"):
        g.back = g.state
        g.state = "shop"
    elif bid.startswith("shoptab_"):
        g.shop_tab = bid[8:]
        g.shop_page = 0
    elif bid == "shop_prev":
        g.shop_page = max(0, g.shop_page - 1)
    elif bid == "shop_next":
        g.shop_page = min((len(SKINS) - 1) // 12, g.shop_page + 1)
    elif bid.startswith("skin_"):
        buy_skin(g, bid[5:])
    elif bid.startswith("buy_"):
        buy_upgrade(g, bid[4:])
    elif bid.startswith("item_"):
        buy_start_item(g, bid[5:])
    elif bid.startswith("task_"):
        g.claim_task(bid[5:])
    elif bid == "claim_day":
        g.claim_daily()
    elif bid == "secret":
        if g.secret_t <= 0:
            g.secret_hits = 0
        g.secret_hits += 1
        g.secret_t = 150
        if g.secret_hits >= 4:
            g.secret_hits = 0
            g.back = g.state
            g.state = "admin" if g.dev_on else "code"
            g.code = ""
            SFX.key()
        elif g.secret_hits >= 2:
            g.toast("ещё %d" % (4 - g.secret_hits))
    elif bid == "dev_open":
        g.back = g.state
        g.state = "admin" if g.dev_on else "code"
        g.code = ""
    elif bid == "code_del":
        g.code = g.code[:-1]
    elif bid.startswith("num_"):
        g.dev_digit(bid[4:])
    elif bid.startswith("dev_"):
        g.dev_do(bid[4:])
    elif bid == "records_open":
        g.back = g.state
        g.state = "records"
    elif bid.startswith("rec_"):
        g.rec_tab = bid[4:]
    elif bid == "ach_prev":
        g.ach_page = max(0, g.ach_page - 1)
    elif bid == "ach_next":
        g.ach_page = min((len(ACHS) - 1) // 22, g.ach_page + 1)
    elif bid.startswith("ans"):
        g.lesson_answer(int(bid[3:]))
    elif bid == "back":
        g.state = g.back or "menu"
        g.back = None


def buy_upgrade(g, key):
    u = UPG_BY_KEY.get(key)
    if not u:
        return
    price = upg_price(key)
    if price is None:
        g.toast("Уже куплено")
        return
    if SAVE.stats["buns"] < price:
        g.toast("Не хватает булок: нужно %d" % price)
        SFX.hurt()
        return
    SAVE.stats["buns"] -= price
    SAVE.stats["spent"] += price
    SAVE.stats["upg"][key] = upg(key) + 1
    SAVE.stats["upg_total"] += 1
    SAVE.stats["bought"] += 1
    g.toast("%s — уровень %d" % (u[1], upg(key)))
    SFX.win()
    g.save_and_check()


def buy_start_item(g, key):
    if key not in ITEMS:
        return
    if SAVE.start_item == key:
        SAVE.start_item = None
        g.toast("Предмет убран из портфеля")
        SAVE.save()
        return
    price = ITEM_PRICE[key]
    if SAVE.stats["buns"] < price:
        g.toast("Не хватает булок: нужно %d" % price)
        SFX.hurt()
        return
    SAVE.stats["buns"] -= price
    SAVE.stats["spent"] += price
    SAVE.stats["bought"] += 1
    SAVE.start_item = key
    g.toast(ITEMS[key]["n"] + " — в портфель на старт")
    SFX.box()
    g.save_and_check()


def buy_skin(g, key):
    sk = SKIN_BY_KEY.get(key)
    if not sk:
        return
    price = sk[6]
    if owns(key):
        SAVE.skin = key
        SAVE.save()
        g.toast("Надет: " + sk[1])
        SFX.key()
        return
    if SAVE.stats["buns"] < price:
        g.toast("Не хватает булок: нужно %d" % price)
        SFX.hurt()
        return
    SAVE.stats["buns"] -= price
    SAVE.stats["spent"] += price
    SAVE.stats["owned"].append(key)
    SAVE.skin = key
    g.toast("Куплено: " + sk[1] + "!")
    SFX.win()
    g.save_and_check()


def click_at(g, pos):
    for bid, rect in reversed(g.buttons):
        if rect.collidepoint(pos):
            do_button(g, bid)
            return True
    return False


def on_key(g, key, down):
    if down and g.state == "code":
        name = pygame.key.name(key)
        if name.isdigit():
            g.dev_digit(name)
        elif key == pygame.K_BACKSPACE:
            g.code = g.code[:-1]
        elif key == pygame.K_ESCAPE:
            do_button(g, "back")
        return
    if down and g.state == "seedin":
        name = pygame.key.name(key).upper()
        if len(name) == 1 and (name.isdigit() or "A" <= name <= "Z"):
            if len(g.seed_in) < 8:
                g.seed_in += name
        elif key == pygame.K_BACKSPACE:
            g.seed_in = g.seed_in[:-1]
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            do_button(g, "seed_ok")
        elif key == pygame.K_ESCAPE:
            do_button(g, "back")
        return

    if key in (pygame.K_LEFT, pygame.K_a):
        KEYS["left"] = down
        if down and g.state == "lesson":
            g.lesson_press("left")
    elif key in (pygame.K_RIGHT, pygame.K_d):
        KEYS["right"] = down
        if down and g.state == "lesson":
            g.lesson_press("right")
    elif key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
        KEYS["jump"] = down
        if down:
            if g.state == "lesson":
                g.lesson_press("jump")
            elif g.player:
                g.player["jump_buf"] = 8
    if not down:
        return

    if g.state == "lesson" and key in (pygame.K_1, pygame.K_2, pygame.K_3):
        g.lesson_answer(key - pygame.K_1)
        return
    if g.state == "menu" and key in (pygame.K_1, pygame.K_2, pygame.K_3):
        g.pick = ["normal", "hard", "endless"][key - pygame.K_1]
        g.start_run(g.pick)
        return
    if key in (pygame.K_e, pygame.K_q, pygame.K_DOWN, pygame.K_LSHIFT):
        if g.state == "play" and not g.ring_bell():
            g.use_item()
    elif key == pygame.K_r:
        if g.state == "play":
            g.kill_player(True)
        elif g.state in ("menu", "win", "over"):
            g.start_run(g.diff["key"])
    elif key in (pygame.K_p, pygame.K_ESCAPE):
        if g.state == "play":
            g.state = "paused"
        elif g.state == "paused":
            g.state = "play"
        elif g.state in ("mods", "settings", "shop", "records", "seedin", "code", "admin"):
            do_button(g, "back")
    elif key == pygame.K_m:
        do_button(g, "sound")
    elif key == pygame.K_o and g.state in ("menu", "mods"):
        g.state = "menu" if g.state == "mods" else "mods"
        g.back = "menu"
    elif key == pygame.K_f:
        do_button(g, "full")
    elif key == pygame.K_RETURN:
        if g.state == "menu":
            g.start_run(g.pick)
        elif g.state in ("win", "over"):
            do_button(g, "again")


# ================== КАДР ==================
def render(surf, g):
    g.buttons = []
    if g.state == "lesson":
        draw_lesson(surf, g)
        draw_toast(surf, g)
        draw_ach(surf, g)
        return
    if g.state == "menu":
        draw_menu(surf, g)
    else:
        if g.level:
            draw_world(surf, g)
            draw_hud(surf, g)
        else:
            draw_menu(surf, g)
    if g.state == "clear":
        draw_clear(surf, g)
    elif g.state == "paused":
        draw_paused(surf, g)
    elif g.state in ("win", "over"):
        draw_end(surf, g)
    if g.state == "mods":
        draw_mods(surf, g)
    elif g.state == "settings":
        draw_settings(surf, g)
    elif g.state == "seedin":
        draw_seed(surf, g)
    elif g.state == "shop":
        draw_shop(surf, g)
    elif g.state == "code":
        draw_code(surf, g)
    elif g.state == "admin":
        draw_admin(surf, g)
    elif g.state == "records":
        draw_records(surf, g)
    draw_toast(surf, g)
    draw_ach(surf, g)


def main():
    pygame.init()
    pick_font()
    flags = pygame.SCALED | pygame.RESIZABLE
    screen = pygame.display.set_mode((VW, VH), flags)
    pygame.display.set_caption("Перемена — 15 минут свободы")
    clock = pygame.time.Clock()
    SAVE.day_streak()
    g = Game()
    g.save_and_check()
    acc = 0.0
    running = True
    while running:
        dt = min(0.1, clock.tick(60) / 1000.0)
        acc += dt * (1.2 if mod("fastgame") else 1.0)
        guard = 0
        while acc >= STEP and guard < 5:
            g.update(STEP)
            acc -= STEP
            guard += 1
        if guard >= 5:
            acc = 0.0

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                on_key(g, ev.key, True)
            elif ev.type == pygame.KEYUP:
                on_key(g, ev.key, False)
            elif ev.type == pygame.MOUSEMOTION:
                g.mouse = ev.pos
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                g.mouse = ev.pos
                click_at(g, ev.pos)

        render(screen, g)
        pygame.display.flip()

    SAVE.save()
    pygame.quit()


if __name__ == "__main__":
    main()
