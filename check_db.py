import sqlite3

def check_database():
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()

    print("=" * 50)
    print("🔍 ПРОВЕРКА БАЗЫ ДАННЫХ")
    print("=" * 50)

    # Проверяем структуру таблицы users
    c.execute("PRAGMA table_info(users)")
    columns = c.fetchall()
    print("\n📋 Структура таблицы users:")
    for col in columns:
        print(f"   {col[1]} - {col[2]}")

    # Получаем всех пользователей
    c.execute("SELECT id, email, username, name, password FROM users")
    users = c.fetchall()

    print(f"\n👥 Найдено пользователей: {len(users)}")

    for user in users:
        print(f"\n📧 Email: {user[1]}")
        print(f"   Username: {user[2]}")
        print(f"   Имя: {user[3]}")
        print(f"   Хеш пароля: {user[4][:20]}...")

    conn.close()

if __name__ == "__main__":
    check_database()
