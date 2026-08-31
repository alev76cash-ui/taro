import sqlite3

def fix_database():
    """Добавляет все недостающие колонки в базу данных"""
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()

    # Получаем существующие колонки
    c.execute("PRAGMA table_info(subscribers)")
    existing_columns = [col[1] for col in c.fetchall()]

    print("📋 Существующие колонки:", existing_columns)

    # Все необходимые колонки
    required_columns = {
        'test_result': 'TEXT',
        'token': 'TEXT',
        'token_expiry': 'TEXT'
    }

    # Добавляем недостающие колонки
    for col_name, col_type in required_columns.items():
        if col_name not in existing_columns:
            try:
                c.execute(f"ALTER TABLE subscribers ADD COLUMN {col_name} {col_type}")
                print(f"✅ Добавлена колонка: {col_name}")
            except Exception as e:
                print(f"❌ Ошибка при добавлении {col_name}: {e}")
        else:
            print(f"ℹ️ Колонка {col_name} уже существует")

    # Проверяем, что колонки действительно добавились
    c.execute("PRAGMA table_info(subscribers)")
    updated_columns = [col[1] for col in c.fetchall()]
    print("\n📋 Обновленные колонки:", updated_columns)

    conn.commit()
    conn.close()
    print("\n✅ База данных успешно обновлена!")

def check_data():
    """Проверяет данные в базе"""
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()

    # Проверяем структуру
    c.execute("PRAGMA table_info(subscribers)")
    columns = c.fetchall()
    print("\n🔍 Детальная структура таблицы:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

    # Проверяем данные
    c.execute("SELECT * FROM subscribers")
    rows = c.fetchall()
    print(f"\n👥 Всего записей: {len(rows)}")

    if rows:
        print("\n📝 Первые 3 записи:")
        for i, row in enumerate(rows[:3]):
            print(f"  {i+1}. {row}")

    conn.close()

if __name__ == "__main__":
    print("="*50)
    print("🔧 ИСПРАВЛЕНИЕ БАЗЫ ДАННЫХ")
    print("="*50)

    # Сначала проверяем текущее состояние
    check_data()

    print("\n" + "="*50)
    print("🔄 ОБНОВЛЕНИЕ СТРУКТУРЫ")
    print("="*50)

    # Обновляем базу
    fix_database()

    # Проверяем результат
    print("\n" + "="*50)
    print("✅ ПРОВЕРКА РЕЗУЛЬТАТА")
    print("="*50)
    check_data()
