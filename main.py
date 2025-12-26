import telebot
from telebot import types
from datetime import datetime
import json

# ================== НАЛАШТУВАННЯ ==================
BOT_TOKEN = "8576990117:AAFj7NHUXQu-pCFmm1Z-K78Brc2EhLGnmho"
ADMIN_ID = 1952761674
CHANNEL_ID = "@plitkypidhaitsi"
SUPPORT_CHAT_ID = -4955378532
MODERATION_GROUP_ID = -4964196339
LOG_GROUP_ID = -5061472780
STATS_FILE = "user_stats.json"
# =================================================

bot = telebot.TeleBot(BOT_TOKEN)

# ================== Глобальні ==================
user_states = {}      # chat_id -> стан (anon, support)
joined_users = []     # всі user_id
anon_messages = {}    # message_id модерації -> user_id
banned_users = {}     # user_id -> True

# ================== Статистика ==================
try:
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        user_stats = json.load(f)
except FileNotFoundError:
    user_stats = {}

def save_stats():
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(user_stats, f, ensure_ascii=False, indent=4)

# ================== ДОПОМІЖНІ ==================
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except telebot.apihelper.ApiTelegramException:
        return False

def send_main_menu(chat_id):
    bot.send_message(chat_id, "🗂 <b>Головне меню</b> 👇", reply_markup=main_keyboard(), parse_mode="HTML")

def ask_subscribe(chat_id):
    bot.send_message(chat_id, "❌ <b>Ви не підписані на канал</b> 📌", reply_markup=subscribe_keyboard(), parse_mode="HTML")

# ================== КНОПКИ ==================
def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✉️ Анонімне повідомлення", "🛠️ Підтримка")
    kb.add("📊 Статистика", "❓ FAQ")
    kb.add("📰 Новини каналу")
    return kb

def back_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⬅️ Назад в меню")
    return kb

def subscribe_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔔 Підписатись", url=f"https://t.me/{CHANNEL_ID.replace('@','')}"))
    kb.add(types.InlineKeyboardButton("✅ Я підписався", callback_data="check_sub"))
    return kb

def admin_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Прийняти", callback_data="accept"),
        types.InlineKeyboardButton("❌ Відхилити", callback_data="reject")
    )
    return kb

# ================== START ==================
@bot.message_handler(commands=["start"])
def start(message):
    user_id = str(message.from_user.id)

    # Ініціалізація статистики
    if user_id not in user_stats:
        user_stats[user_id] = {
            "joined": datetime.now().strftime("%d.%m.%Y"),
            "anon_count": 0,
            "support_count": 0,
            "banned": False,
            "username": message.from_user.username
        }
        save_stats()

    # Логи нового користувача
    if user_id not in joined_users:
        joined_users.append(user_id)
        try:
            bot.send_message(
                LOG_GROUP_ID,
                f"👤 <b>Новий користувач приєднався</b>\n"
                f"№ {len(joined_users)}\n"
                f"ID: {user_id}\n"
                f"Username: @{message.from_user.username if message.from_user.username else 'немає'}",
                parse_mode="HTML"
            )
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Помилка надсилання логу: {e}")

    # Перевірка підписки
    if not is_subscribed(message.from_user.id):
        ask_subscribe(message.chat.id)
        return

    send_main_menu(message.chat.id)

# ================== CALLBACK ==================
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    if is_subscribed(call.from_user.id):
        bot.edit_message_text("✅ <b>Доступ відкрито!</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        send_main_menu(call.message.chat.id)
    else:
        bot.answer_callback_query(call.id, "❌ Ви ще не підписались")

# ================== НАЗАД ==================
@bot.message_handler(func=lambda m: m.text.strip() == "⬅️ Назад в меню")
def back_menu(message):
    user_states.pop(message.chat.id, None)
    send_main_menu(message.chat.id)

# ================== СТАТИСТИКА ==================
@bot.message_handler(func=lambda m: m.text.strip() == "📊 Статистика")
def stats(message):
    user_id = str(message.from_user.id)
    s = user_stats.get(user_id)
    if not s:
        bot.send_message(message.chat.id, "❌ Дані не знайдені", parse_mode="HTML")
        return
    bot.send_message(
        message.chat.id,
        f"📊 <b>Ваша статистика</b>\n\n"
        f"📅 Дата приєднання: <code>{s['joined']}</code>\n"
        f"✉️ Анонімні повідомлення: <b>{s['anon_count']}</b>\n"
        f"🛠️ Підтримка: <b>{s['support_count']}</b>\n"
        f"🚫 Заблокований: <i>{'Так' if s['banned'] else 'Ні'}</i>",
        parse_mode="HTML"
    )

# ================== FAQ ==================
@bot.message_handler(func=lambda m: m.text.strip() == "❓ FAQ")
def faq(message):
    if not is_subscribed(message.from_user.id):
        ask_subscribe(message.chat.id)
        return
    bot.send_message(
        message.chat.id,
        "❓ <b>FAQ</b>\n\n• Усі повідомлення анонімні\n• Адміністратор не бачить автора\n• Повідомлення проходять модерацію",
        parse_mode="HTML"
    )

# ================== NEWS ==================
@bot.message_handler(func=lambda m: m.text.strip() == "📰 Новини каналу")
def news(message):
    if not is_subscribed(message.from_user.id):
        ask_subscribe(message.chat.id)
        return
    bot.send_message(
        message.chat.id,
        f"📰 <b>Новини каналу</b>\nhttps://t.me/{CHANNEL_ID.replace('@', '')}",
        parse_mode="HTML"
    )

# ================== АНОНІМНЕ ==================
@bot.message_handler(func=lambda m: m.text.strip() == "✉️ Анонімне повідомлення")
def anon_start(message):
    user_id = str(message.from_user.id)
    if user_stats[user_id]["banned"]:
        bot.send_message(message.chat.id, "🚫 <b>Вам заборонено надсилати анонімні повідомлення</b>", parse_mode="HTML")
        return
    user_states[message.chat.id] = "anon"
    bot.send_message(message.chat.id, "✍️ <b>Напишіть повідомлення:</b>", reply_markup=back_keyboard(), parse_mode="HTML")

@bot.message_handler(func=lambda m: user_states.get(m.chat.id) == "anon" and m.text.strip() != "⬅️ Назад в меню")
def anon_receive(message):
    user_states.pop(message.chat.id, None)
    user_id = str(message.from_user.id)
    user_stats[user_id]["anon_count"] += 1
    save_stats()
    user_info = f"@{message.from_user.username}" if message.from_user.username else f"ID:{message.from_user.id}"
    try:
        msg = bot.send_message(
            MODERATION_GROUP_ID,
            f"{message.text}\n\n👤 Автор: {user_info}",
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        anon_messages[msg.message_id] = message.from_user.id
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Помилка надсилання анонімного повідомлення: {e}")
    send_main_menu(message.chat.id)

# ================== ПІДТРИМКА ==================
@bot.message_handler(func=lambda m: m.text.strip() == "🛠️ Підтримка")
def support_start(message):
    user_states[message.chat.id] = "support"
    bot.send_message(message.chat.id, "🛠️ <b>Опишіть вашу проблему:</b>", reply_markup=back_keyboard(), parse_mode="HTML")

@bot.message_handler(func=lambda m: user_states.get(m.chat.id) == "support" and m.text.strip() != "⬅️ Назад в меню")
def support_receive(message):
    user_states.pop(message.chat.id, None)
    user_id = str(message.from_user.id)
    user_stats[user_id]["support_count"] += 1
    save_stats()
    try:
        bot.send_message(SUPPORT_CHAT_ID, f"🛠️ <b>ПІДТРИМКА</b>:\n\n{message.text}\n\n🆔 {message.from_user.id}", parse_mode="HTML")
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Помилка надсилання підтримки: {e}")
    send_main_menu(message.chat.id)

# ================== МОДЕРАЦІЯ ==================
@bot.callback_query_handler(func=lambda call: call.data in ["accept", "reject"])
def admin_actions(call):
    if call.message.chat.id != MODERATION_GROUP_ID:
        return

    raw_text = call.message.text
    # Беремо лише текст повідомлення користувача
    clean_text = raw_text.split("\n\n👤 Автор")[0]

    if call.data == "accept":
        markup_channel = types.InlineKeyboardMarkup()
        markup_channel.add(
            types.InlineKeyboardButton("❓ Залишити анонімне повідомлення", url="https://t.me/PlitkyPidhaitsiBot")
        )
        try:
            bot.send_message(
                CHANNEL_ID,
                f"📢 <b>Анонімно:</b>\n\n{clean_text}",
                reply_markup=markup_channel,
                parse_mode="HTML"
            )
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Помилка публікації в канал: {e}")

        markup_admin = types.InlineKeyboardMarkup()
        markup_admin.add(types.InlineKeyboardButton(text="Прийнято ✅", callback_data="done"))
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup_admin)

    elif call.data == "reject":
        markup_admin = types.InlineKeyboardMarkup()
        markup_admin.add(types.InlineKeyboardButton(text="Відхилено ❌", callback_data="done"))
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup_admin)

# ================== БАН/РОЗБАН ==================
@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        username = message.text.split()[1].replace("@","")
        user_id = next((uid for uid, info in user_stats.items() if info.get("username") == username), None)
        if not user_id:
            bot.send_message(message.chat.id, f"❌ Користувач @{username} не знайдений", parse_mode="HTML")
            return
        user_stats[user_id]["banned"] = True
        save_stats()
        bot.send_message(message.chat.id, f"✅ Користувач @{username} заблокований", parse_mode="HTML")
    except IndexError:
        bot.send_message(message.chat.id, "❌ Використання: /ban <username>", parse_mode="HTML")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        username = message.text.split()[1].replace("@","")
        user_id = next((uid for uid, info in user_stats.items() if info.get("username") == username), None)
        if not user_id:
            bot.send_message(message.chat.id, f"❌ Користувач @{username} не знайдений", parse_mode="HTML")
            return
        user_stats[user_id]["banned"] = False
        save_stats()
        bot.send_message(message.chat.id, f"✅ Користувач @{username} розблокований", parse_mode="HTML")
    except IndexError:
        bot.send_message(message.chat.id, "❌ Використання: /unban <username>", parse_mode="HTML")

# ================== ЗАПУСК ==================
print("🤖 Бот запущений")
bot.infinity_polling()
