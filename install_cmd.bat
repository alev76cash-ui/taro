@echo off
echo ========================================
echo    Установка окружения для сайта Таро
echo ========================================
echo.

echo Создание виртуального окружения...
python -m venv .venv

echo Активация окружения...
call .venv\Scripts\activate.bat

echo Установка пакетов...
pip install flask flask-mail requests Pillow

echo.
echo ========================================
echo ✅ Установка завершена!
echo ========================================
echo.
echo Для запуска сайта выполните:
echo   call .venv\Scripts\activate.bat
echo   python app.py
echo.
pause