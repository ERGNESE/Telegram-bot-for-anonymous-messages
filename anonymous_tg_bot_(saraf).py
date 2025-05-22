import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = telebot.TeleBot('your_token_here')

thread_id = xxx #thread id, if you use a supergroup
group_chat_id = xxx #Your chat id
admins = [] #admins personal ID must be in lst

msg_id = 0  # message from bot to admin id
last_message_data = {}  # dictionary for database

''' #you can see your chat id by this command
@bot.message_handler(commands=['chat_id'])
def get_chat_id(message):
    bot.send_message(message.chat.id, f"Chat ID: {message.chat.id}")'''


@bot.message_handler(commands=['start'])
def start(message): #hello message
    bot.send_message(message.chat.id, "Бот активирован, ваше сообщение будет анонимно передано модерации, а затем опубликовано. Не злоупотребляйте :)")


@bot.message_handler(content_types=['text', 'photo', 'video']) #getting messages
def handle_input(message):
    if message.chat.type != "private": #messages must be from private chats only
        return

    global msg_id
    user_id = message.from_user.id
    msg_id += 1
#adding buttons
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Отправить", callback_data=f"send_to_group:{msg_id}"),
        InlineKeyboardButton("Удалить", callback_data=f"delete:{msg_id}")
    )

    msg_data = {
        'us_id': user_id,
        'admin_msgs': {}  # msgs sended to admins dict. Using it for deleting messages from all private chats with admins after moderation. {admin_id: bot_msg_id}
    }

    if message.photo:
        file_id = message.photo[-1].file_id
        caption = message.caption or ""
        msg_data.update({'type': 'photo', 'info': file_id, 'capt': caption})

    elif message.video:
        file_id = message.video.file_id
        caption = message.caption or ""
        msg_data.update({'type': 'video', 'info': file_id, 'capt': caption})

    elif message.text:
        msg_data.update({'type': 'text', 'info': message.text, 'capt': ''})

    #sending on moderation
    last_message_data[msg_id] = msg_data

    for admin_id in admins:
        try:
            if msg_data['type'] == 'text':
                sent = bot.send_message(admin_id, msg_data['info'], reply_markup=markup)
            elif msg_data['type'] == 'photo':
                sent = bot.send_photo(admin_id, msg_data['info'], caption=msg_data['capt'], reply_markup=markup)
            elif msg_data['type'] == 'video':
                sent = bot.send_video(admin_id, msg_data['info'], caption=msg_data['capt'], reply_markup=markup)

            msg_data['admin_msgs'][admin_id] = sent.message_id
        except Exception as e:
            print(f"Ошибка при отправке админу {admin_id}: {e}") #sending error

#button action

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    action, msg_key_str = call.data.split(':')
    msg_key = int(msg_key_str)

    if msg_key not in last_message_data:
        bot.send_message(user_id, "⚠️ Нет сохранённого сообщения.")
        return

    msg_data = last_message_data[msg_key]
    msg_type = msg_data['type']
    content = msg_data['info']
    caption = msg_data['capt']

    if action == "send_to_group":
        if msg_type == 'text':
            bot.send_message(group_chat_id, content, message_thread_id=thread_id)
        elif msg_type == 'photo':
            bot.send_photo(group_chat_id, content, caption=caption, message_thread_id=thread_id)
        elif msg_type == 'video':
            bot.send_video(group_chat_id, content, caption=caption, message_thread_id=thread_id)
        bot.send_message(user_id, "✅ Сообщение отправлено в группу.")

    elif action == "delete":
        bot.send_message(user_id, "🚫 Сообщение удалено.")

    # deleting message from private chat with admin after moderstion
    for admin_id in admins:
        try:
            bot_msg_id = msg_data['admin_msgs'].get(admin_id)
            if bot_msg_id:
                bot.delete_message(admin_id, bot_msg_id)
        except Exception as e:
            print(f"Ошибка удаления у {admin_id}: {e}")

    if action == "delete":
        del last_message_data[msg_key]


bot.infinity_polling()
