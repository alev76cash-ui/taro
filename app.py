from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, Response
from flask_mail import Mail, Message
import random
import logging
import sqlite3
import datetime
import hashlib
import secrets
import os
import requests
import threading
import csv
from io import StringIO
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this-in-production'

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

# ============================================
# НАСТРОЙКИ ДЛЯ MAIL.RU
# ============================================
app.config['MAIL_SERVER'] = 'smtp.mail.ru'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'eremeev_an@list.ru'
app.config['MAIL_PASSWORD'] = 'l5noLnY9I5Lk58CQNv48'
app.config['MAIL_DEFAULT_SENDER'] = 'eremeev_an@list.ru'
app.config['MAIL_ASCII_ATTACHMENTS'] = False
app.config['MAIL_CONNECTION_TIMEOUT'] = 5
app.config['MAIL_MAX_EMAILS'] = 10

mail = Mail(app)

# ============================================
# НАСТРОЙКИ TELEGRAM
# ============================================
TELEGRAM_TOKEN = '8707413550:AAF_1dRdk9TLapliloGUW0L0DhPAJoF9dH8'
TELEGRAM_CHAT_ID = '1409979028'

# ============================================
# РАБОТА С БАЗОЙ ДАННЫХ
# ============================================
def init_db():
    """Создает базу данных при первом запуске"""
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    
    # Таблица пользователей
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT UNIQUE,
                  username TEXT,
                  password TEXT,
                  name TEXT,
                  date TEXT,
                  test_result TEXT,
                  avatar TEXT DEFAULT '👤',
                  last_login TEXT,
                  is_blocked INTEGER DEFAULT 0)''')
    
    # Таблица для карт дня (история)
    c.execute('''CREATE TABLE IF NOT EXISTS card_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_email TEXT,
                  card_name TEXT,
                  card_meaning TEXT,
                  date TEXT)''')
    
    # Таблица для заявок
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  email TEXT,
                  phone TEXT,
                  message TEXT,
                  status TEXT DEFAULT 'new',
                  admin_comment TEXT,
                  date TEXT)''')
    
    # Таблица для архивных заявок
    c.execute('''CREATE TABLE IF NOT EXISTS orders_archive
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  original_id INTEGER,
                  name TEXT,
                  email TEXT,
                  phone TEXT,
                  message TEXT,
                  status TEXT,
                  admin_comment TEXT,
                  date TEXT,
                  archived_date TEXT)''')
    
    # Таблица для избранных карт
    c.execute('''CREATE TABLE IF NOT EXISTS favorite_cards
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_email TEXT,
                  card_name TEXT,
                  date TEXT)''')
    
    # Таблица для чата
    c.execute('''CREATE TABLE IF NOT EXISTS chat_messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  order_id INTEGER,
                  sender TEXT,
                  message TEXT,
                  is_read INTEGER DEFAULT 0,
                  date TEXT)''')
    
    conn.commit()
    conn.close()
    print("✅ База данных пользователей инициализирована")
    
    # Создаем базу данных Таро (если её нет)
    from tarot_db import create_tarot_database
    create_tarot_database()

def migrate_db():
    """Обновляет структуру базы данных"""
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        
        # Проверяем пользователей
        c.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in c.fetchall()]
        
        if 'is_blocked' not in columns:
            print("🔄 Добавляем колонку is_blocked в таблицу users...")
            c.execute("ALTER TABLE users ADD COLUMN is_blocked INTEGER DEFAULT 0")
        
        # Проверяем таблицу chat_messages
        c.execute("PRAGMA table_info(chat_messages)")
        columns = [col[1] for col in c.fetchall()]
        
        if 'order_id' not in columns:
            print("🔄 Создаем таблицу chat_messages...")
            c.execute('''CREATE TABLE IF NOT EXISTS chat_messages
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          order_id INTEGER,
                          sender TEXT,
                          message TEXT,
                          is_read INTEGER DEFAULT 0,
                          date TEXT)''')
        
        conn.commit()
        print("✅ База данных обновлена")
    except Exception as e:
        print(f"❌ Ошибка при обновлении БД: {e}")
    finally:
        conn.close()

# Инициализируем БД
init_db()
migrate_db()

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ
# ============================================
def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def create_user(email, username, password, name=''):
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        
        c.execute("SELECT id FROM users WHERE email = ?", (email,))
        if c.fetchone():
            conn.close()
            return False, "Пользователь с таким email уже существует"
        
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        if c.fetchone():
            conn.close()
            return False, "Имя пользователя уже занято"
        
        hashed = hash_password(password)
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        c.execute("""
            INSERT INTO users (email, username, password, name, date, avatar, test_result, last_login, is_blocked) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (email, username, hashed, name, current_time, '👤', None, None, 0))
        
        conn.commit()
        conn.close()
        return True, "Пользователь успешно создан"
    except Exception as e:
        print(f"❌ Ошибка создания пользователя: {e}")
        return False, f"Ошибка сервера"

def authenticate_user(login, password):
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        hashed = hash_password(password)
        
        c.execute("""
            SELECT id, email, username, name, avatar, test_result, password, is_blocked
            FROM users
            WHERE email = ? OR username = ?
        """, (login, login))
        
        user = c.fetchone()
        
        if user and user[6] == hashed and user[7] == 0:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            c.execute("UPDATE users SET last_login = ? WHERE id = ?", (current_time, user[0]))
            conn.commit()
            conn.close()
            return True, {
                'id': user[0],
                'email': user[1],
                'username': user[2],
                'name': user[3] if user[3] else '',
                'avatar': user[4] if user[4] else '👤',
                'test_result': user[5] if user[5] else ''
            }
        
        conn.close()
        return False, "Неверный логин или пароль" if user else "Пользователь не найден"
    except Exception as e:
        print(f"❌ Ошибка аутентификации: {e}")
        return False, f"Ошибка сервера"

def get_user_by_email(email):
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()
        return user
    except Exception as e:
        return None

def get_all_users():
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute("SELECT id, email, username, name, date, last_login, is_blocked, test_result FROM users ORDER BY date DESC")
        users = c.fetchall()
        conn.close()
        return users
    except Exception as e:
        return []

def toggle_block_user(user_id):
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute("UPDATE users SET is_blocked = NOT is_blocked WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def reset_user_password(user_id, new_password):
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        hashed = hash_password(new_password)
        c.execute("UPDATE users SET password = ? WHERE id = ?", (hashed, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def get_user_history_all(user_id):
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute("""
            SELECT card_name, card_meaning, date 
            FROM card_history 
            WHERE user_email IN (SELECT email FROM users WHERE id = ?)
            ORDER BY date DESC
        """, (user_id,))
        history = c.fetchall()
        conn.close()
        return history
    except Exception as e:
        return []

def get_user_history(email):
    """Получает историю карт пользователя по email"""
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute("""
            SELECT card_name, card_meaning, date
            FROM card_history
            WHERE user_email = ?
            ORDER BY date DESC
            LIMIT 10
        """, (email,))
        history = c.fetchall()
        conn.close()
        return history
    except Exception as e:
        print(f"❌ Ошибка получения истории: {e}")
        return []

def get_favorite_cards(email):
    """Получает избранные карты пользователя"""
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute("""
            SELECT card_name, date
            FROM favorite_cards
            WHERE user_email = ?
            ORDER BY date DESC
        """, (email,))
        favorites = c.fetchall()
        conn.close()
        return favorites
    except Exception as e:
        print(f"❌ Ошибка получения избранного: {e}")
        return []

def get_user_orders(email):
    """Получает заявки пользователя"""
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute("SELECT id, name, date, status FROM orders WHERE email = ? ORDER BY date DESC", (email,))
        orders = c.fetchall()
        conn.close()
        return orders
    except Exception as e:
        print(f"❌ Ошибка получения заявок: {e}")
        return []

def save_card_history(email, card_name, card_meaning):
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute("""
            INSERT INTO card_history (user_email, card_name, card_meaning, date)
            VALUES (?, ?, ?, ?)
        """, (email, card_name, card_meaning, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Ошибка сохранения истории: {e}")

def add_favorite_card(email, card_name):
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute("""
            INSERT INTO favorite_cards (user_email, card_name, date)
            VALUES (?, ?, ?)
        """, (email, card_name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def get_chat_messages(order_id):
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute("""
            SELECT id, sender, message, date, is_read 
            FROM chat_messages 
            WHERE order_id = ? 
            ORDER BY date ASC
        """, (order_id,))
        messages = c.fetchall()
        c.execute("UPDATE chat_messages SET is_read = 1 WHERE order_id = ? AND sender = 'user'", (order_id,))
        conn.commit()
        conn.close()
        return messages
    except Exception as e:
        return []

def add_chat_message(order_id, sender, message):
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        c.execute("""
            INSERT INTO chat_messages (order_id, sender, message, date, is_read) 
            VALUES (?, ?, ?, ?, ?)
        """, (order_id, sender, message, current_time, 1 if sender == 'admin' else 0))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def get_unread_messages_count():
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM chat_messages WHERE is_read = 0 AND sender = 'user'")
        count = c.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        return 0

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != 'admin' or auth.password != 'taro2026':
            return ('Необходима авторизация', 401, {
                'WWW-Authenticate': 'Basic realm="Login Required"'
            })
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# ОТЗЫВЫ УЧЕНИКОВ
# ============================================
reviews = [
    {
        "name": "Елена",
        "age": 34,
        "city": "Москва",
        "photo": "👩",
        "text": "Долго искала школу Таро, где объясняют доступно. После первого же урока смогла сделать расклад для подруги! Очень благодарна за поддержку.",
        "rating": 5,
        "date": "февраль 2026"
    },
    {
        "name": "Анна",
        "age": 28,
        "city": "Санкт-Петербург",
        "photo": "👱‍♀️",
        "text": "Начала с нуля, сейчас уже читаю карты для себя и близких. Тест показал, что я Императрица — и правда, всегда хотела свой цветочный магазин!",
        "rating": 5,
        "date": "январь 2026"
    },
    {
        "name": "Дмитрий",
        "age": 42,
        "city": "Новосибирск",
        "photo": "👨",
        "text": "Думал, Таро только для женщин. Оказалось, отличный инструмент для анализа бизнес-ситуаций! Рекомендую курс всем, кто хочет развить интуицию.",
        "rating": 5,
        "date": "декабрь 2025"
    },
    {
        "name": "Ольга",
        "age": 25,
        "city": "Краснодар",
        "photo": "🧝‍♀️",
        "text": "Прошла тест, узнала, что я Шут, и решила записаться на курс. Теперь путешествую и делаю расклады в разных городах. Это изменило мою жизнь!",
        "rating": 5,
        "date": "январь 2026"
    }
]

# ============================================
# ВОПРОСЫ ДЛЯ ТЕСТА
# ============================================
test_questions = [
    {
        "question": "Что ты чувствуешь, когда просыпаешься утром?",
        "options": [
            {"text": "Жажду приключений и новых открытий", "card": "Шут"},
            {"text": "Готовность действовать и менять мир", "card": "Маг"},
            {"text": "Желание прислушаться к своим ощущениям", "card": "Верховная Жрица"},
            {"text": "Благодарность за новый день", "card": "Императрица"}
        ]
    },
    {
        "question": "Как ты принимаешь важные решения?",
        "options": [
            {"text": "Иду за интуицией, чувствую сердцем", "card": "Верховная Жрица"},
            {"text": "Анализирую все 'за' и 'против'", "card": "Император"},
            {"text": "Слушаю совет близких", "card": "Влюбленные"},
            {"text": "Действую быстро и решительно", "card": "Маг"}
        ]
    },
    {
        "question": "Что для тебя самое важное в жизни?",
        "options": [
            {"text": "Любовь и гармония", "card": "Влюбленные"},
            {"text": "Самореализация и успех", "card": "Маг"},
            {"text": "Стабильность и порядок", "card": "Император"},
            {"text": "Развитие и перемены", "card": "Колесо Фортуны"}
        ]
    },
    {
        "question": "Как ты проводишь выходной?",
        "options": [
            {"text": "Отправляюсь в спонтанное путешествие", "card": "Шут"},
            {"text": "Занимаюсь творчеством", "card": "Императрица"},
            {"text": "Медитирую или читаю", "card": "Верховная Жрица"},
            {"text": "Планирую следующую неделю", "card": "Император"}
        ]
    }
]

# ============================================
# ФУНКЦИИ ДЛЯ УВЕДОМЛЕНИЙ
# ============================================
def send_telegram_notification(name, email, phone, message):
    """Отправляет уведомление в Telegram"""
    try:
        import socket
        socket.setdefaulttimeout(5)
        
        text = f"""🔮 НОВАЯ ЗАЯВКА С САЙТА

👤 Имя: {name}
📧 Email: {email}
📞 Телефон: {phone if phone else 'не указан'}

💬 Сообщение:
{message}

⏰ {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}"""

        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            print("✅ Уведомление в Telegram отправлено")
        else:
            print(f"❌ Ошибка Telegram: {response.text}")
    except requests.exceptions.Timeout:
        print("❌ Таймаут Telegram - сервер не отвечает")
    except Exception as e:
        print(f"❌ Ошибка отправки в Telegram: {e}")

# ============================================
# АСИНХРОННАЯ ОТПРАВКА ПИСЕМ
# ============================================
def send_email_async(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            print("✅ Письмо отправлено асинхронно")
        except Exception as e:
            print(f"❌ Ошибка отправки письма: {e}")

def send_emails_background(app, name, email, phone, message, is_auth):
    msg_admin = Message(
        subject='Новая заявка с сайта Школы Таро',
        recipients=['eremeev_an@list.ru'],
        reply_to=email,
        charset='utf-8'
    )
    msg_admin.body = f"""
✨ ПОЛУЧЕНА НОВАЯ ЗАЯВКА ✨

👤 Имя: {name}
📧 Email: {email}
📞 Телефон: {phone if phone else 'не указан'}

💬 Сообщение:
{message}

---
Отправлено: {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}
{'🔐 Авторизованный пользователь' if is_auth else '👤 Гость'}
"""
    msg_admin.charset = 'utf-8'
    
    msg_client = Message(
        subject='Спасибо за заявку в Школу Таро!',
        recipients=[email],
        charset='utf-8'
    )
    msg_client.body = f"""
Здравствуйте, {name}!

🌟 Спасибо за интерес к Школе Таро!

Я получил вашу заявку и свяжусь с вами в ближайшее время (обычно в течение 24 часов).

С уважением,
Анна
"""
    msg_client.charset = 'utf-8'
    
    threading.Thread(target=send_email_async, args=(app, msg_admin)).start()
    threading.Thread(target=send_email_async, args=(app, msg_client)).start()
    threading.Thread(target=send_telegram_notification, args=(name, email, phone, message)).start()

# ============================================
# МАРШРУТЫ
# ============================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cards')
def cards():
    from tarot_db import get_all_cards
    cards_list = get_all_cards()
    return render_template('cards.html', cards=cards_list)

@app.route('/get_all_cards')
def get_all_cards_api():
    conn = None
    try:
        conn = sqlite3.connect('tarot.db')
        c = conn.cursor()
        c.execute("""
            SELECT name, arcana, COALESCE(suit, '') as suit, image, image_path, meaning, card_number, keywords, element
            FROM tarot_cards
            ORDER BY arcana, suit, card_number
        """)
        cards = c.fetchall()
        result = []
        for card in cards:
            result.append({
                'name': card[0],
                'arcana': card[1],
                'suit': card[2] if card[2] else '',
                'image_emoji': card[3],
                'image_path': card[4],
                'meaning': card[5],
                'card_number': card[6],
                'keywords': card[7] if card[7] else '',
                'element': card[8] if card[8] else ''
            })
        return jsonify(result)
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/get_card_by_name/<name>')
def get_card_by_name(name):
    conn = None
    try:
        conn = sqlite3.connect('tarot.db')
        c = conn.cursor()
        c.execute("SELECT * FROM tarot_cards WHERE name = ?", (name,))
        card_data = c.fetchone()
        if card_data:
            card = {
                'id': card_data[0],
                'card_number': card_data[1],
                'name': card_data[2],
                'arcana': card_data[3],
                'suit': card_data[4] if card_data[4] else '',
                'image': card_data[5],
                'image_path': card_data[6],
                'element': card_data[7],
                'keywords': card_data[8],
                'description': card_data[9],
                'meaning': card_data[10],
                'advice': card_data[11],
                'reverse': card_data[12],
                'question': card_data[13]
            }
            return jsonify(card)
        return jsonify({'error': 'Card not found'}), 404
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/get_card_of_day')
def get_card_of_day():
    from tarot_db import get_random_card
    card = get_random_card()
    if not card:
        card = {'name': 'Шут', 'image': '🤹', 'image_path': '/static/images/cards/fool.jpg', 'meaning': 'Новые начинания, спонтанность, вера в лучшее', 'advice': 'Позволь себе рискнуть и довериться потоку жизни'}
    else:
        card = {'name': card['name'], 'image': card['image'], 'image_path': card['image_path'], 'meaning': card['meaning'], 'advice': card['advice'], 'keywords': card['keywords'], 'element': card['element'], 'arcana': card['arcana'], 'suit': card['suit']}
    if 'user_id' in session:
        save_card_history(session['user_email'], card['name'], card['meaning'])
    return jsonify(card)

@app.route('/get_test_result', methods=['POST'])
def get_test_result():
    data = request.json
    answers = data.get('answers', [])
    card_counts = {}
    for answer in answers:
        card = answer.get('card')
        card_counts[card] = card_counts.get(card, 0) + 1
    if card_counts:
        result_card_name = max(card_counts, key=card_counts.get)
        from tarot_db import get_card_by_name as get_card
        card_info = get_card(result_card_name)
    else:
        from tarot_db import get_random_card
        card_info = get_random_card()
    if not card_info:
        card_info = {'name': 'Шут', 'image': '🤹', 'image_path': '/static/images/cards/fool.jpg', 'meaning': 'Новые начинания, спонтанность, вера в лучшее', 'advice': 'Позволь себе рискнуть и довериться потоку жизни', 'description': 'Шут — это чистый лист, начало пути.', 'element': 'воздух', 'keywords': 'начало, спонтанность, вера, риск', 'question': 'Что нового ты готов(а) начать?'}
    else:
        card_info = {'name': card_info['name'], 'image': card_info['image'], 'image_path': card_info['image_path'], 'meaning': card_info['meaning'], 'advice': card_info['advice'], 'description': card_info['description'], 'element': card_info['element'], 'keywords': card_info['keywords'], 'question': card_info['question']}
    if 'user_id' in session:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute("UPDATE users SET test_result = ? WHERE email = ?", (card_info['name'], session['user_email']))
        conn.commit()
        conn.close()
    return jsonify(card_info)

@app.route('/get_reviews')
def get_reviews():
    return jsonify(reviews)

@app.route('/order', methods=['POST'])
def order():
    data = request.json
    name = data.get('name', '')
    email = data.get('email', '')
    phone = data.get('phone', '')
    message = data.get('message', '')
    
    if 'user_id' in session and not email:
        email = session.get('user_email', '')
        name = session.get('user_name') or session.get('user_username', '')
    
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        c.execute("INSERT INTO orders (name, email, phone, message, status, date) VALUES (?, ?, ?, ?, ?, ?)", (name, email, phone, message, 'new', current_time))
        order_id = c.lastrowid
        conn.commit()
        conn.close()
        
        add_chat_message(order_id, 'user', message)
    except Exception as e:
        print(f"❌ Ошибка сохранения в базу: {e}")
    
    send_emails_background(app, name, email, phone, message, 'user_id' in session)
    
    return jsonify({'success': True, 'message': 'Заявка отправлена! Я свяжусь с вами в ближайшее время.'})

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    name = data.get('name', '')
    if not email or not username or not password:
        return jsonify({'success': False, 'message': 'Заполните все поля'})
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Пароль должен быть не менее 6 символов'})
    success, message = create_user(email, username, password, name)
    return jsonify({'success': success, 'message': message})

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Нет данных'})
        login = data.get('login', '').strip()
        password = data.get('password', '')
        if not login or not password:
            return jsonify({'success': False, 'message': 'Заполните все поля'})
        success, result = authenticate_user(login, password)
        if success:
            session['user_id'] = result['id']
            session['user_email'] = result['email']
            session['user_name'] = result['name']
            session['user_username'] = result['username']
            session['user_avatar'] = result['avatar']
            session['test_result'] = result['test_result']
            return jsonify({'success': True, 'message': 'Вход выполнен успешно', 'user': result})
        else:
            return jsonify({'success': False, 'message': result})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Ошибка сервера'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    email = session['user_email']
    history = get_user_history(email)
    favorites = get_favorite_cards(email)
    orders = get_user_orders(email)
    return render_template('profile.html',
                         email=email,
                         name=session.get('user_name', ''),
                         username=session.get('user_username', ''),
                         avatar=session.get('user_avatar', '👤'),
                         history=history,
                         favorites=favorites,
                         orders=orders,
                         test_result=session.get('test_result'))

@app.route('/api/update_profile', methods=['POST'])
@login_required
def update_profile():
    data = request.json
    name = data.get('name')
    avatar = data.get('avatar')
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        if name:
            c.execute("UPDATE users SET name = ? WHERE email = ?", (name, session['user_email']))
            session['user_name'] = name
        if avatar:
            c.execute("UPDATE users SET avatar = ? WHERE email = ?", (avatar, session['user_email']))
            session['user_avatar'] = avatar
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Профиль обновлен'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/change_password', methods=['POST'])
@login_required
def change_password():
    data = request.json
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    if not old_password or not new_password:
        return jsonify({'success': False, 'message': 'Заполните все поля'})
    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'Новый пароль должен быть не менее 6 символов'})
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        hashed_old = hash_password(old_password)
        c.execute("SELECT id FROM users WHERE email = ? AND password = ?", (session['user_email'], hashed_old))
        if not c.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Неверный текущий пароль'})
        hashed_new = hash_password(new_password)
        c.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_new, session['user_email']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Пароль успешно изменен'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/profile/clear_history', methods=['POST'])
@login_required
def clear_my_history():
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute("DELETE FROM card_history WHERE user_email = ?", (session['user_email'],))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'История очищена'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ============================================
# АДМИН-ПАНЕЛЬ
# ============================================
@app.route('/admin/new_orders_count')
@admin_required
def new_orders_count():
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM orders WHERE status = 'new'")
        count = c.fetchone()[0]
        conn.close()
        return jsonify({'count': count})
    except Exception as e:
        return jsonify({'count': 0})

@app.route('/admin/export/excel')
@admin_required
def export_orders_excel():
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        
        status_filter = request.args.get('status', 'all')
        search_query = request.args.get('search', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        query = "SELECT id, name, email, phone, message, status, date FROM orders"
        params = []
        
        conditions = []
        if status_filter != 'all':
            conditions.append("status = ?")
            params.append(status_filter)
        if search_query:
            conditions.append("(name LIKE ? OR email LIKE ? OR phone LIKE ? OR message LIKE ?)")
            params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
        if date_from:
            conditions.append("date >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("date <= ?")
            params.append(date_to + " 23:59:59")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY date DESC"
        
        c.execute(query, params)
        orders = c.fetchall()
        conn.close()
        
        output = StringIO()
        writer = csv.writer(output, delimiter=';')
        writer.writerow(['ID', 'Имя', 'Email', 'Телефон', 'Сообщение', 'Статус', 'Дата'])
        
        status_names = {'new': 'Новая', 'in-progress': 'В работе', 'done': 'Завершена'}
        for order in orders:
            writer.writerow([
                order[0], order[1], order[2], order[3] or '',
                order[4][:100] if order[4] else '',
                status_names.get(order[5], order[5]),
                order[6]
            ])
        
        response = Response(output.getvalue(), mimetype='text/csv; charset=utf-8-sig')
        response.headers['Content-Disposition'] = f'attachment; filename=orders_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/archive/<int:order_id>', methods=['POST'])
@admin_required
def archive_order(order_id):
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        order = c.fetchone()
        if order:
            c.execute("""
                INSERT INTO orders_archive 
                (original_id, name, email, phone, message, status, admin_comment, date, archived_date) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (order[0], order[1], order[2], order[3], order[4], order[5], order[6], order[7], 
                  datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
            c.execute("DELETE FROM orders WHERE id = ?", (order_id,))
            conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/restore/<int:archive_id>', methods=['POST'])
@admin_required
def restore_order(archive_id):
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute("SELECT * FROM orders_archive WHERE id = ?", (archive_id,))
        archive = c.fetchone()
        if archive:
            c.execute("""
                INSERT INTO orders (name, email, phone, message, status, admin_comment, date) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (archive[2], archive[3], archive[4], archive[5], archive[6], archive[7], archive[8]))
            c.execute("DELETE FROM orders_archive WHERE id = ?", (archive_id,))
            conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/delete/<int:order_id>', methods=['DELETE'])
@admin_required
def delete_order(order_id):
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/archive_list')
@admin_required
def archive_list():
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute("""
            SELECT id, original_id, name, email, phone, message, status, date, archived_date 
            FROM orders_archive 
            ORDER BY archived_date DESC
        """)
        archives = c.fetchall()
        conn.close()
        return render_template('admin_archive.html', archives=archives)
    except Exception as e:
        return render_template('admin_archive.html', archives=[])

@app.route('/admin')
@admin_required
def admin_panel():
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        
        status_filter = request.args.get('status', 'all')
        search_query = request.args.get('search', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        sort = request.args.get('sort', 'date_desc')
        
        query = "SELECT id, name, email, phone, message, status, date FROM orders"
        params = []
        
        conditions = []
        if status_filter != 'all':
            conditions.append("status = ?")
            params.append(status_filter)
        if search_query:
            conditions.append("(name LIKE ? OR email LIKE ? OR phone LIKE ? OR message LIKE ?)")
            params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
        if date_from:
            conditions.append("date >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("date <= ?")
            params.append(date_to + " 23:59:59")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        sort_options = {
            'date_desc': "ORDER BY date DESC",
            'date_asc': "ORDER BY date ASC",
            'name_asc': "ORDER BY name ASC",
            'name_desc': "ORDER BY name DESC"
        }
        query += " " + sort_options.get(sort, "ORDER BY date DESC")
        
        c.execute(query, params)
        orders = c.fetchall()
        
        c.execute("SELECT COUNT(*) FROM orders WHERE status = 'new'")
        new_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM orders")
        total_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM orders WHERE status = 'in-progress'")
        in_progress_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM orders WHERE status = 'done'")
        done_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM chat_messages WHERE is_read = 0 AND sender = 'user'")
        unread_count = c.fetchone()[0]
        
        conn.close()
        return render_template('admin.html', 
                             orders=orders,
                             new_count=new_count,
                             total_count=total_count,
                             in_progress_count=in_progress_count,
                             done_count=done_count,
                             unread_count=unread_count,
                             status_filter=status_filter,
                             search_query=search_query,
                             date_from=date_from,
                             date_to=date_to)
    except Exception as e:
        return render_template('admin.html', orders=[], error=str(e))

@app.route('/admin/order/<int:order_id>', methods=['GET', 'POST'])
@admin_required
def admin_order_detail(order_id):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = c.fetchone()
    
    c.execute("SELECT id, sender, message, date FROM chat_messages WHERE order_id = ? ORDER BY date ASC", (order_id,))
    messages = c.fetchall()
    
    c.execute("UPDATE chat_messages SET is_read = 1 WHERE order_id = ? AND sender = 'user'", (order_id,))
    conn.commit()
    conn.close()
    
    if not order:
        return "Заявка не найдена", 404
    
    if request.method == 'POST':
        status = request.form.get('status')
        comment = request.form.get('comment')
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute("UPDATE orders SET status = ?, admin_comment = ? WHERE id = ?", (status, comment, order_id))
        conn.commit()
        
        chat_message = request.form.get('chat_message', '').strip()
        if chat_message:
            add_chat_message(order_id, 'admin', chat_message)
        
        conn.close()
        return redirect(url_for('admin_order_detail', order_id=order_id))
    
    return render_template('admin_order.html', order=order, messages=messages)

@app.route('/admin/users')
@admin_required
def admin_users():
    users = get_all_users()
    return render_template('admin_users.html', users=users)

@app.route('/admin/block_user/<int:user_id>', methods=['POST'])
@admin_required
def block_user(user_id):
    success = toggle_block_user(user_id)
    return jsonify({'success': success})

@app.route('/admin/reset_password/<int:user_id>', methods=['POST'])
@admin_required
def reset_user_pass(user_id):
    data = request.json
    new_password = data.get('new_password', '123456')
    success = reset_user_password(user_id, new_password)
    return jsonify({'success': success, 'new_password': new_password if success else None})

@app.route('/admin/user_history/<int:user_id>')
@admin_required
def user_history(user_id):
    history = get_user_history_all(user_id)
    return jsonify(history)

@app.route('/admin/send_reply/<int:order_id>', methods=['POST'])
@admin_required
def send_reply(order_id):
    data = request.json
    message = data.get('message', '')
    
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute("SELECT email, name FROM orders WHERE id = ?", (order_id,))
    order = c.fetchone()
    
    if order and message:
        try:
            msg = Message(
                subject='Ответ на вашу заявку в Школу Таро',
                recipients=[order[0]],
                charset='utf-8'
            )
            msg.body = f"""
Здравствуйте, {order[1]}!

{message}

С уважением,
Анна
"""
            mail.send(msg)
            
            add_chat_message(order_id, 'admin', f"📧 Отправлен email-ответ: {message[:50]}...")
            
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    conn.close()
    return jsonify({'success': False})

@app.route('/admin/quick_reply/<int:order_id>', methods=['POST'])
@admin_required
def quick_reply(order_id):
    data = request.json
    template = data.get('template', '')
    
    templates = {
        'standard': 'Спасибо за заявку! Я свяжусь с вами в ближайшее время.',
        'cards': 'Добрый день! Уточните, пожалуйста, какие карты вас интересуют?',
        'price': 'Здравствуйте! Стоимость курса 15 000 ₽. Можем начать в любое удобное время.',
        'time': 'Здравствуйте! Когда вам удобно провести консультацию?'
    }
    
    message = templates.get(template, template)
    
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute("SELECT email, name FROM orders WHERE id = ?", (order_id,))
    order = c.fetchone()
    
    if order and message:
        try:
            msg = Message(
                subject='Ответ на вашу заявку в Школу Таро',
                recipients=[order[0]],
                charset='utf-8'
            )
            msg.body = f"""
Здравствуйте, {order[1]}!

{message}

С уважением,
Анна
"""
            mail.send(msg)
            
            add_chat_message(order_id, 'admin', f"📧 Отправлен быстрый ответ: {message[:50]}...")
            
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    conn.close()
    return jsonify({'success': False})

@app.route('/admin/chat_send/<int:order_id>', methods=['POST'])
@admin_required
def chat_send(order_id):
    data = request.json
    message = data.get('message', '')
    
    if message:
        add_chat_message(order_id, 'admin', message)
    
    return jsonify({'success': True})

@app.route('/admin/chat_messages/<int:order_id>')
@admin_required
def get_chat(order_id):
    messages = get_chat_messages(order_id)
    result = []
    for msg in messages:
        result.append({
            'id': msg[0],
            'sender': msg[1],
            'message': msg[2],
            'date': msg[3],
            'is_read': msg[4]
        })
    return jsonify(result)

@app.route('/static/<path:filename>')
def custom_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    print("=" * 50)
    print("🔮 Сервер Школы Таро запущен!")
    print("=" * 50)
    print("🌐 Главная страница: http://127.0.0.1:5000")
    print("📚 Значения карт: http://127.0.0.1:5000/cards")
    print("🔑 Вход: http://127.0.0.1:5000/login")
    print("📝 Регистрация: http://127.0.0.1:5000/register")
    print("🔐 Админ-панель: http://127.0.0.1:5000/admin")
    print("   Логин: admin")
    print("   Пароль: taro2026")
    print("=" * 50)
    app.run(debug=True)