import random
import time
import asyncio
from datetime import datetime

from config import TOKEN
from Data_base import *
import telebot
from telebot.types import Message, ReplyKeyboardMarkup as RKM, ReplyKeyboardRemove as RKRe, InlineKeyboardMarkup as IKM, \
    InlineKeyboardButton as IKB, CallbackQuery as CBQ

bot = telebot.TeleBot(TOKEN)
temp = {}
clear = RKRe()


class Enemy:
    enemies = {
        "Разбойник": (75, 7.5),
        "Циклоп": (125, 7.5),
        "Темный рыцарь": (150, 10.0),
        "Силач": (100, 11.0),
        "Акробат": (200, 4.5),
        "Гвардеец": (80, 9.0),
        "Мечник": (75, 11.5),
        "Менестрель": (60, 4.0),
        "Медик": (150, 5.5)
    }

    def __init__(self, hero_lvl: int):
        self.name = random.choice(list(self.enemies))
        self.hp = self.enemies[self.name][0] + (hero_lvl - 1) * 5
        self.dmg = self.enemies[self.name][1] + (hero_lvl - 1) * 0.25


@bot.message_handler(commands=["start"])
def start(m: Message):
    if new_plr(m):
        temp[m.chat.id] = {}
        reg0(m)
        return
    else:
        menu(m)
        return


@bot.message_handler(commands=["menu"])
def menu(m: Message):
    try:
        print(temp[m.chat.id])
    except KeyError:
        temp[m.chat.id] = {}
    txt = "что будешь делать?\n/home - пойти домой\n/square - пойти на главную площадь\n/stats - статистика"
    bot.send_message(m.chat.id, txt, reply_markup=clear)


@bot.message_handler(commands=["home"])
def home(m: Message):
    kb = RKM(True, True)
    kb.row("поспать", "поесть")
    bot.send_message(m.chat.id, "Что ты хочешь сделать?", reply_markup=kb)
    bot.register_next_step_handler(m, reg3)


@bot.message_handler(commands=["stats"])
def stats(m: Message):
    player = carachters.read("user_id", m.chat.id)
    txt = (f"hp - {player[-4]}❤\n"
           f"dmg - {player[-3]}❤\n"
           f"lvl - {player[-2]}🟢\n"
           f"exp - {player[-1]}🟢")
    bot.send_message(m.chat.id, txt)
    asyncio.run(asyncio.sleep(4))
    menu(m)
    return


@bot.message_handler(commands=["square"])
def square(m: Message):
    kb = RKM(True, True)
    kb.row("тренировка", "прокачка ловкости", 'пойти в путешествие')
    bot.send_message(m.chat.id,
                     'Придя на площадь, путник увидел стрельбище, манекенов, набитых сеном, чтобы тренировать '
                     'ближний бой, замысловатую полосу препятствий для прокачки ловкости и поле, за ним был вход в лес,'
                     ' где можно найти приключений. Что ты хочешь сделать?', reply_markup=kb)
    bot.register_next_step_handler(m, reg3)


@bot.callback_query_handler(func=lambda call: True)
def call_back(call: CBQ):
    if call.data.startswith("food_"):
        a = call.data.split(sep="_")
        eating(call.message, a[1], a[-1])
        kb = IKM()
        id, food = heals.read("user_id", call.message.chat.id)
        flag = 0
        for i in food:
            if food[i][0] == 0:
                pass
            elif food[i][0] > 0:
                flag = 1
        if flag == 0:
            bot.send_message(call.message.chat.id, "'... Больше есть как-то нечего...(Добыть еду можно в путешествии)'")
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
            menu(call.message)
            return
        else:
            for key in food:
                if food[key][0] > 0:
                    kb.row(
                        IKB(f"{key} - {food[key][0]} шт; {food[key][-1]} хп",
                            callback_data=f"food_{key}_{food[key][-1]}"))
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=kb)
    elif call.data.startswith("sleep_"):
        a = call.data.split(sep="_")
        t = round(int(a[1]) / 10, 0)
        bot.send_message(call.message.chat.id, f"Вы будете спать {t} сек.")
        asyncio.run(asyncio.sleep(t))
        sleeping(call.message, a[1])
        bot.delete_message(call.message.chat.id, call.message.message_id)
        menu(call.message)
        return
    if call.data == "workout":
        player = carachters.read("user_id", call.message.chat.id)
        dmg = int(player[-2]) / 10
        player[-3] += dmg
        player[-3] = round(player[-3], 1)
        carachters.write(player)
        bot.answer_callback_query(call.id, f"Ух... Хорошая тренировочка выдалась) (+ {dmg}dmg)", True)
    elif call.data == "menu":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        menu(call.message)
        return


def eat(m: Message):
    kb = IKM()
    id, food = heals.read("user_id", m.chat.id)
    flag = 0
    for i in food:
        if food[i][0] == 0:
            pass
        elif food[i][0] > 0:
            flag = 1
    if flag == 0:
        bot.send_message(m.chat.id, "'... Да... А в погребе мышь повесилась...(Добыть еду можно в путешествии)'")
        menu(m)
        return
    else:
        for key in food:
            if food[key][0] > 0:
                kb.row(
                    IKB(f"{key} - {food[key][0]} шт; {food[key][-1]} хп", callback_data=f"food_{key}_{food[key][-1]}"))
        bot.send_message(m.chat.id, "Что будешь есть?", reply_markup=kb)


def eating(m: Message, food_type, hp):
    id, food = heals.read("user_id", m.chat.id)
    player = carachters.read("user_id", m.chat.id)
    if food[food_type][0] == 1:
        del food[food_type]
    else:
        food[food_type][0] -= 1
    heals.write([m.chat.id, food])
    player[3] += int(hp)
    carachters.write(player)
    print("поели")


def sleep(m: Message):
    player = carachters.read("user_id", m.chat.id)
    low = int(races[player[2]][0] + ((player[-2] - 1) * 5)) // 2 - player[3]
    high = int(races[player[2]][0] + ((player[-2] - 1) * 5)) - player[3]
    if low > 0 or high > 0:
        kb = IKM()
        if low > 0:
            kb.row(IKB(f"Подремать: +{low}❤", callback_data=f"sleep_{low}"))
        if high > 0:
            kb.row(IKB(f"Давануть храпака: +{high}❤", callback_data=f"sleep_{high}"))
        bot.send_message(m.chat.id, "Cколько ты будешь спать?", reply_markup=kb)
    else:
        bot.send_message(m.chat.id, "Тебе не нужно спать")
        menu(m)
        return


def sleeping(m: Message, hp):
    player = carachters.read("user_id", m.chat.id)
    player[3] += int(hp)
    carachters.write(player)
    print("поспали")


def workout(m: Message):
    kb = IKM()
    kb.row(IKB("тренироваться", callback_data="workout"))
    kb.row(IKB("назад", callback_data="menu"))
    bot.send_message(m.chat.id, '"интересно, интересно... и что здесь делать...?"', reply_markup=kb)


def block(m: Message):
    try:
        print(temp[m.chat.id])
    except KeyError:
        temp[m.chat.id] = {}
    try:
        print(temp[m.chat.id]['win'])
    except KeyError:
        temp[m.chat.id]['win'] = 0
    if temp[m.chat.id]['win'] == 0:
        bot.send_message(m.chat.id, "Шпаги наголо, дворяне!", reply_markup=clear)
    asyncio.run(asyncio.sleep(3))
    sides = ["слева", "справа", "сверху", "снизу"]
    random.shuffle(sides)
    kb = RKM(True, False)
    kb.row(sides[0], sides[1])
    kb.row(sides[2], sides[-1])
    hit = sides[random.randint(0, 3)]
    bot.send_message(m.chat.id, f"Осторожнее, сударь, {hit}!", reply_markup=kb)
    temp[m.chat.id]["start_t"] = datetime.now().timestamp()
    bot.register_next_step_handler(m, block_handler, hit)


def block_handler(m: Message, hit: str):
    temp[m.chat.id]["finish_t"] = datetime.now().timestamp()
    if temp[m.chat.id]["finish_t"] - temp[m.chat.id]["start_t"] > 2.5:
        bot.send_message(m.chat.id, "Ты не успел уклониться")
        asyncio.run(asyncio.sleep(1))
        temp[m.chat.id]['win'] = 0
        menu(m)
        return
    if m.text != hit:
        bot.send_message(m.chat.id, "Ты уклонился не в ту сторону")
        asyncio.run(asyncio.sleep(1))
        temp[m.chat.id]['win'] = 0
        menu(m)
        return
    if temp[m.chat.id]['win'] < 9:
        temp[m.chat.id]['win'] += 1
        bot.send_message(m.chat.id, "А ты неплох) еще разок!")
        block(m)
        return
    else:
        temp[m.chat.id]['win'] = 0
        player = carachters.read("user_id", m.chat.id)
        exp = player[-2] * 10 - player[-2] * 2
        player[-1] += exp
        carachters.write(player)
        lvl_up_check(m)
        bot.send_message(m.chat.id, f"Сударь, я вас поздравляю, вы прошли данное испытание!)(+ {exp} exp)")
        menu(m)
        return


def battle(m: Message):
    bot.send_message(m.chat.id, f"Ты встретил врага на дороге, он выскочил из-за куста")
    asyncio.run(asyncio.sleep(2.3))
    new_enemy(m)


def new_enemy(m: Message):
    player = carachters.read("user_id", m.chat.id)
    enemy = Enemy(player[-2])
    kb = RKM(True, True)
    kb.row("Драться", "Пафосно пройти мимо")
    kb.row("Вернуться в город")
    txt = f'"Хм... Что же мне делать...? Мой враг: {enemy.name}"'
    bot.send_message(m.chat.id, txt, reply_markup=kb)
    bot.register_next_step_handler(m, attack_handler, enemy)


def attack_handler(m: Message, enemy):
    txt = m.text
    chance = random.randint(1, 6)
    if txt == "Драться":
        attack(m, enemy)
        return
    elif txt == "Пафосно пройти мимо":
        if chance != 6:
            bot.send_message(m.chat.id, f"Ты встречаешь нового врага: {enemy.name}")
            asyncio.run(asyncio.sleep(2))
            new_enemy(m)
            return
        else:
            bot.send_message(m.chat.id, "Эй, сударь, я вас не понял, куда вы идете?! Сейчас мы с вами будем драться!")
            asyncio.run(asyncio.sleep(2))
            attack(m, enemy)
            return
    elif txt == "Вернуться в город":
        asyncio.run(asyncio.sleep(2.3))
        menu(m)
        return


def attack(m: Message, enemy):
    if attack_plr(m, enemy):
        if attack_enemy(m, enemy):
            attack(m, enemy)
    else:
        player = carachters.read("user_id", m.chat.id)
        player[-1] += random.randint(5, 7) * player[-2]
        carachters.write(player)
        asyncio.run(asyncio.sleep(1))
        lvl_up_check(m)
        asyncio.run(asyncio.sleep(1))
        bot.send_message(m.chat.id, "Да, нелегко было, пойду дальше)")
        asyncio.run(asyncio.sleep(3))
        battle(m)
        return


def attack_plr(m: Message, enemy):
    food_chance = random.randint(0,1)
    crit = random.randint(0, 499)
    print(food_chance)
    if enemy.name == "Циклоп" and crit == 499:
        enemy.hp = 0
        bot.send_message(m.chat.id, "Ха-ха! Так тебе, громила! Знать будешь! Это было замечательно!")
        if food_chance == 1:

            id, food = heals.read("user_id", m.chat.id)
            food[random.choice(list(food))][0] += random.randint(1, 2)
            heals.write([m.chat.id, food])
            bot.send_message(m.chat.id, "Так у тебя еще и еда была, а ты не поделился?! Что ж, ты все равно уже мертв)")
        return False
    else:
        player = carachters.read("user_id", m.chat.id)
        dmg = player[-3]
        chance = random.randint(1, 20)
        if chance == 1:
            bot.send_message(m.chat.id, "Эх, промазал...")
            return True
        elif chance == 20:
            bot.send_message(m.chat.id, "Ой, хорошо! Какой удар!")
            enemy.hp -= dmg * 1.5
        else:
            enemy.hp -= dmg
        if enemy.hp <= 0:
            bot.send_message(m.chat.id, "Ура, победа!")
            if food_chance == 1:
                id, food = heals.read("user_id", m.chat.id)
                food[random.choice(list(food))][0] += random.randint(1,2)
                heals.write([m.chat.id, food])
                bot.send_message(m.chat.id, "Так у тебя еще и еда была, а ты не поделился?! Что ж, ты все равно уже мертв)")
            return False
        else:
            bot.send_message(m.chat.id, f"Не помер, гад!(еще {enemy.hp}hp)")
            return True


def attack_enemy(m: Message, enemy):
    player = carachters.read("user_id", m.chat.id)
    crit = random.randint(0, 499)
    if enemy.name == "Медик" and crit == 499:
        enemy.hp = enemy.enemies[enemy.name][0] + (player[-2] - 1) * 5
        bot.send_message(m.chat.id, "Так ты еще и вылечился, гадина!")
    hp = player[-4]
    chance = random.randint(1, 20)
    if chance == 1:
        bot.send_message(m.chat.id, "Эх, промазал...) Ну ничего, будет и на твоей улице праздник)")
        return True
    elif chance == 20:
        bot.send_message(m.chat.id, "Ай... Хорошо...! Какой удар! Молодец!)")
        hp -= enemy.dmg * 1.5
    else:
        hp -= enemy.dmg
    if hp <= 0:
        die(m)
        return
    else:
        player[-4] = hp
        carachters.write(player)
        bot.send_message(m.chat.id, f"Не помер, хорошо!(еще {hp}hp)")
        return True


def new_plr(m: Message):
    db = carachters.read_all()
    for i in db:
        if m.chat.id == i[0]:
            return False
    return True


def reg0(m: Message):
    txt_nik = "Здравствуй, путник, как мне тебя называть?"
    bot.send_message(m.chat.id, txt_nik)
    bot.register_next_step_handler(m, reg1)


def reg1(m: Message):
    temp[m.chat.id]["nik"] = m.text
    kb = RKM(True, True)
    for race in list(races):
        kb.add(race)
    bot.send_message(m.chat.id, f"Неплохое имя, {m.text}. А какова будет твоя раса?", reply_markup=kb)
    bot.register_next_step_handler(m, reg2)


def reg2(m: Message):
    race_choice = m.text
    hp, damage = races[race_choice]
    carachters.write([m.chat.id, temp[m.chat.id]['nik'], race_choice, hp, damage, 1, 0])
    heals.write([m.chat.id, {
        "яблоко": [0, 3],
        "пирожок с картошкой": [0, 5],
        "сендвич с курицей": [0, 7],
        "бутерброд": [0, 6],
        "вяленая вобла": [0, 4]}])
    time.sleep(2)
    menu(m)
    return


def reg3(m: Message):
    if m.text == "поспать":
        sleep(m)
    elif m.text == "поесть":
        eat(m)
    elif m.text == "тренировка":
        workout(m)
    elif m.text == "прокачка ловкости":
        block(m)
    elif m.text == 'пойти в путешествие':
        battle(m)
    else:
        bot.send_message(m.chat.id, "Такого действия нет")
        menu(m)
        return


def lvl_up_check(m: Message):
    player = carachters.read("user_id", m.chat.id)
    max_exp = 100 + (player[-2] - 1) * 10
    if player[-1] >= max_exp:
        player[-1] -= max_exp
        player[-2] += 1
        player[4] += 1 * player[-2]
        player[3] = races[player[2]][0] + 5 * (player[-2] - 1)
        carachters.write(player)
        bot.send_message(m.chat.id, "(роботизированное эхо в голове) Ваш уровень повышен, поздравляю")
    return


def die(m: Message):
    bot.send_message(m.chat.id, "Заморили, черти...!"
                                "\n(роботизированное эхо в голове) Cпасибо за участие в испытании нашей симуляции, ваш персонаж "
                                "умер, перезапускаю систему")
    for i in range(10, 0, -1):
        asyncio.run(asyncio.sleep(1))
        if i == 10:
            bot.send_message(m.chat.id, "Подождите чуть-чуть, я загружаю новую симуляцию...")
        elif i == 1:
            bot.send_message(m.chat.id, "Готово")
        else:
            bot.send_message(m.chat.id, "...")
    heals.delete_row("user_id", m.chat.id)
    carachters.delete_row("user_id", m.chat.id)
    start(m)
    return


bot.infinity_polling()
