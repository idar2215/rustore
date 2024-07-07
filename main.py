import telebot
from telebot import types

# Замените этот токен на ваш реальный токен бота
TOKEN = '123456789:AaBbHopkwjp3293ikd'

bot = telebot.TeleBot(TOKEN)

# Отключаем вебхук (если он был установлен ранее)
try:
    bot.delete_webhook()
except Exception as e:
    print(f"Ошибка при удалении вебхука: {e}")

# Стартовая клавиатура с кнопкой "Соединить с оператором"
start_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
start_keyboard.add(types.KeyboardButton("Соединить с оператором"))

# Клавиатура для завершения диалога
end_dialog_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
end_dialog_keyboard.add(types.KeyboardButton("Завершить диалог"))

# Клавиатура для оператора с кнопками "Принять" и "Отклонить"
operator_keyboard = types.InlineKeyboardMarkup()
operator_keyboard.add(types.InlineKeyboardButton("Принять", callback_data='accept'),
                      types.InlineKeyboardButton("Отклонить", callback_data='reject'))

# Словарь для хранения операторов и их статуса
operators = {}  # {operator_id: {'status': 'free', 'stats': {'accepted': 0, 'rejected': 0}}}

# Словарь для хранения активных диалогов
active_dialogs = {}  # {user_id: operator_id}

# Список администраторов
admins = [1234567, 2314685]  # Замените ID на реальные ID администраторов

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "Привет! 👋", reply_markup=start_keyboard)

# Обработчик кнопки "Соединить с оператором"
@bot.message_handler(func=lambda message: message.text == "Соединить с оператором")
def connect_operator(message):
    user_id = message.from_user.id
    free_operator = None
    for operator_id, data in operators.items():
        if data['status'] == 'free':
            free_operator = operator_id
            break

    if free_operator:
        bot.send_message(free_operator, "Нужна помощь!", reply_markup=operator_keyboard)
        active_dialogs[user_id] = free_operator
        operators[free_operator]['status'] = 'busy'
        bot.send_message(user_id, "Ожидайте, оператор скоро подключится!")
    else:
        bot.send_message(user_id, "К сожалению, все операторы заняты. Попробуйте позже.")

# Обработчик callback-запросов от кнопок оператора
@bot.callback_query_handler(func=lambda call: call.data in ['accept', 'reject'])
def handle_operator_choice(call):
    operator_id = call.from_user.id
    user_id = None
    for uid, oid in active_dialogs.items():
        if oid == operator_id:
            user_id = uid
            break
    
    if call.data == 'accept' and user_id:
        bot.send_message(user_id, "Оператор подключился!", reply_markup=end_dialog_keyboard)
        bot.send_message(operator_id, "Вы подключены к пользователю. Можете начинать диалог.")
        operators[operator_id]['stats']['accepted'] += 1
    elif call.data == 'reject' and user_id:
        bot.send_message(user_id, "К сожалению, оператор не смог принять ваш запрос. Попробуйте позже.")
        bot.send_message(operator_id, "Запрос отклонен.")
        operators[operator_id]['stats']['rejected'] += 1
        operators[operator_id]['status'] = 'free'
        del active_dialogs[user_id]

# Обработчик кнопки "Завершить диалог"
@bot.message_handler(func=lambda message: message.text == "Завершить диалог")
def end_dialog(message):
    user_id = message.from_user.id
    operator_id = active_dialogs.get(user_id)
    if operator_id:
        bot.send_message(operator_id, "Диалог завершен.")
        operators[operator_id]['status'] = 'free'
        del active_dialogs[user_id]
        bot.send_message(user_id, "Диалог завершен. Спасибо!")
    else:
        bot.send_message(user_id, "Вы не в диалоге с оператором.")

# Обработчик команды /add_operator
@bot.message_handler(commands=['add_operator'])
def add_operator(message):
    user_id = message.from_user.id
    if user_id in admins:
        text = message.text.split()
        if len(text) > 1:
            operator_id = int(text[1])
            operators[operator_id] = {'status': 'free', 'stats': {'accepted': 0, 'rejected': 0}}
            bot.send_message(user_id, f"Оператор {operator_id} добавлен.")
        else:
            bot.send_message(user_id, "Пожалуйста, укажите ID оператора.")
    else:
        bot.send_message(user_id, "У вас нет прав на добавление операторов.")

# Обработчик команды /add_admin
@bot.message_handler(commands=['add_admin'])
def add_admin(message):
    user_id = message.from_user.id
    if user_id in admins:
        text = message.text.split()
        if len(text) > 1:
            admin_id = int(text[1])
            admins.append(admin_id)
            bot.send_message(user_id, f"Администратор {admin_id} добавлен.")
        else:
            bot.send_message(user_id, "Пожалуйста, укажите ID администратора.")
    else:
        bot.send_message(user_id, "У вас нет прав на добавление администраторов.")

# Обработчик команды /operator_stats
@bot.message_handler(commands=['operator_stats'])
def show_operator_stats(message):
    user_id = message.from_user.id
    if user_id in admins:
        text = message.text.split()
        if len(text) > 1:
            operator_id = int(text[1])
            if operator_id in operators:
                stats = operators[operator_id]['stats']
                bot.send_message(user_id, f"Статистика оператора {operator_id}:\nПринято запросов: {stats['accepted']}\nОтклонено запросов: {stats['rejected']}")
            else:
                bot.send_message(user_id, "Такого оператора не существует.")
        else:
            bot.send_message(user_id, "Пожалуйста, укажите ID оператора.")
    else:
        bot.send_message(user_id, "У вас нет прав на просмотр статистики операторов.")

# Обработчик команды /mystats для операторов
@bot.message_handler(commands=['mystats'])
def show_my_stats(message):
    user_id = message.from_user.id
    if user_id in operators:
        stats = operators[user_id]['stats']
        bot.send_message(user_id, f"Ваша статистика:\nПринято запросов: {stats['accepted']}\nОтклонено запросов: {stats['rejected']}")
    else:
        bot.send_message(user_id, "Вы не являетесь оператором.")

# Перенаправление сообщений от пользователя к оператору и обратно
@bot.message_handler(func=lambda message: message.from_user.id in active_dialogs or message.from_user.id in operators)
def relay_messages(message):
    user_id = message.from_user.id
    if user_id in active_dialogs:
        operator_id = active_dialogs[user_id]
        bot.send_message(operator_id, message.text)
    elif user_id in operators:
        for uid, oid in active_dialogs.items():
            if oid == user_id:
                bot.send_message(uid, message.text)
                break

# Запускаем бота в режиме Long polling
bot.polling(none_stop=True)
