#!/usr/bin/env python3
"""
🔍 ГЛУБОКИЙ АНАЛИЗ ВАКАНСИЙ ВЛАДИВОСТОКА ЗА 5 ОКТЯБРЯ 2025
Анализ только данных за 5 октября (без дублей и исторических данных)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Настройка matplotlib для русских шрифтов
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

def setup_report_folder():
    """Создаёт папку для отчётов за 5 октября"""
    report_dir = Path("report_oct5")
    report_dir.mkdir(exist_ok=True)
    print(f"📁 Папка для отчётов за 5 октября: {report_dir.absolute()}")
    return report_dir

def load_oct5_data():
    """Загружает только данные за 5 октября"""
    print("📂 Загружаем данные за 5 октября 2025...")
    
    data_dir = Path("data/2025-10-05")
    csv_files = list(data_dir.glob("*.csv"))
    print(f"🔍 Найдено CSV файлов за 5 октября: {len(csv_files)}")
    
    all_data = []
    for csv_file in csv_files:
        print(f"  📄 Загружаем: {csv_file.name}")
        try:
            df = pd.read_csv(csv_file, sep=';', encoding='utf-8-sig')
            all_data.append(df)
        except Exception as e:
            print(f"  ❌ Ошибка при загрузке {csv_file}: {e}")
    
    if not all_data:
        raise ValueError("❌ Не найдено данных за 5 октября!")
    
    # Объединяем данные за 5 октября
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"✅ Загружено {len(combined_df)} записей за 5 октября")
    
    return combined_df

def clean_salary_data(df):
    """Очищает и обрабатывает данные о зарплатах"""
    print("🧹 Очищаем данные о зарплатах...")
    
    def parse_salary(salary_text):
        """Парсит текст зарплаты и возвращает числовые значения"""
        if pd.isna(salary_text) or salary_text == "не указано":
            return None, None
        
        salary_str = str(salary_text).replace(" ", "").replace(",", "").lower()
        
        # Диапазон зарплат
        range_match = re.search(r'(\d+)–(\d+)', salary_str)
        if range_match:
            from_salary = int(range_match.group(1))
            to_salary = int(range_match.group(2))
            return from_salary, to_salary
        
        # "от X"
        from_match = re.search(r'от(\d+)', salary_str)
        if from_match:
            from_salary = int(from_match.group(1))
            return from_salary, None
        
        # "до X"
        to_match = re.search(r'до(\d+)', salary_str)
        if to_match:
            to_salary = int(to_match.group(1))
            return None, to_salary
        
        return None, None
    
    # Парсим зарплаты
    salary_data = df['Зарплата'].apply(parse_salary)
    df['salary_from'] = salary_data.apply(lambda x: x[0] if x[0] is not None else np.nan)
    df['salary_to'] = salary_data.apply(lambda x: x[1] if x[1] is not None else np.nan)
    
    # Вычисляем среднюю зарплату
    df['salary_avg'] = np.where(
        df['salary_to'].notna() & df['salary_from'].notna(),
        (df['salary_from'] + df['salary_to']) / 2,
        np.where(
            df['salary_from'].notna(),
            df['salary_from'],
            df['salary_to']
        )
    )
    
    # Удаляем строки без зарплаты
    initial_count = len(df)
    df = df.dropna(subset=['salary_avg'])
    final_count = len(df)
    
    print(f"  📊 Было записей: {initial_count}")
    print(f"  📊 С зарплатой: {final_count}")
    print(f"  📊 Удалено без зарплаты: {initial_count - final_count}")
    
    return df

def categorize_roles(df):
    """Определяет категории ролей"""
    print("🏷️ Определяем категории ролей...")
    
    def get_role_category(title):
        if pd.isna(title):
            return "Неизвестно"
        
        title_lower = title.lower()
        
        # Продажи
        sales_keywords = ["продаж", "sales", "менеджер по продаж", "руководитель продаж"]
        if any(keyword in title_lower for keyword in sales_keywords):
            return "Продажи"
        
        # Закупки
        procurement_keywords = ["закуп", "закупк", "закупщик", "снабжен"]
        if any(keyword in title_lower for keyword in procurement_keywords):
            return "Закупки"
        
        # Проекты
        project_keywords = ["проект", "project", "менеджер проект", "руководитель проект"]
        if any(keyword in title_lower for keyword in project_keywords):
            return "Проекты"
        
        # Менеджмент
        management_keywords = ["менеджер", "руководитель", "директор"]
        if any(keyword in title_lower for keyword in management_keywords):
            return "Менеджмент"
        
        return "Другое"
    
    df['role_category'] = df['Название вакансии'].apply(get_role_category)
    
    # Статистика по категориям
    role_counts = df['role_category'].value_counts()
    print("  📈 Категории ролей за 5 октября:")
    for role, count in role_counts.items():
        print(f"    • {role}: {count} вакансий")
    
    return df

def calculate_detailed_statistics(df):
    """Вычисляет детальную статистику за 5 октября"""
    print("📊 Вычисляем детальную статистику за 5 октября...")
    
    salaries = df['salary_avg'].dropna()
    
    stats = {
        'date': '2025-10-05',
        'total_vacancies': len(df),
        'with_salary': len(salaries),
        'mean_salary': np.mean(salaries),
        'median_salary': np.median(salaries),
        'std_salary': np.std(salaries),
        'min_salary': np.min(salaries),
        'max_salary': np.max(salaries),
        'q25_salary': np.percentile(salaries, 25),
        'q75_salary': np.percentile(salaries, 75),
        'unique_companies': df['Компания'].nunique()
    }
    
    print("  📈 ДЕТАЛЬНАЯ СТАТИСТИКА за 5 октября:")
    print(f"    • Всего вакансий: {stats['total_vacancies']}")
    print(f"    • С зарплатой: {stats['with_salary']}")
    print(f"    • Уникальных компаний: {stats['unique_companies']}")
    print(f"    • Средняя зарплата: {stats['mean_salary']:,.0f} ₽")
    print(f"    • Медианная зарплата: {stats['median_salary']:,.0f} ₽")
    print(f"    • Разброс (σ): {stats['std_salary']:,.0f} ₽")
    print(f"    • Минимум: {stats['min_salary']:,.0f} ₽")
    print(f"    • Максимум: {stats['max_salary']:,.0f} ₽")
    print(f"    • 25-й процентиль: {stats['q25_salary']:,.0f} ₽")
    print(f"    • 75-й процентиль: {stats['q75_salary']:,.0f} ₽")
    
    return stats

def create_oct5_visualizations(df, report_dir):
    """Создаёт визуализации для 5 октября"""
    print("📊 Создаём визуализации за 5 октября...")
    
    df_with_salary = df.dropna(subset=['salary_avg'])
    print(f"  📊 Анализируем {len(df_with_salary)} вакансий с зарплатой")
    
    # 1. Гистограмма распределения зарплат за 5 октября
    plt.figure(figsize=(12, 7))
    plt.hist(df_with_salary['salary_avg'], bins=25, color='lightblue', edgecolor='navy', alpha=0.7)
    plt.title('💰 Распределение зарплат во Владивостоке\n5 октября 2025 года (данные за 3-5 октября)', fontsize=16, fontweight='bold')
    plt.xlabel('Зарплата, ₽', fontsize=12)
    plt.ylabel('Количество вакансий', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Статистики на графике
    mean_salary = np.mean(df_with_salary['salary_avg'])
    median_salary = np.median(df_with_salary['salary_avg'])
    plt.axvline(mean_salary, color='red', linestyle='--', linewidth=2, label=f'Средняя: {mean_salary:,.0f} ₽')
    plt.axvline(median_salary, color='orange', linestyle='--', linewidth=2, label=f'Медиана: {median_salary:,.0f} ₽')
    plt.legend(fontsize=10)
    
    plt.tight_layout()
    plt.savefig(report_dir / 'oct5_salary_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✅ Создан: oct5_salary_distribution.png")
    
    # 2. Топ-15 компаний за 5 октября
    top_companies = df_with_salary['Компания'].value_counts().head(15)
    
    plt.figure(figsize=(14, 10))
    bars = plt.barh(range(len(top_companies)), top_companies.values, color='lightcoral')
    plt.yticks(range(len(top_companies)), top_companies.index)
    plt.xlabel('Количество вакансий с зарплатой', fontsize=12)
    plt.title('🏢 Топ-15 компаний по количеству вакансий\n5 октября 2025 года (данные за 3-5 октября)', fontsize=16, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    # Значения на столбцах
    for i, bar in enumerate(bars):
        width = bar.get_width()
        plt.text(width + 0.1, bar.get_y() + bar.get_height()/2,
                f'{int(width)}', ha='left', va='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(report_dir / 'oct5_top_companies.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✅ Создан: oct5_top_companies.png")
    
    # 3. Зарплаты по категориям ролей
    role_salaries = df_with_salary.groupby('role_category')['salary_avg'].agg(['mean', 'count']).sort_values('mean', ascending=False)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Средние зарплаты
    bars1 = ax1.bar(role_salaries.index, role_salaries['mean'], color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57'])
    ax1.set_title('💰 Средняя зарплата по категориям\n5 октября 2025 (данные за 3-5 октября)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Средняя зарплата, ₽', fontsize=12)
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3)
    
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 5000,
                f'{height:,.0f} ₽', ha='center', va='bottom', fontweight='bold', fontsize=9)
    
    # Количество вакансий
    bars2 = ax2.bar(role_salaries.index, role_salaries['count'], color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57'])
    ax2.set_title('📊 Количество вакансий по категориям\n5 октября 2025 (данные за 3-5 октября)', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Количество вакансий', fontsize=12)
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3)
    
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{int(height)}', ha='center', va='bottom', fontweight='bold', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(report_dir / 'oct5_salary_by_role.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✅ Создан: oct5_salary_by_role.png")

def create_oct5_summary_report(df, stats, report_dir):
    """Создаёт детальный отчёт за 5 октября"""
    print("📋 Создаём детальный отчёт за 5 октября...")
    
    excel_file = report_dir / 'oct5_detailed_report.xlsx'
    df_with_salary = df.dropna(subset=['salary_avg'])
    
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # Общая статистика
        summary_data = {
            'Показатель': ['Дата анализа', 'Всего вакансий', 'С зарплатой', 'Уникальных компаний',
                          'Средняя зарплата', 'Медианная зарплата', 'Минимальная зарплата', 
                          'Максимальная зарплата', 'Разброс (σ)', '25-й процентиль', '75-й процентиль'],
            'Значение': [stats['date'], stats['total_vacancies'], stats['with_salary'], stats['unique_companies'],
                        f"{stats['mean_salary']:,.0f} ₽", f"{stats['median_salary']:,.0f} ₽",
                        f"{stats['min_salary']:,.0f} ₽", f"{stats['max_salary']:,.0f} ₽",
                        f"{stats['std_salary']:,.0f} ₽", f"{stats['q25_salary']:,.0f} ₽",
                        f"{stats['q75_salary']:,.0f} ₽"]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Общая статистика 5 октября', index=False)
        
        # Статистика по ролям
        role_stats = df_with_salary.groupby('role_category')['salary_avg'].agg([
            'count', 'mean', 'median', 'min', 'max', 'std'
        ]).round(0)
        role_stats.columns = ['Количество', 'Средняя', 'Медиана', 'Минимум', 'Максимум', 'Разброс']
        role_stats.to_excel(writer, sheet_name='По категориям ролей')
        
        # Детальная статистика по компаниям
        company_stats = df_with_salary.groupby('Компания').agg({
            'salary_avg': ['count', 'mean', 'median'],
            'Название вакансии': lambda x: ', '.join(x.unique()[:3])  # Первые 3 уникальных названия
        }).round(0)
        company_stats.columns = ['Количество вакансий', 'Средняя зарплата', 'Медианная зарплата', 'Примеры вакансий']
        company_stats = company_stats.sort_values('Количество вакансий', ascending=False)
        company_stats.to_excel(writer, sheet_name='По компаниям (детально)')
        
        # Все данные с зарплатой
        df_with_salary.to_excel(writer, sheet_name='Все данные 5 октября', index=False)
    
    print(f"  ✅ Создан: {excel_file}")

def main():
    """Основная функция анализа за 5 октября"""
    print("🔍 ГЛУБОКИЙ АНАЛИЗ ВАКАНСИЙ ВЛАДИВОСТОКА ЗА 5 ОКТЯБРЯ 2025")
    print("=" * 70)
    
    try:
        # 1. Создаём папку для отчётов
        report_dir = setup_report_folder()
        
        # 2. Загружаем только данные за 5 октября
        df = load_oct5_data()
        
        # 3. Очищаем данные
        df = clean_salary_data(df)
        
        # 4. Категоризируем роли
        df = categorize_roles(df)
        
        # 5. Вычисляем детальную статистику
        stats = calculate_detailed_statistics(df)
        
        # 6. Создаём визуализации
        create_oct5_visualizations(df, report_dir)
        
        # 7. Создаём детальный отчёт
        create_oct5_summary_report(df, stats, report_dir)
        
        print("\n🎉 ГЛУБОКИЙ АНАЛИЗ ЗА 5 ОКТЯБРЯ ЗАВЕРШЁН!")
        print(f"📁 Все файлы сохранены в папке: {report_dir.absolute()}")
        print("\n📊 Созданные файлы:")
        print("  • oct5_salary_distribution.png - Распределение зарплат")
        print("  • oct5_top_companies.png - Топ-15 компаний")
        print("  • oct5_salary_by_role.png - Зарплаты по ролям")
        print("  • oct5_detailed_report.xlsx - Детальный Excel отчёт")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
