import sqlite3

def view_database():
    """Безопасный просмотр базы данных с учетом всех колонок"""
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()

    # Получаем информацию о структуре таблицы
    c.execute("PRAGMA table_info(subscribers)")
    columns_info = c.fetchall()
    columns = [col[1] for col in columns_info]

    print("📋 Структура таблицы:")
    for col in columns_info:
        print(f"  - {col[1]} ({col[2]})")

    # Получаем все данные
    c.execute("SELECT * FROM subscribers ORDER BY date DESC")
    rows = c.fetchall()

    print("\n" + "="*80)
    print("📋 СПИСОК ПОДПИСЧИКОВ")
    print("="*80)

    if not rows:
        print("❌ В базе нет подписчиков")
    else:
        for i, row in enumerate(rows, 1):
            print(f"\n{i}. ", end="")
            # Выводим все пары "колонка: значение"
            for j, col in enumerate(columns):
                if j < len(row) and row[j] is not None:
                    value = row[j]
                    if col in ['email', 'date', 'test_result', 'token']:
                        print(f"{col}: {value} | ", end="")
            print()

    print(f"\n👥 Всего: {len(rows)} подписчиков")
    conn.close()

def fix_database():
    """Добавляет недостающие колонки, если их нет"""
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()

    # Проверяем существующие колонки
    c.execute("PRAGMA table_info(subscribers)")
    existing_columns = [col[1] for col in c.fetchall()]

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

    conn.commit()
    conn.close()

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "fix":
        fix_database()
    else:
        view_database()
        print("\n💡 Совет: Запусти 'python view_db.py fix' для добавления недостающих колонок")
