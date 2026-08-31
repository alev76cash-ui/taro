import sqlite3

def check_database_structure():
    """Проверяет структуру таблицы tarot_cards"""
    conn = sqlite3.connect('tarot.db')
    c = conn.cursor()

    # Получаем информацию о колонках таблицы
    c.execute("PRAGMA table_info(tarot_cards)")
    columns = c.fetchall()

    print("📊 Структура таблицы tarot_cards:")
    print("-" * 50)
    for col in columns:
        print(f"   {col[1]} - {col[2]}")

    # Проверяем количество записей
    c.execute("SELECT COUNT(*) FROM tarot_cards")
    count = c.fetchone()[0]
    print("-" * 50)
    print(f"📊 Всего записей: {count}")

    # Показываем пример первых 5 карт
    if count > 0:
        print("\n📝 Пример первых 5 карт:")
        c.execute("SELECT name, arcana, suit, image, image_path FROM tarot_cards LIMIT 5")
        sample = c.fetchall()
        for card in sample:
            print(f"   {card[0]} | {card[1]} | {card[2]} | image: {card[3]} | path: {card[4]}")

    conn.close()

if __name__ == "__main__":
    check_database_structure()
