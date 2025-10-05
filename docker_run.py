#!/usr/bin/env python3
"""
🐳 Docker Runner для HH_Watcher
Удобный скрипт для запуска различных задач в Docker
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Выполняет команду и выводит результат."""
    print(f"\n🔄 {description}...")
    print(f"Команда: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - успешно!")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при {description}:")
        print(f"Код ошибки: {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def check_docker():
    """Проверяет установку Docker."""
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        subprocess.run(["docker-compose", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker или Docker Compose не установлен!")
        print("Установите Docker Desktop: https://www.docker.com/products/docker-desktop")
        return False

def build_image():
    """Собирает Docker образ."""
    return run_command("docker build -t hh-watcher .", "Сборка Docker образа")

def run_full_analysis():
    """Запускает полный анализ."""
    return run_command(
        "docker-compose up --build hh-watcher",
        "Полный анализ (парсинг + анализ + отчёты)"
    )

def run_parsing_only():
    """Запускает только парсинг."""
    return run_command(
        "docker-compose up --build hh-parser",
        "Только парсинг данных"
    )

def run_analysis_only():
    """Запускает только анализ."""
    return run_command(
        "docker-compose up --build hh-analyzer",
        "Только анализ данных"
    )

def run_specific_script(script_name):
    """Запускает конкретный скрипт в Docker."""
    if not os.path.exists(script_name):
        print(f"❌ Скрипт {script_name} не найден!")
        return False
    
    cmd = f"docker run --rm -v {os.getcwd()}/data:/app/data -v {os.getcwd()}/report_oct5:/app/report_oct5 -v {os.getcwd()}/report_dynamics:/app/report_dynamics -v {os.getcwd()}/report_automated:/app/report_automated hh-watcher python {script_name}"
    return run_command(cmd, f"Запуск {script_name}")

def clean_docker():
    """Очищает Docker ресурсы."""
    print("\n🧹 Очистка Docker ресурсов...")
    run_command("docker-compose down", "Остановка контейнеров")
    run_command("docker system prune -f", "Очистка неиспользуемых ресурсов")

def show_menu():
    """Показывает меню опций."""
    print("\n🐳 HH_Watcher Docker Runner")
    print("=" * 50)
    print("1. 🔨 Собрать Docker образ")
    print("2. 🚀 Полный анализ (парсинг + анализ + отчёты)")
    print("3. 📊 Только парсинг данных")
    print("4. 📈 Только анализ данных")
    print("5. 🎯 Запустить конкретный скрипт")
    print("6. 🧹 Очистить Docker ресурсы")
    print("7. ❌ Выход")
    print("=" * 50)

def main():
    """Основная функция."""
    if not check_docker():
        return
    
    while True:
        show_menu()
        choice = input("\nВыберите опцию (1-7): ").strip()
        
        if choice == "1":
            build_image()
        elif choice == "2":
            run_full_analysis()
        elif choice == "3":
            run_parsing_only()
        elif choice == "4":
            run_analysis_only()
        elif choice == "5":
            print("\nДоступные скрипты:")
            scripts = [
                "sales_parser.py",
                "zakup_parser.py", 
                "vacancy_analysis_oct5.py",
                "vacancy_dynamics_comparison.py",
                "create_automated_report.py"
            ]
            for i, script in enumerate(scripts, 1):
                print(f"  {i}. {script}")
            
            try:
                script_choice = int(input("\nВыберите номер скрипта (1-5): "))
                if 1 <= script_choice <= 5:
                    run_specific_script(scripts[script_choice - 1])
                else:
                    print("❌ Неверный номер!")
            except ValueError:
                print("❌ Введите число!")
        elif choice == "6":
            clean_docker()
        elif choice == "7":
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор!")
        
        input("\nНажмите Enter для продолжения...")

if __name__ == "__main__":
    main()

