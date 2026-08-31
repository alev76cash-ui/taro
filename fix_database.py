import sqlite3

def fix_database():
    """Добавляет недостающие колонки в базу данных"""
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()

    # Проверяем существующие колонки
    c.execute("PRAGMA table_info(subscribers)")
    existing_columns = [col[1] for col in c.fetchall()]

    print("📋 Существующие колонки:", existing_columns)

    # Добавляем новые колонки, если их нет
    new_columns = {
        'token': 'TEXT',
        'token_expiry': 'TEXT'
    }

    for col_name, col_type in new_columns.items():
        if col_name not in existing_columns:
            try:
                c.execute(f"ALTER TABLE subscribers ADD COLUMN {col_name} {col_type}")
                print(f"✅ Добавлена колонка: {col_name}")
            except Exception as e:
                print(f"❌ Ошибка при добавлении {col_name}: {e}")
        else:
            print(f"ℹ️ Колонка {col_name} уже существует")

    conn.commit()
    conn.close()
    print("\n✅ База данных обновлена!")

if __name__ == "__main__":
    fix_database()
