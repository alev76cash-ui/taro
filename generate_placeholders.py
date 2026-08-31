from PIL import Image, ImageDraw, ImageFont
import os

def create_placeholder_card(card_name, filename):
    """Создает placeholder изображение для карты"""
    # Создаем изображение 300x500 с градиентом
    img = Image.new('RGB', (300, 500), color='white')
    draw = ImageDraw.Draw(img)

    # Рисуем рамку
    draw.rectangle([10, 10, 290, 490], outline='gold', width=3)

    # Рисуем фон (градиент)
    for i in range(500):
        color = int(100 + (i / 500) * 100)
        draw.line([(0, i), (300, i)], fill=(color, color, 200))

    # Добавляем текст
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()

    # Разбиваем название на слова
    words = card_name.split()
    y_position = 150

    for word in words:
        # Получаем размер текста
        bbox = draw.textbbox((0, 0), word, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Рисуем текст по центру
        x_position = (300 - text_width) // 2
        draw.text((x_position, y_position), word, fill='gold', font=font)
        y_position += text_height + 10

    # Добавляем символ масти
    suit_symbols = {
        'Жезлы': '🔥',
        'Кубки': '💧',
        'Мечи': '⚔️',
        'Пентакли': '💰'
    }

    for suit, symbol in suit_symbols.items():
        if suit in card_name or suit in filename:
            draw.text((140, 350), symbol, fill='gold', font=ImageFont.truetype("arial.ttf", 60) if font else font)
            break

    # Сохраняем
    img.save(f'static/images/cards/{filename}')
    print(f"✅ Создано: {filename}")

# Список всех карт
cards = [
    # Старшие Арканы
    ("Шут", "fool.jpg"),
    ("Маг", "magician.jpg"),
    ("Верховная Жрица", "high_priestess.jpg"),
    ("Императрица", "empress.jpg"),
    ("Император", "emperor.jpg"),
    ("Иерофант", "hierophant.jpg"),
    ("Влюбленные", "lovers.jpg"),
    ("Колесница", "chariot.jpg"),
    ("Сила", "strength.jpg"),
    ("Отшельник", "hermit.jpg"),
    ("Колесо Фортуны", "wheel_of_fortune.jpg"),
    ("Справедливость", "justice.jpg"),
    ("Повешенный", "hanged_man.jpg"),
    ("Смерть", "death.jpg"),
    ("Умеренность", "temperance.jpg"),
    ("Дьявол", "devil.jpg"),
    ("Башня", "tower.jpg"),
    ("Звезда", "star.jpg"),
    ("Луна", "moon.jpg"),
    ("Солнце", "sun.jpg"),
    ("Суд", "judgment.jpg"),
    ("Мир", "world.jpg"),

    # Жезлы
    ("Туз Жезлов", "ace_of_wands.jpg"),
    ("Двойка Жезлов", "two_of_wands.jpg"),
    ("Тройка Жезлов", "three_of_wands.jpg"),
    ("Четверка Жезлов", "four_of_wands.jpg"),
    ("Пятерка Жезлов", "five_of_wands.jpg"),
    ("Шестерка Жезлов", "six_of_wands.jpg"),
    ("Семерка Жезлов", "seven_of_wands.jpg"),
    ("Восьмерка Жезлов", "eight_of_wands.jpg"),
    ("Девятка Жезлов", "nine_of_wands.jpg"),
    ("Десятка Жезлов", "ten_of_wands.jpg"),
    ("Паж Жезлов", "page_of_wands.jpg"),
    ("Рыцарь Жезлов", "knight_of_wands.jpg"),
    ("Королева Жезлов", "queen_of_wands.jpg"),
    ("Король Жезлов", "king_of_wands.jpg"),

    # Кубки
    ("Туз Кубков", "ace_of_cups.jpg"),
    ("Двойка Кубков", "two_of_cups.jpg"),
    ("Тройка Кубков", "three_of_cups.jpg"),
    ("Четверка Кубков", "four_of_cups.jpg"),
    ("Пятерка Кубков", "five_of_cups.jpg"),
    ("Шестерка Кубков", "six_of_cups.jpg"),
    ("Семерка Кубков", "seven_of_cups.jpg"),
    ("Восьмерка Кубков", "eight_of_cups.jpg"),
    ("Девятка Кубков", "nine_of_cups.jpg"),
    ("Десятка Кубков", "ten_of_cups.jpg"),
    ("Паж Кубков", "page_of_cups.jpg"),
    ("Рыцарь Кубков", "knight_of_cups.jpg"),
    ("Королева Кубков", "queen_of_cups.jpg"),
    ("Король Кубков", "king_of_cups.jpg"),

    # Мечи
    ("Туз Мечей", "ace_of_swords.jpg"),
    ("Двойка Мечей", "two_of_swords.jpg"),
    ("Тройка Мечей", "three_of_swords.jpg"),
    ("Четверка Мечей", "four_of_swords.jpg"),
    ("Пятерка Мечей", "five_of_swords.jpg"),
    ("Шестерка Мечей", "six_of_swords.jpg"),
    ("Семерка Мечей", "seven_of_swords.jpg"),
    ("Восьмерка Мечей", "eight_of_swords.jpg"),
    ("Девятка Мечей", "nine_of_swords.jpg"),
    ("Десятка Мечей", "ten_of_swords.jpg"),
    ("Паж Мечей", "page_of_swords.jpg"),
    ("Рыцарь Мечей", "knight_of_swords.jpg"),
    ("Королева Мечей", "queen_of_swords.jpg"),
    ("Король Мечей", "king_of_swords.jpg"),

    # Пентакли
    ("Туз Пентаклей", "ace_of_pentacles.jpg"),
    ("Двойка Пентаклей", "two_of_pentacles.jpg"),
    ("Тройка Пентаклей", "three_of_pentacles.jpg"),
    ("Четверка Пентаклей", "four_of_pentacles.jpg"),
    ("Пятерка Пентаклей", "five_of_pentacles.jpg"),
    ("Шестерка Пентаклей", "six_of_pentacles.jpg"),
    ("Семерка Пентаклей", "seven_of_pentacles.jpg"),
    ("Восьмерка Пентаклей", "eight_of_pentacles.jpg"),
    ("Девятка Пентаклей", "nine_of_pentacles.jpg"),
    ("Десятка Пентаклей", "ten_of_pentacles.jpg"),
    ("Паж Пентаклей", "page_of_pentacles.jpg"),
    ("Рыцарь Пентаклей", "knight_of_pentacles.jpg"),
    ("Королева Пентаклей", "queen_of_pentacles.jpg"),
    ("Король Пентаклей", "king_of_pentacles.jpg"),
]

# Создаем изображения
for card_name, filename in cards:
    create_placeholder_card(card_name, filename)

print("\n✅ Все 78 placeholder изображений созданы!")
