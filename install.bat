@echo off
chcp 65001 > nul
title Установка окружения для сайта Таро
echo ========================================
echo    Установка окружения для сайта Таро
echo ========================================
echo.

:: Проверка наличия Python
echo [1/4] Проверка установки Python...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python не найден!
    echo.
    echo Пожалуйста, скачайте и установите Python с официального сайта:
    echo https://www.python.org/downloads/
    echo.
    echo ВАЖНО: При установке отметьте галочку "Add Python to PATH"
    echo.
    pause
    exit /b 1
) else (
    echo ✅ Python найден
    python --version
)

:: Обновление pip
echo.
echo [2/4] Обновление pip...
python -m pip install --upgrade pip
echo ✅ pip обновлен

:: Установка зависимостей
echo.
echo [3/4] Установка необходимых пакетов...
echo.

pip install flask
pip install flask-mail
pip install requests
pip install sqlite3
pip install hashlib
pip install secrets
pip install datetime

:: Проверка установки Pillow для изображений
echo.
echo [4/4] Установка Pillow для работы с изображениями...
pip install Pillow

echo.
echo ========================================
echo ✅ Установка завершена!
echo ========================================
echo.
echo Для запуска сайта выполните:
echo   python app.py
echo.
echo Затем откройте в браузере: http://127.0.0.1:5000
echo.
pause