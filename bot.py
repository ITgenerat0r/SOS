import telebot
from telebot import types
from datetime import datetime, timedelta
import re
from database import Database
from config import BOT_TOKEN

# Инициализация бота и базы данных
bot = telebot.TeleBot(BOT_TOKEN)
db = Database()
db.create_tables()

# Состояния пользователей
user_states = {}
user_data = {}

# Состояния
STATES = {
    'WAITING_PASSWORD': 'waiting_password',
    'CREATING_BANNER_MESSAGE': 'creating_banner_message',
    'CREATING_BANNER_DATE': 'creating_banner_date',
    'CREATING_BANNER_RECEIVERS': 'creating_banner_receivers',
    'EDITING_BANNER_MESSAGE': 'editing_banner_message',
    'EDITING_BANNER_DATE': 'editing_banner_date',
    'EDITING_BANNER_RECEIVERS': 'editing_banner_receivers',
    'CHANGING_PASSWORD_OLD': 'changing_password_old',
    'CHANGING_PASSWORD_NEW': 'changing_password_new',
    'SELECTING_BANNER': 'selecting_banner',
    'CONFIRMING_DELETION': 'confirming_deletion',
    'EDITING_SELECT_BANNER': 'editing_select_banner',
    'EDITING_MESSAGE_INPUT': 'editing_message_input',
    'EDITING_DATE_INPUT': 'editing_date_input',
    'EDITING_RECEIVERS_INPUT': 'editing_receivers_input',
    'TOGGLE_BANNER_SELECT': 'toggle_banner_select',
    'CHOOSING_RECEIVERS_METHOD': 'choosing_receivers_method',
    'SELECTING_CONTACTS': 'selecting_contacts'
}

def delete_message_after_delay(chat_id, message_id, delay=0.5):
    """Удаление сообщения через задержку"""
    import threading
    def delete():
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
    timer = threading.Timer(delay, delete)
    timer.start()

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    
    if db.user_exists(user_id):
        bot.reply_to(message, "Вы уже зарегистрированы в системе!")
        show_main_menu(message.chat.id)
        return
    
    msg = bot.reply_to(message, "Добро пожаловать! Придумайте пароль для своей учетной записи:")
    user_states[user_id] = STATES['WAITING_PASSWORD']
    user_data[user_id] = {}
    bot.register_next_step_handler(msg, process_password)

@bot.message_handler(commands=['get_login'])
def get_login_command(message):
    user_id = message.from_user.id
    bot.reply_to(message, f"Ваш ID пользователя: {user_id}")

def process_password(message):
    user_id = message.from_user.id
    password = message.text
    
    # Удаляем сообщение с паролем
    delete_message_after_delay(message.chat.id, message.message_id)
    
    if len(password) < 4:
        msg = bot.reply_to(message, "Пароль должен быть не менее 4 символов. Попробуйте еще раз:")
        bot.register_next_step_handler(msg, process_password)
        return
    
    if db.create_user(user_id, message.from_user.username, message.from_user.first_name, password):
        bot.reply_to(message, "Регистрация завершена! Теперь вы можете использовать бота.")
        show_main_menu(message.chat.id)
        user_states.pop(user_id, None)
        user_data.pop(user_id, None)
    else:
        bot.reply_to(message, "Ошибка регистрации. Попробуйте позже.")

def show_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Создать сообщение', 'Показать все сообщения')
    markup.row('Редактировать сообщение', 'Активировать/Деактивировать')
    markup.row('Изменить пароль', 'Удалить сообщение')
    markup.row('Мой ID')
    bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'Создать сообщение')
def create_banner_start(message):
    user_id = message.from_user.id
    msg = bot.reply_to(message, "Введите текст сообщения:")
    user_states[user_id] = STATES['CREATING_BANNER_MESSAGE']
    user_data[user_id] = {}
    bot.register_next_step_handler(msg, process_banner_message)

def process_banner_message(message):
    user_id = message.from_user.id
    user_data[user_id]['message'] = message.text
    msg = bot.reply_to(message, "Введите дату и время отправки в формате ДД.ММ.ГГГГ ЧЧ:ММ (например, 25.12.2024 15:30):")
    user_states[user_id] = STATES['CREATING_BANNER_DATE']
    bot.register_next_step_handler(msg, process_banner_date)

def process_banner_date(message):
    user_id = message.from_user.id
    try:
        # Парсим дату
        date_str = message.text
        send_at = datetime.strptime(date_str, "%d.%m.%Y %H:%M")
        
        if send_at <= datetime.now():
            msg = bot.reply_to(message, "Дата должна быть в будущем. Попробуйте еще раз:")
            bot.register_next_step_handler(msg, process_banner_date)
            return
            
        user_data[user_id]['send_at'] = send_at
        show_receivers_menu(message.chat.id, user_id, "Выберите способ добавления получателей:")
    except ValueError:
        msg = bot.reply_to(message, "Неверный формат даты. Введите в формате ДД.ММ.ГГГГ ЧЧ:ММ:")
        bot.register_next_step_handler(msg, process_banner_date)

def show_receivers_menu(chat_id, user_id, text):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Выбрать из контактов', 'Добавить вручную')
    markup.row('Отмена')
    msg = bot.send_message(chat_id, text, reply_markup=markup)
    user_states[user_id] = 'CHOOSING_RECEIVERS_METHOD'
    bot.register_next_step_handler(msg, process_receivers_method)

def process_receivers_method(message):
    user_id = message.from_user.id
    
    if message.text == 'Выбрать из контактов':
        show_contacts_menu(message.chat.id, user_id)
    elif message.text == 'Добавить вручную':
        msg = bot.reply_to(message, "Введите ID получателей через запятую (например, 123456789, 987654321):")
        user_states[user_id] = STATES['CREATING_BANNER_RECEIVERS']
        bot.register_next_step_handler(msg, process_banner_receivers_manual)
    elif message.text == 'Отмена':
        show_main_menu(message.chat.id)
        user_states.pop(user_id, None)
        user_data.pop(user_id, None)
    else:
        show_receivers_menu(message.chat.id, user_id, "Пожалуйста, выберите один из вариантов:")

def show_contacts_menu(chat_id, user_id):
    try:
        # Отправляем запрос на получение контактов
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        contact_button = types.KeyboardButton('Поделиться контактом', request_contact=True)
        markup.add(contact_button)
        markup.row('Завершить выбор')
        markup.row('Назад')
        
        msg = bot.send_message(
            chat_id, 
            "Поделитесь контактами или нажмите 'Завершить выбор' когда добавите всех получателей.\n"
            "Нажмите 'Назад' для возврата к предыдущему меню.",
            reply_markup=markup
        )
        
        user_states[user_id] = STATES['SELECTING_CONTACTS']
        if 'selected_contacts' not in user_data[user_id]:
            user_data[user_id]['selected_contacts'] = []
        
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {str(e)}")
        show_receivers_menu(chat_id, user_id, "Ошибка. Попробуйте снова:")

@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    user_id = message.from_user.id
    
    # Проверяем, что это наш пользователь и он в нужном состоянии
    if user_states.get(user_id) == STATES['SELECTING_CONTACTS']:
        contact_user_id = message.contact.user_id
        contact_phone = message.contact.phone_number
        
        # Добавляем контакт в список выбранных
        if 'selected_contacts' not in user_data[user_id]:
            user_data[user_id]['selected_contacts'] = []
        
        # Проверяем, что контакт еще не добавлен
        if contact_user_id not in user_data[user_id]['selected_contacts']:
            user_data[user_id]['selected_contacts'].append(contact_user_id)
            bot.reply_to(message, f"Контакт добавлен! ID: {contact_user_id}, Телефон: {contact_phone}")
        else:
            bot.reply_to(message, f"Этот контакт уже добавлен!")
        
        # Показываем текущий список
        show_current_contacts(message.chat.id, user_id)
    else:
        show_main_menu(message.chat.id)

def show_current_contacts(chat_id, user_id):
    if user_data[user_id].get('selected_contacts'):
        contacts_list = "\n".join([f"• {contact_id}" for contact_id in user_data[user_id]['selected_contacts']])
        bot.send_message(chat_id, f"Выбранные контакты:\n{contacts_list}")

@bot.message_handler(func=lambda message: message.text == 'Завершить выбор')
def finish_contact_selection(message):
    user_id = message.from_user.id
    
    if user_states.get(user_id) == STATES['SELECTING_CONTACTS']:
        selected_contacts = user_data[user_id].get('selected_contacts', [])
        
        if not selected_contacts:
            bot.reply_to(message, "Вы не выбрали ни одного контакта!")
            show_contacts_menu(message.chat.id, user_id)
            return
        
        # Сохраняем выбранные контакты как получателей
        user_data[user_id]['receivers'] = selected_contacts
        
        # Запрашиваем пароль для подтверждения
        msg = bot.reply_to(message, "Введите ваш пароль для подтверждения создания сообщения:")
        user_states[user_id] = STATES['WAITING_PASSWORD']
        user_data[user_id]['next_action'] = 'create_banner'
        bot.register_next_step_handler(msg, process_action_password)
    else:
        show_main_menu(message.chat.id)

@bot.message_handler(func=lambda message: message.text == 'Назад')
def back_from_contacts(message):
    user_id = message.from_user.id
    if user_states.get(user_id) == STATES['SELECTING_CONTACTS']:
        show_receivers_menu(message.chat.id, user_id, "Выберите способ добавления получателей:")
        user_states[user_id] = 'CHOOSING_RECEIVERS_METHOD'
        # Очищаем выбранные контакты
        if 'selected_contacts' in user_data[user_id]:
            del user_data[user_id]['selected_contacts']

def process_banner_receivers_manual(message):
    user_id = message.from_user.id
    try:
        receivers = [int(x.strip()) for x in message.text.split(',')]
        user_data[user_id]['receivers'] = receivers
        
        # Запрашиваем пароль для подтверждения
        msg = bot.reply_to(message, "Введите ваш пароль для подтверждения создания сообщения:")
        user_states[user_id] = STATES['WAITING_PASSWORD']
        user_data[user_id]['next_action'] = 'create_banner'
        bot.register_next_step_handler(msg, process_action_password)
    except ValueError:
        msg = bot.reply_to(message, "Неверный формат ID. Введите через запятую:")
        bot.register_next_step_handler(msg, process_banner_receivers_manual)

def process_action_password(message):
    user_id = message.from_user.id
    password = message.text
    delete_message_after_delay(message.chat.id, message.message_id)
    
    if not db.check_password(user_id, password):
        bot.reply_to(message, "Неверный пароль!")
        user_states.pop(user_id, None)
        user_data.pop(user_id, None)
        show_main_menu(message.chat.id)
        return
    
    next_action = user_data[user_id].get('next_action')
    
    if next_action == 'create_banner':
        # Создаем баннер
        banner_id = db.create_banner(
            user_id, 
            user_data[user_id]['message'], 
            user_data[user_id]['send_at']
        )
        
        if banner_id:
            # Добавляем получателей
            for receiver_id in user_data[user_id]['receivers']:
                db.add_receiver(banner_id, receiver_id)
            
            bot.reply_to(message, f"Сообщение успешно создано! ID: {banner_id}")
        else:
            bot.reply_to(message, "Ошибка создания сообщения!")
    
    elif next_action == 'edit_message':
        banner_id = user_data[user_id]['banner_id']
        if db.update_banner_message(banner_id, user_data[user_id]['new_message']):
            bot.reply_to(message, "Сообщение успешно обновлено!")
        else:
            bot.reply_to(message, "Ошибка обновления сообщения!")
    
    elif next_action == 'edit_date':
        banner_id = user_data[user_id]['banner_id']
        if db.update_banner_send_at(banner_id, user_data[user_id]['new_date']):
            bot.reply_to(message, "Дата отправки успешно обновлена!")
        else:
            bot.reply_to(message, "Ошибка обновления даты!")
    
    elif next_action == 'edit_receivers':
        banner_id = user_data[user_id]['banner_id']
        # Удаляем старых получателей
        db.delete_banner_receivers(banner_id)
        # Добавляем новых
        for receiver_id in user_data[user_id]['new_receivers']:
            db.add_receiver(banner_id, receiver_id)
        bot.reply_to(message, "Получатели успешно обновлены!")
    
    elif next_action == 'change_password':
        if db.change_password(user_id, user_data[user_id]['new_password']):
            bot.reply_to(message, "Пароль успешно изменен!")
        else:
            bot.reply_to(message, "Ошибка изменения пароля!")
    
    elif next_action == 'delete_banner':
        banner_id = user_data[user_id]['banner_id']
        if db.delete_banner(banner_id):
            bot.reply_to(message, "Сообщение успешно удалено!")
        else:
            bot.reply_to(message, "Ошибка удаления сообщения!")
    
    elif next_action == 'toggle_banner':
        banner_id = user_data[user_id]['banner_id']
        is_active = user_data[user_id]['is_active']
        if db.toggle_banner_active(banner_id, is_active):
            status = "активировано" if is_active else "деактивировано"
            bot.reply_to(message, f"Сообщение успешно {status}!")
        else:
            bot.reply_to(message, "Ошибка изменения статуса сообщения!")
    
    user_states.pop(user_id, None)
    user_data.pop(user_id, None)
    show_main_menu(message.chat.id)

@bot.message_handler(func=lambda message: message.text == 'Показать все сообщения')
def show_all_banners(message):
    user_id = message.from_user.id
    banners = db.get_user_banners(user_id)
    
    if not banners:
        bot.reply_to(message, "У вас нет созданных сообщений.")
        return
    
    response = "Ваши сообщения:\n\n"
    for banner in banners:
        status = "Активно" if banner['is_active'] else "Неактивно"
        receivers = db.get_banner_receivers(banner['id'])
        response += f"ID: {banner['id']}\n"
        response += f"Текст: {banner['message'][:50]}{'...' if len(banner['message']) > 50 else ''}\n"
        response += f"Дата создания: {banner['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
        response += f"Дата отправки: {banner['send_at'].strftime('%d.%m.%Y %H:%M')}\n"
        response += f"Статус: {status}\n"
        response += f"Получатели: {len(receivers)}\n"
        response += "-" * 30 + "\n"
    
    bot.reply_to(message, response)

@bot.message_handler(func=lambda message: message.text == 'Редактировать сообщение')
def edit_banner_start(message):
    user_id = message.from_user.id
    banners = db.get_user_banners(user_id)
    
    if not banners:
        bot.reply_to(message, "У вас нет созданных сообщений для редактирования.")
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for banner in banners:
        text = banner['message'][:30] + "..." if len(banner['message']) > 30 else banner['message']
        markup.row(f"{banner['id']} - {text}")
    markup.row('Отмена')
    
    msg = bot.reply_to(message, "Выберите сообщение для редактирования:", reply_markup=markup)
    user_states[user_id] = STATES['EDITING_SELECT_BANNER']
    user_data[user_id] = {'action': 'edit'}
    bot.register_next_step_handler(msg, select_banner_for_editing)

def select_banner_for_editing(message):
    user_id = message.from_user.id
    
    if message.text == 'Отмена':
        show_main_menu(message.chat.id)
        user_states.pop(user_id, None)
        user_data.pop(user_id, None)
        return
    
    try:
        banner_id = int(message.text.split(' - ')[0])
        banner = db.get_banner_by_id(banner_id)
        
        if not banner or banner['author'] != user_id:
            bot.reply_to(message, "Неверный выбор!")
            show_main_menu(message.chat.id)
            return
            
        user_data[user_id]['banner_id'] = banner_id
        show_edit_menu(message.chat.id, user_id, banner_id)
    except:
        bot.reply_to(message, "Неверный выбор!")
        show_main_menu(message.chat.id)

def show_edit_menu(chat_id, user_id, banner_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Изменить текст', 'Изменить дату отправки')
    markup.row('Изменить получателей', 'Назад')
    
    banner = db.get_banner_by_id(banner_id)
    receivers = db.get_banner_receivers(banner_id)
    
    info = f"Сообщение ID: {banner_id}\n"
    info += f"Текст: {banner['message']}\n"
    info += f"Дата отправки: {banner['send_at'].strftime('%d.%m.%Y %H:%M')}\n"
    info += f"Получатели: {', '.join(map(str, receivers))}\n\n"
    info += "Выберите что хотите изменить:"
    
    msg = bot.send_message(chat_id, info, reply_markup=markup)
    bot.register_next_step_handler(msg, process_edit_choice)

def process_edit_choice(message):
    user_id = message.from_user.id
    
    if message.text == 'Назад':
        show_main_menu(message.chat.id)
        user_states.pop(user_id, None)
        user_data.pop(user_id, None)
        return
    
    banner_id = user_data[user_id]['banner_id']
    
    if message.text == 'Изменить текст':
        msg = bot.reply_to(message, "Введите новый текст сообщения:")
        user_states[user_id] = STATES['EDITING_MESSAGE_INPUT']
        bot.register_next_step_handler(msg, process_edit_message_input)
    
    elif message.text == 'Изменить дату отправки':
        msg = bot.reply_to(message, "Введите новую дату и время отправки в формате ДД.ММ.ГГГГ ЧЧ:ММ:")
        user_states[user_id] = STATES['EDITING_DATE_INPUT']
        bot.register_next_step_handler(msg, process_edit_date_input)
    
    elif message.text == 'Изменить получателей':
        show_receivers_menu_edit(message.chat.id, user_id, banner_id)
    else:
        banner_id = user_data[user_id]['banner_id']
        show_edit_menu(message.chat.id, user_id, banner_id)

def show_receivers_menu_edit(chat_id, user_id, banner_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Выбрать из контактов', 'Добавить вручную')
    markup.row('Назад')
    msg = bot.send_message(chat_id, "Выберите способ изменения получателей:", reply_markup=markup)
    user_states[user_id] = 'CHOOSING_RECEIVERS_METHOD'
    user_data[user_id]['editing_banner_id'] = banner_id
    bot.register_next_step_handler(msg, process_receivers_method_edit)

def process_receivers_method_edit(message):
    user_id = message.from_user.id
    banner_id = user_data[user_id].get('editing_banner_id')
    
    if message.text == 'Выбрать из контактов':
        show_contacts_menu_edit(message.chat.id, user_id, banner_id)
    elif message.text == 'Добавить вручную':
        msg = bot.reply_to(message, "Введите ID получателей через запятую (например, 123456789, 987654321):")
        user_states[user_id] = 'EDITING_RECEIVERS_INPUT'
        bot.register_next_step_handler(msg, process_edit_receivers_manual)
    elif message.text == 'Назад':
        show_edit_menu(message.chat.id, user_id, banner_id)
    else:
        show_receivers_menu_edit(message.chat.id, user_id, banner_id)

def show_contacts_menu_edit(chat_id, user_id, banner_id):
    try:
        # Отправляем запрос на получение контактов
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        contact_button = types.KeyboardButton('Поделиться контактом', request_contact=True)
        markup.add(contact_button)
        markup.row('Завершить выбор')
        markup.row('Назад')
        
        msg = bot.send_message(
            chat_id, 
            "Поделитесь контактами или нажмите 'Завершить выбор' когда добавите всех получателей.\n"
            "Нажмите 'Назад' для возврата к предыдущему меню.",
            reply_markup=markup
        )
        
        user_states[user_id] = 'SELECTING_CONTACTS'
        user_data[user_id]['editing_banner_id'] = banner_id
        if 'selected_contacts' not in user_data[user_id]:
            user_data[user_id]['selected_contacts'] = []
        
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {str(e)}")
        show_receivers_menu_edit(chat_id, user_id, banner_id)

@bot.message_handler(func=lambda message: message.text == 'Завершить выбор' and user_states.get(message.from_user.id) == 'SELECTING_CONTACTS')
def finish_contact_selection_edit(message):
    user_id = message.from_user.id
    banner_id = user_data[user_id].get('editing_banner_id')
    
    if user_states.get(user_id) == 'SELECTING_CONTACTS':
        selected_contacts = user_data[user_id].get('selected_contacts', [])
        
        if not selected_contacts:
            bot.reply_to(message, "Вы не выбрали ни одного контакта!")
            show_contacts_menu_edit(message.chat.id, user_id, banner_id)
            return
        
        # Сохраняем выбранные контакты как новых получателей
        user_data[user_id]['new_receivers'] = selected_contacts
        user_data[user_id]['banner_id'] = banner_id
        
        # Запрашиваем пароль для подтверждения
        msg = bot.reply_to(message, "Введите ваш пароль для подтверждения изменения получателей:")
        user_states[user_id] = STATES['WAITING_PASSWORD']
        user_data[user_id]['next_action'] = 'edit_receivers'
        bot.register_next_step_handler(msg, process_action_password)
    else:
        show_main_menu(message.chat.id)

def process_edit_receivers_manual(message):
    user_id = message.from_user.id
    banner_id = user_data[user_id].get('editing_banner_id')
    try:
        new_receivers = [int(x.strip()) for x in message.text.split(',')]
        user_data[user_id]['new_receivers'] = new_receivers
        user_data[user_id]['banner_id'] = banner_id
        
        # Запрашиваем пароль для подтверждения
        msg = bot.reply_to(message, "Введите ваш пароль для подтверждения изменения получателей:")
        user_states[user_id] = STATES['WAITING_PASSWORD']
        user_data[user_id]['next_action'] = 'edit_receivers'
        bot.register_next_step_handler(msg, process_action_password)
    except ValueError:
        msg = bot.reply_to(message, "Неверный формат ID. Введите через запятую:")
        bot.register_next_step_handler(msg, process_edit_receivers_manual)

def process_edit_message_input(message):
    user_id = message.from_user.id
    user_data[user_id]['new_message'] = message.text
    msg = bot.reply_to(message, "Введите ваш пароль для подтверждения изменения:")
    user_states[user_id] = STATES['WAITING_PASSWORD']
    user_data[user_id]['next_action'] = 'edit_message'
    bot.register_next_step_handler(msg, process_action_password)

def process_edit_date_input(message):
    user_id = message.from_user.id
    try:
        date_str = message.text
        new_date = datetime.strptime(date_str, "%d.%m.%Y %H:%M")
        
        if new_date <= datetime.now():
            msg = bot.reply_to(message, "Дата должна быть в будущем. Попробуйте еще раз:")
            bot.register_next_step_handler(msg, process_edit_date_input)
            return
            
        user_data[user_id]['new_date'] = new_date
        msg = bot.reply_to(message, "Введите ваш пароль для подтверждения изменения:")
        user_states[user_id] = STATES['WAITING_PASSWORD']
        user_data[user_id]['next_action'] = 'edit_date'
        bot.register_next_step_handler(msg, process_action_password)
    except ValueError:
        msg = bot.reply_to(message, "Неверный формат даты. Введите в формате ДД.ММ.ГГГГ ЧЧ:ММ:")
        bot.register_next_step_handler(msg, process_edit_date_input)

@bot.message_handler(func=lambda message: message.text == 'Активировать/Деактивировать')
def toggle_banner_start(message):
    user_id = message.from_user.id
    banners = db.get_user_banners(user_id)
    
    if not banners:
        bot.reply_to(message, "У вас нет созданных сообщений.")
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for banner in banners:
        status = "Активировать" if not banner['is_active'] else "Деактивировать"
        text = banner['message'][:30] + "..." if len(banner['message']) > 30 else banner['message']
        markup.row(f"{banner['id']} - {text} ({status})")
    markup.row('Отмена')
    
    msg = bot.reply_to(message, "Выберите сообщение для изменения статуса:", reply_markup=markup)
    user_states[user_id] = STATES['TOGGLE_BANNER_SELECT']
    user_data[user_id] = {}
    bot.register_next_step_handler(msg, process_toggle_banner)

def process_toggle_banner(message):
    user_id = message.from_user.id
    
    if message.text == 'Отмена':
        show_main_menu(message.chat.id)
        user_states.pop(user_id, None)
        user_data.pop(user_id, None)
        return
    
    try:
        # Извлекаем ID из текста вида "123 - текст (Активировать)"
        banner_id = int(message.text.split(' - ')[0])
        banner = db.get_banner_by_id(banner_id)
        
        if not banner or banner['author'] != user_id:
            bot.reply_to(message, "Неверный выбор!")
            show_main_menu(message.chat.id)
            return
            
        # Определяем новый статус
        new_status = not banner['is_active']
        
        user_data[user_id]['banner_id'] = banner_id
        user_data[user_id]['is_active'] = new_status
        msg = bot.reply_to(message, "Введите ваш пароль для подтверждения изменения:")
        user_states[user_id] = STATES['WAITING_PASSWORD']
        user_data[user_id]['next_action'] = 'toggle_banner'
        bot.register_next_step_handler(msg, process_action_password)
    except:
        bot.reply_to(message, "Неверный выбор!")
        show_main_menu(message.chat.id)

@bot.message_handler(func=lambda message: message.text == 'Изменить пароль')
def change_password_start(message):
    user_id = message.from_user.id
    msg = bot.reply_to(message, "Введите текущий пароль:")
    user_states[user_id] = STATES['CHANGING_PASSWORD_OLD']
    user_data[user_id] = {}
    bot.register_next_step_handler(msg, process_old_password)

def process_old_password(message):
    user_id = message.from_user.id
    password = message.text
    delete_message_after_delay(message.chat.id, message.message_id)
    
    if not db.check_password(user_id, password):
        bot.reply_to(message, "Неверный текущий пароль!")
        show_main_menu(message.chat.id)
        return
    
    msg = bot.reply_to(message, "Введите новый пароль:")
    user_states[user_id] = STATES['CHANGING_PASSWORD_NEW']
    bot.register_next_step_handler(msg, process_new_password)

def process_new_password(message):
    user_id = message.from_user.id
    new_password = message.text
    
    if len(new_password) < 4:
        msg = bot.reply_to(message, "Пароль должен быть не менее 4 символов. Введите новый пароль:")
        bot.register_next_step_handler(msg, process_new_password)
        return
    
    user_data[user_id] = {'new_password': new_password}
    msg = bot.reply_to(message, "Подтвердите новый пароль:")
    bot.register_next_step_handler(msg, confirm_new_password)

def confirm_new_password(message):
    user_id = message.from_user.id
    confirm_password = message.text
    
    if user_data[user_id]['new_password'] != confirm_password:
        bot.reply_to(message, "Пароли не совпадают!")
        show_main_menu(message.chat.id)
        return
    
    msg = bot.reply_to(message, "Введите ваш пароль для подтверждения изменения:")
    user_states[user_id] = STATES['WAITING_PASSWORD']
    user_data[user_id]['next_action'] = 'change_password'
    bot.register_next_step_handler(msg, process_action_password)

@bot.message_handler(func=lambda message: message.text == 'Удалить сообщение')
def delete_banner_start(message):
    user_id = message.from_user.id
    banners = db.get_user_banners(user_id)
    
    if not banners:
        bot.reply_to(message, "У вас нет созданных сообщений для удаления.")
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for banner in banners:
        text = banner['message'][:30] + "..." if len(banner['message']) > 30 else banner['message']
        markup.row(f"{banner['id']} - {text}")
    markup.row('Отмена')
    
    msg = bot.reply_to(message, "Выберите сообщение для удаления:", reply_markup=markup)
    user_states[user_id] = STATES['SELECTING_BANNER']
    user_data[user_id] = {}
    bot.register_next_step_handler(msg, select_banner_for_action)

def select_banner_for_action(message):
    user_id = message.from_user.id
    
    if message.text == 'Отмена':
        show_main_menu(message.chat.id)
        user_states.pop(user_id, None)
        user_data.pop(user_id, None)
        return
    
    try:
        banner_id = int(message.text.split(' - ')[0])
        banner = db.get_banner_by_id(banner_id)
        
        if not banner or banner['author'] != user_id:
            bot.reply_to(message, "Неверный выбор!")
            show_main_menu(message.chat.id)
            return
            
        user_data[user_id]['banner_id'] = banner_id
        msg = bot.reply_to(message, "Введите ваш пароль для подтверждения удаления:")
        user_states[user_id] = STATES['WAITING_PASSWORD']
        user_data[user_id]['next_action'] = 'delete_banner'
        bot.register_next_step_handler(msg, process_action_password)
    except:
        bot.reply_to(message, "Неверный выбор!")
        show_main_menu(message.chat.id)

@bot.message_handler(func=lambda message: message.text == 'Мой ID')
def show_my_id(message):
    user_id = message.from_user.id
    bot.reply_to(message, f"Ваш ID пользователя: {user_id}")

# Функция для отправки сообщений по расписанию
def send_scheduled_messages():
    import threading
    import time
    
    def check_and_send():
        while True:
            try:
                banners_to_send = db.get_banners_to_send()
                for banner in banners_to_send:
                    # Получаем получателей
                    receivers = db.get_banner_receivers_with_data(banner['id'])
                    
                    # Отправляем сообщение каждому получателю
                    for receiver in receivers:
                        try:
                            bot.send_message(
                                receiver['receiver'], 
                                f"Сообщение от {banner['author_name'] or banner['author_username'] or banner['author']}:\n\n{banner['message']}"
                            )
                        except Exception as e:
                            print(f"Ошибка отправки сообщения получателю {receiver['receiver']}: {e}")
                    
                    # Уведомляем отправителя
                    try:
                        bot.send_message(
                            banner['author'],
                            f"Ваше сообщение (ID: {banner['id']}) было отправлено {len(receivers)} получателям:\n\n{banner['message']}"
                        )
                    except Exception as e:
                        print(f"Ошибка уведомления отправителя {banner['author']}: {e}")
                    
                    # Отключаем баннер
                    db.toggle_banner_active(banner['id'], False)
                
                time.sleep(60)  # Проверяем каждую минуту
            except Exception as e:
                print(f"Ошибка при отправке запланированных сообщений: {e}")
                time.sleep(60)
    
    # Запускаем в отдельном потоке
    sender_thread = threading.Thread(target=check_and_send, daemon=True)
    sender_thread.start()

# Запуск проверки сообщений
send_scheduled_messages()

# Обработка всех остальных сообщений
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    
    # Если пользователь не зарегистрирован
    if not db.user_exists(user_id):
        start_command(message)
        return
    
    # Если ожидаем пароль
    if user_states.get(user_id) == STATES['WAITING_PASSWORD']:
        process_action_password(message)
        return
    
    # Если ожидаем выбор баннера
    if user_states.get(user_id) in [STATES['SELECTING_BANNER'], STATES['EDITING_SELECT_BANNER'], STATES['TOGGLE_BANNER_SELECT']]:
        if user_states.get(user_id) == STATES['EDITING_SELECT_BANNER']:
            select_banner_for_editing(message)
        elif user_states.get(user_id) == STATES['TOGGLE_BANNER_SELECT']:
            process_toggle_banner(message)
        else:
            select_banner_for_action(message)
        return
    
    show_main_menu(message.chat.id)

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)