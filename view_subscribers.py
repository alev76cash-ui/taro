import sqlite3
from tabulate import tabulate

def view_subscribers():
    """Просмотр всех подписчиков и их результатов теста"""

    # Подключаемся к базе данных
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()

    # Получаем всех подписчиков
    c.execute("SELECT id, email, date, test_result FROM subscribers ORDER BY date DESC")
    rows = c.fetchall()

    print("\n" + "="*80)
    print("🔮 ПОДПИСЧИКИ ШКОЛЫ ТАРО")
    print("="*80)

    if not rows:
        print("❌ Пока нет подписчиков")
    else:
        # Подготавливаем данные для красивой таблицы
        table_data = []
        for row in rows:
            table_data.append([
                row[0],  # id
                row[1],  # email
                row[2],  # дата
                row[3] if row[3] else "❌ не проходил тест"  # результат теста
            ])

        # Выводим таблицу
        print(tabulate(table_data,
                       headers=["ID", "Email", "Дата подписки", "Результат теста"],
                       tablefmt="grid"))

        # Статистика
        print("\n" + "="*80)
        print("📊 СТАТИСТИКА")
        print("="*80)

        # Всего подписчиков
        print(f"👥 Всего подписчиков: {len(rows)}")

        # Сколько прошли тест
        test_count = len([r for r in rows if r[3]])
        print(f"📋 Прошли тест: {test_count} ({test_count/len(rows)*100:.1f}%)")

        # Распределение по картам
        c.execute("SELECT test_result, COUNT(*) FROM subscribers WHERE test_result IS NOT NULL GROUP BY test_result")
        card_stats = c.fetchall()

        if card_stats:
            print("\n🃏 Популярность карт:")
            for card, count in card_stats:
                percentage = count / test_count * 100
                bar = "█" * int(percentage / 5)  # Полоска для наглядности
                print(f"  {card}: {count} чел. ({percentage:.1f}%) {bar}")

    conn.close()

    # Дополнительно: просмотр файла emails.txt (резервная копия)
    try:
        with open('emails.txt', 'r', encoding='utf-8') as f:
            emails = f.readlines()
        print(f"\n📁 Резервная копия (emails.txt): {len(emails)} записей")
    except:
        print("\n📁 Файл emails.txt не найден")

def export_to_csv():
    """Экспорт подписчиков в CSV файл"""
    import csv
    from datetime import datetime

    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute("SELECT id, email, date, test_result FROM subscribers ORDER BY date DESC")
    rows = c.fetchall()

    filename = f'subscribers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Email', 'Дата подписки', 'Результат теста'])
        writer.writerows(rows)

    print(f"✅ Экспортировано в файл: {filename}")
    conn.close()

def search_subscriber(email_search):
    """Поиск подписчика по email"""
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()

    c.execute("SELECT id, email, date, test_result FROM subscribers WHERE email LIKE ?",
              (f'%{email_search}%',))
    rows = c.fetchall()

    if rows:
        print(f"\n🔍 Найдено {len(rows)} подписчиков:")
        for row in rows:
            print(f"  ID: {row[0]}")
            print(f"  Email: {row[1]}")
            print(f"  Дата: {row[2]}")
            print(f"  Результат теста: {row[3] if row[3] else 'не проходил'}")
            print("-" * 40)
    else:
        print("❌ Ничего не найдено")

    conn.close()

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "csv":
            export_to_csv()
        elif sys.argv[1] == "search" and len(sys.argv) > 2:
            search_subscriber(sys.argv[2])
        else:
            print("Использование:")
            print("  python view_subscribers.py           - показать всех подписчиков")
            print("  python view_subscribers.py csv       - экспорт в CSV")
            print("  python view_subscribers.py search email@example.com - поиск по email")
    else:
        view_subscribers()
