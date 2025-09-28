#!/usr/bin/env python3
"""
Простой веб-парсер для hh.ru без дополнительных зависимостей
Использует только стандартные библиотеки Python
"""

import urllib.request
import urllib.parse
import json
import csv
import re
import gzip
from datetime import datetime
from pathlib import Path
import time
import random

def get_random_headers():
    """Генерация случайных заголовков для обхода блокировок"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36"
    ]
    
    return {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "DNT": "1",
        "Referer": "https://hh.ru/"
    }

def search_vacancies_api(query: str, area: str = "22") -> list:
    """Поиск вакансий через API hh.ru"""
    
    print(f"🔍 API поиск: {query}")
    
    # Параметры запроса
    params = {
        "text": query,
        "area": area,  # 22 = Владивосток
        "per_page": 50,
        "page": 0
    }
    
    # Формируем URL
    base_url = "https://api.hh.ru/vacancies"
    query_string = urllib.parse.urlencode(params)
    url = f"{base_url}?{query_string}"
    
    try:
        # Создаем запрос
        request = urllib.request.Request(url, headers=get_random_headers())
        
        # Выполняем запрос
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status == 200:
                # Читаем данные
                raw_data = response.read()
                
                # Проверяем, сжаты ли данные gzip
                if response.headers.get('Content-Encoding') == 'gzip':
                    raw_data = gzip.decompress(raw_data)
                
                data = json.loads(raw_data.decode('utf-8'))
                
                vacancies = []
                items = data.get('items', [])
                print(f"  📊 Найдено вакансий: {len(items)}")
                
                for item in items:
                    # Извлекаем основную информацию
                    title = item.get('name', '')
                    company = item.get('employer', {}).get('name', 'Не указана')
                    vacancy_id = item.get('id', '')
                    url = item.get('alternate_url', '')
                    
                    # Зарплата
                    salary = item.get('salary')
                    if salary:
                        salary_from = salary.get('from')
                        salary_to = salary.get('to')
                        currency = salary.get('currency', 'RUR')
                        
                        if salary_from and salary_to:
                            salary_text = f"{salary_from:,}–{salary_to:,} {currency}"
                        elif salary_from:
                            salary_text = f"от {salary_from:,} {currency}"
                        elif salary_to:
                            salary_text = f"до {salary_to:,} {currency}"
                        else:
                            salary_text = "не указано"
                    else:
                        salary_text = "не указано"
                    
                    # Дата публикации
                    published_at = item.get('published_at', '')
                    if published_at:
                        try:
                            # Парсим ISO дату
                            pub_datetime = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                            date_text = pub_datetime.strftime("%Y-%m-%d %H:%M")
                            
                            # Определяем относительную дату
                            now = datetime.now()
                            diff = now - pub_datetime.replace(tzinfo=None)
                            
                            if diff.days == 0:
                                relative_date = "сегодня"
                            elif diff.days == 1:
                                relative_date = "вчера"
                            elif diff.days <= 7:
                                relative_date = f"{diff.days} дней назад"
                            else:
                                relative_date = date_text
                        except:
                            date_text = published_at
                            relative_date = "неизвестно"
                    else:
                        date_text = "не указано"
                        relative_date = "неизвестно"
                    
                    # Проверяем, что вакансия свежая (за последние 3 дня)
                    if not is_recent_vacancy(published_at):
                        continue
                    
                    vacancy_data = {
                        "id": vacancy_id,
                        "Название вакансии": title,
                        "Компания": company,
                        "Ссылка": url,
                        "Дата публикации": date_text,
                        "Когда": relative_date,
                        "Зарплата": salary_text,
                        "Запрос": query
                    }
                    
                    vacancies.append(vacancy_data)
                    print(f"    📋 {title} - {company} - {salary_text} - {relative_date}")
                
                return vacancies
                
            else:
                print(f"  ❌ Ошибка HTTP: {response.status}")
                return []
                
    except Exception as e:
        print(f"  ❌ Ошибка запроса: {e}")
        return []

def is_recent_vacancy(published_at: str) -> bool:
    """Проверяет, опубликована ли вакансия за последние 3 дня"""
    if not published_at:
        return False
    
    try:
        # Парсим ISO дату
        pub_datetime = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        
        # Вычисляем разницу в днях
        now = datetime.now()
        diff = now - pub_datetime.replace(tzinfo=None)
        
        # Возвращаем True если вакансия опубликована за последние 3 дня
        return diff.days <= 3
    except:
        return False

def is_relevant_vacancy(title: str) -> bool:
    """Проверяет, относится ли вакансия к закупкам, снабжению или проектам"""
    if not title:
        return False
        
    title_lower = title.lower()
    
    # Ключевые слова для закупок
    procurement_keywords = [
        "закуп", "закупк", "закупочн", "закупщик", "procurement"
    ]
    
    # Ключевые слова для снабжения
    supply_keywords = [
        "снабжен", "снабжени", "снабженческ", "supply"
    ]
    
    # Ключевые слова для проектов
    project_keywords = [
        "проект", "project", "менеджер проект", "руководитель проект", 
        "координатор проект", "управление проект"
    ]
    
    # Проверяем наличие ключевых слов
    has_procurement = any(keyword in title_lower for keyword in procurement_keywords)
    has_supply = any(keyword in title_lower for keyword in supply_keywords)
    has_project = any(keyword in title_lower for keyword in project_keywords)
    
    return has_procurement or has_supply or has_project

def main():
    """Основная функция"""
    print("🌐 ПРОСТОЙ ВЕБ-ПАРСЕР HH.RU")
    print("📅 ФИЛЬТР: ТОЛЬКО ВАКАНСИИ ЗА ПОСЛЕДНИЕ 3 ДНЯ")
    print("=" * 60)
    
    # Запросы для поиска
    queries = [
        # Закупки и снабжение
        "менеджер по закупкам",
        "менеджер по закупу", 
        "менеджер по закупкам и снабжению",
        "специалист по закупкам",
        "закупщик",
        "менеджер по снабжению",
        "специалист по снабжению",
        
        # Проекты
        "менеджер проектов",
        "руководитель проектов",
        "project manager"
    ]
    
    all_vacancies = []
    
    for i, query in enumerate(queries, 1):
        print(f"\n📋 {i}/{len(queries)}: {query}")
        vacancies = search_vacancies_api(query)
        
        # Фильтруем только релевантные вакансии
        relevant_vacancies = [v for v in vacancies if is_relevant_vacancy(v['Название вакансии'])]
        print(f"  ✅ Релевантных: {len(relevant_vacancies)}")
        
        all_vacancies.extend(relevant_vacancies)
        
        # Пауза между запросами
        sleep_time = random.uniform(2, 4)
        print(f"  ⏳ Пауза: {sleep_time:.1f} сек")
        time.sleep(sleep_time)
    
    # Дедупликация по ID
    unique_vacancies = {}
    for vacancy in all_vacancies:
        vacancy_id = vacancy.get("id", "")
        if vacancy_id and vacancy_id not in unique_vacancies:
            unique_vacancies[vacancy_id] = vacancy
        elif not vacancy_id:
            # Если нет ID, используем название + компания
            key = f"{vacancy['Название вакансии']}_{vacancy['Компания']}"
            if key not in unique_vacancies:
                unique_vacancies[key] = vacancy
    
    final_vacancies = list(unique_vacancies.values())
    
    print(f"\n🎯 ИТОГО: {len(final_vacancies)} уникальных вакансий")
    
    # Сохранение в CSV
    if final_vacancies:
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_dir = Path("data") / date_str
        output_dir.mkdir(parents=True, exist_ok=True)
        
        csv_file = output_dir / f"Закупки_Снабжение_Проекты_3дня_{date_str}.csv"
        
        with csv_file.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            
            # Заголовки
            headers = ["Название вакансии", "Компания", "Ссылка", "Дата публикации", "Когда", "Зарплата", "Запрос"]
            writer.writerow(headers)
            
            # Данные
            for vacancy in final_vacancies:
                row = [
                    vacancy.get("Название вакансии", ""),
                    vacancy.get("Компания", ""),
                    vacancy.get("Ссылка", ""),
                    vacancy.get("Дата публикации", ""),
                    vacancy.get("Когда", ""),
                    vacancy.get("Зарплата", ""),
                    vacancy.get("Запрос", "")
                ]
                writer.writerow(row)
        
        print(f"✅ CSV файл создан: {csv_file}")
        
        # Статистика
        with_salary = sum(1 for v in final_vacancies if v['Зарплата'] != "не указано")
        with_date = sum(1 for v in final_vacancies if v['Дата публикации'] != "не указано")
        companies = len(set(v['Компания'] for v in final_vacancies))
        
        print(f"\n📊 СТАТИСТИКА:")
        print(f"  • Всего вакансий: {len(final_vacancies)}")
        print(f"  • Компаний: {companies}")
        print(f"  • С зарплатой: {with_salary}")
        print(f"  • С датой: {with_date}")
        
        # Проверяем, есть ли "Дикий Улов"
        wild_catch = [v for v in final_vacancies if "дикий улов" in v['Компания'].lower()]
        if wild_catch:
            print(f"  🎯 НАЙДЕНА 'Дикий Улов': {len(wild_catch)} вакансий")
            for v in wild_catch:
                print(f"    - {v['Название вакансии']} - {v['Зарплата']} ({v['Когда']})")
        else:
            print(f"  ❌ 'Дикий Улов' не найден")
        
        # Топ-5 компаний
        company_counts = {}
        for vacancy in final_vacancies:
            company = vacancy['Компания']
            company_counts[company] = company_counts.get(company, 0) + 1
        
        top_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"\n🏢 Топ-5 компаний:")
        for company, count in top_companies:
            print(f"  • {company}: {count} вакансий")
    
    else:
        print("❌ Нет данных для сохранения")

if __name__ == "__main__":
    main()
