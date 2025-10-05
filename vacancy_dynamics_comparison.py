#!/usr/bin/env python3
"""
📈 АНАЛИЗ ДИНАМИКИ РЫНКА ТРУДА ВЛАДИВОСТОКА
Сравнение данных 26 сентября vs 5 октября 2025
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
    """Создаёт папку для отчётов динамики"""
    report_dir = Path("report_dynamics")
    report_dir.mkdir(exist_ok=True)
    print(f"📁 Папка для отчётов динамики: {report_dir.absolute()}")
    return report_dir

def load_data_by_date():
    """Загружает данные по датам отдельно"""
    print("📂 Загружаем данные по датам...")
    
    data_26sep = []
    data_5oct = []
    
    # Данные за 26 сентября
    sep_dir = Path("data/2025-09-26")
    if sep_dir.exists():
        sep_files = list(sep_dir.glob("*.csv"))
        print(f"🔍 Найдено файлов за 26 сентября: {len(sep_files)}")
        
        for csv_file in sep_files:
            print(f"  📄 Загружаем: {csv_file.name}")
            try:
                df = pd.read_csv(csv_file, sep=';', encoding='utf-8-sig')
                data_26sep.append(df)
            except Exception as e:
                print(f"  ❌ Ошибка: {e}")
    
    # Данные за 5 октября
    oct_dir = Path("data/2025-10-05")
    if oct_dir.exists():
        oct_files = list(oct_dir.glob("*.csv"))
        print(f"🔍 Найдено файлов за 5 октября: {len(oct_files)}")
        
        for csv_file in oct_files:
            print(f"  📄 Загружаем: {csv_file.name}")
            try:
                df = pd.read_csv(csv_file, sep=';', encoding='utf-8-sig')
                data_5oct.append(df)
            except Exception as e:
                print(f"  ❌ Ошибка: {e}")
    
    # Объединяем данные по датам
    df_26sep = pd.concat(data_26sep, ignore_index=True) if data_26sep else pd.DataFrame()
    df_5oct = pd.concat(data_5oct, ignore_index=True) if data_5oct else pd.DataFrame()
    
    print(f"✅ 26 сентября: {len(df_26sep)} записей")
    print(f"✅ 5 октября: {len(df_5oct)} записей")
    
    return df_26sep, df_5oct

def clean_salary_data(df, date_name):
    """Очищает данные о зарплатах"""
    print(f"🧹 Очищаем данные за {date_name}...")
    
    if len(df) == 0:
        return df
    
    def parse_salary(salary_text):
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
    
    print(f"  📊 {date_name}: {initial_count} → {final_count} (с зарплатой)")
    
    return df

def categorize_roles(df):
    """Определяет категории ролей"""
    if len(df) == 0:
        return df
    
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
    return df

def calculate_comparison_stats(df_26sep, df_5oct):
    """Вычисляет сравнительную статистику"""
    print("📊 Вычисляем сравнительную статистику...")
    
    def get_stats(df, date_name):
        if len(df) == 0:
            return {
                'date': date_name,
                'total_vacancies': 0,
                'with_salary': 0,
                'unique_companies': 0,
                'mean_salary': 0,
                'median_salary': 0,
                'std_salary': 0,
                'min_salary': 0,
                'max_salary': 0
            }
        
        salaries = df['salary_avg'].dropna()
        return {
            'date': date_name,
            'total_vacancies': len(df),
            'with_salary': len(salaries),
            'unique_companies': df['Компания'].nunique(),
            'mean_salary': np.mean(salaries),
            'median_salary': np.median(salaries),
            'std_salary': np.std(salaries),
            'min_salary': np.min(salaries),
            'max_salary': np.max(salaries)
        }
    
    stats_26sep = get_stats(df_26sep, "26 сентября")
    stats_5oct = get_stats(df_5oct, "5 октября")
    
    # Вычисляем изменения
    changes = {}
    for key in ['total_vacancies', 'with_salary', 'unique_companies', 'mean_salary', 'median_salary']:
        if key in stats_26sep and key in stats_5oct:
            old_val = stats_26sep[key]
            new_val = stats_5oct[key]
            if old_val != 0:
                change_pct = ((new_val - old_val) / old_val) * 100
                changes[key] = {
                    'old': old_val,
                    'new': new_val,
                    'change': new_val - old_val,
                    'change_pct': change_pct
                }
    
    print("  📈 СРАВНИТЕЛЬНАЯ СТАТИСТИКА:")
    print(f"    📅 26 сентября: {stats_26sep['with_salary']} вакансий, средняя {stats_26sep['mean_salary']:,.0f} ₽")
    print(f"    📅 5 октября: {stats_5oct['with_salary']} вакансий, средняя {stats_5oct['mean_salary']:,.0f} ₽")
    
    if 'with_salary' in changes:
        change = changes['with_salary']
        print(f"    📊 Изменение количества: {change['change']:+d} ({change['change_pct']:+.1f}%)")
    
    if 'mean_salary' in changes:
        change = changes['mean_salary']
        print(f"    💰 Изменение средней зарплаты: {change['change']:+,.0f} ₽ ({change['change_pct']:+.1f}%)")
    
    return stats_26sep, stats_5oct, changes

def create_dynamics_visualizations(df_26sep, df_5oct, stats_26sep, stats_5oct, changes, report_dir):
    """Создаёт визуализации динамики"""
    print("📊 Создаём визуализации динамики...")
    
    # 1. Сравнение основных показателей
    metrics = ['Количество вакансий', 'Средняя зарплата', 'Медианная зарплата', 'Уникальных компаний']
    sep_values = [stats_26sep['with_salary'], stats_26sep['mean_salary'], 
                 stats_26sep['median_salary'], stats_26sep['unique_companies']]
    oct_values = [stats_5oct['with_salary'], stats_5oct['mean_salary'], 
                 stats_5oct['median_salary'], stats_5oct['unique_companies']]
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # График 1: Количество вакансий
    dates = ['26 сентября', '5 октября']
    values = [stats_26sep['with_salary'], stats_5oct['with_salary']]
    bars1 = ax1.bar(dates, values, color=['lightblue', 'lightcoral'])
    ax1.set_title('📊 Количество вакансий с зарплатой', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Количество вакансий')
    
    # Добавляем значения на столбцы
    for i, bar in enumerate(bars1):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 5,
                f'{int(height)}', ha='center', va='bottom', fontweight='bold')
    
    # Добавляем темп роста между столбцами
    if 'with_salary' in changes:
        change = changes['with_salary']
        delta = change['change_pct']
        arrow = '↑' if delta > 0 else '↓' if delta < 0 else '→'
        color = 'green' if delta > 0 else 'red' if delta < 0 else 'gray'
        
        # Позиция для стрелки (между столбцами)
        mid_x = (bars1[0].get_x() + bars1[0].get_width() + bars1[1].get_x()) / 2
        max_y = max(values) + 15
        
        ax1.text(mid_x, max_y, f'{arrow} {delta:+.1f}%', 
                ha='center', va='bottom', fontweight='bold', fontsize=12, color=color)
    
    ax1.grid(True, alpha=0.3)
    
    # График 2: Средние зарплаты
    values2 = [stats_26sep['mean_salary'], stats_5oct['mean_salary']]
    bars2 = ax2.bar(dates, values2, color=['lightgreen', 'orange'])
    ax2.set_title('💰 Средние зарплаты', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Зарплата, ₽')
    
    for i, bar in enumerate(bars2):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 5000,
                f'{height:,.0f} ₽', ha='center', va='bottom', fontweight='bold')
    
    # Добавляем темп роста для зарплат
    if 'mean_salary' in changes:
        change = changes['mean_salary']
        delta = change['change_pct']
        arrow = '↑' if delta > 0 else '↓' if delta < 0 else '→'
        color = 'green' if delta > 0 else 'red' if delta < 0 else 'gray'
        
        mid_x = (bars2[0].get_x() + bars2[0].get_width() + bars2[1].get_x()) / 2
        max_y = max(values2) + 15000
        
        ax2.text(mid_x, max_y, f'{arrow} {delta:+.1f}%', 
                ha='center', va='bottom', fontweight='bold', fontsize=12, color=color)
    
    ax2.grid(True, alpha=0.3)
    
    # График 3: Медианные зарплаты
    values3 = [stats_26sep['median_salary'], stats_5oct['median_salary']]
    bars3 = ax3.bar(dates, values3, color=['purple', 'pink'])
    ax3.set_title('📈 Медианные зарплаты', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Зарплата, ₽')
    
    for i, bar in enumerate(bars3):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 5000,
                f'{height:,.0f} ₽', ha='center', va='bottom', fontweight='bold')
    
    # Добавляем темп роста для медианных зарплат
    if 'median_salary' in changes:
        change = changes['median_salary']
        delta = change['change_pct']
        arrow = '↑' if delta > 0 else '↓' if delta < 0 else '→'
        color = 'green' if delta > 0 else 'red' if delta < 0 else 'gray'
        
        mid_x = (bars3[0].get_x() + bars3[0].get_width() + bars3[1].get_x()) / 2
        max_y = max(values3) + 15000
        
        ax3.text(mid_x, max_y, f'{arrow} {delta:+.1f}%', 
                ha='center', va='bottom', fontweight='bold', fontsize=12, color=color)
    
    ax3.grid(True, alpha=0.3)
    
    # График 4: Количество компаний
    values4 = [stats_26sep['unique_companies'], stats_5oct['unique_companies']]
    bars4 = ax4.bar(dates, values4, color=['brown', 'gray'])
    ax4.set_title('🏢 Количество уникальных компаний', fontsize=14, fontweight='bold')
    ax4.set_ylabel('Количество компаний')
    
    for i, bar in enumerate(bars4):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{int(height)}', ha='center', va='bottom', fontweight='bold')
    
    # Добавляем темп роста для компаний
    if 'unique_companies' in changes:
        change = changes['unique_companies']
        delta = change['change_pct']
        arrow = '↑' if delta > 0 else '↓' if delta < 0 else '→'
        color = 'green' if delta > 0 else 'red' if delta < 0 else 'gray'
        
        mid_x = (bars4[0].get_x() + bars4[0].get_width() + bars4[1].get_x()) / 2
        max_y = max(values4) + 3
        
        ax4.text(mid_x, max_y, f'{arrow} {delta:+.1f}%', 
                ha='center', va='bottom', fontweight='bold', fontsize=12, color=color)
    
    ax4.grid(True, alpha=0.3)
    
    plt.suptitle('📈 ДИНАМИКА РЫНКА ТРУДА ВЛАДИВОСТОКА\n26 сентября (данные за 24-26.09) vs 5 октября (данные за 3-5.10) 2025', 
                 fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(report_dir / 'dynamics_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✅ Создан: dynamics_comparison.png")
    
    # 2. Сравнение по категориям ролей (если есть данные)
    if len(df_26sep) > 0 and len(df_5oct) > 0:
        df_26sep_clean = categorize_roles(df_26sep)
        df_5oct_clean = categorize_roles(df_5oct)
        
        # Получаем категории для обеих дат
        sep_roles = df_26sep_clean.groupby('role_category')['salary_avg'].agg(['count', 'mean']).fillna(0)
        oct_roles = df_5oct_clean.groupby('role_category')['salary_avg'].agg(['count', 'mean']).fillna(0)
        
        # Объединяем все категории
        all_categories = set(sep_roles.index) | set(oct_roles.index)
        
        sep_counts = [sep_roles.loc[cat, 'count'] if cat in sep_roles.index else 0 for cat in all_categories]
        oct_counts = [oct_roles.loc[cat, 'count'] if cat in oct_roles.index else 0 for cat in all_categories]
        
        # График сравнения по категориям
        x = np.arange(len(all_categories))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(12, 6))
        bars1 = ax.bar(x - width/2, sep_counts, width, label='26 сентября', color='lightblue')
        bars2 = ax.bar(x + width/2, oct_counts, width, label='5 октября', color='lightcoral')
        
        ax.set_xlabel('Категории ролей')
        ax.set_ylabel('Количество вакансий')
        ax.set_title('📊 Сравнение количества вакансий по категориям\n26 сентября (24-26.09) vs 5 октября (3-5.10) 2025', 
                    fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(all_categories)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Добавляем значения на столбцы
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                           f'{int(height)}', ha='center', va='bottom', fontweight='bold', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(report_dir / 'dynamics_by_roles.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✅ Создан: dynamics_by_roles.png")

def create_dynamics_report(df_26sep, df_5oct, stats_26sep, stats_5oct, changes, report_dir):
    """Создаёт отчёт по динамике"""
    print("📋 Создаём отчёт по динамике...")
    
    excel_file = report_dir / 'dynamics_report.xlsx'
    
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # Сводная таблица сравнения
        comparison_data = {
            'Показатель': ['Всего вакансий', 'С зарплатой', 'Уникальных компаний', 
                          'Средняя зарплата', 'Медианная зарплата', 'Разброс (σ)', 
                          'Минимальная зарплата', 'Максимальная зарплата'],
            '26 сентября': [stats_26sep['total_vacancies'], stats_26sep['with_salary'], 
                           stats_26sep['unique_companies'], f"{stats_26sep['mean_salary']:,.0f} ₽",
                           f"{stats_26sep['median_salary']:,.0f} ₽", f"{stats_26sep['std_salary']:,.0f} ₽",
                           f"{stats_26sep['min_salary']:,.0f} ₽", f"{stats_26sep['max_salary']:,.0f} ₽"],
            '5 октября': [stats_5oct['total_vacancies'], stats_5oct['with_salary'], 
                         stats_5oct['unique_companies'], f"{stats_5oct['mean_salary']:,.0f} ₽",
                         f"{stats_5oct['median_salary']:,.0f} ₽", f"{stats_5oct['std_salary']:,.0f} ₽",
                         f"{stats_5oct['min_salary']:,.0f} ₽", f"{stats_5oct['max_salary']:,.0f} ₽"]
        }
        
        # Добавляем изменения
        change_values = []
        for key in ['total_vacancies', 'with_salary', 'unique_companies', 'mean_salary', 'median_salary', 
                   'std_salary', 'min_salary', 'max_salary']:
            if key in changes:
                change = changes[key]
                change_values.append(f"{change['change']:+,.0f} ({change['change_pct']:+.1f}%)")
            else:
                change_values.append("—")
        
        comparison_data['Изменение'] = change_values
        comparison_df = pd.DataFrame(comparison_data)
        comparison_df.to_excel(writer, sheet_name='Сравнение показателей', index=False)
        
        # Данные за 26 сентября
        if len(df_26sep) > 0:
            df_26sep_clean = categorize_roles(df_26sep)
            df_26sep_clean.to_excel(writer, sheet_name='Данные 26 сентября', index=False)
        
        # Данные за 5 октября
        if len(df_5oct) > 0:
            df_5oct_clean = categorize_roles(df_5oct)
            df_5oct_clean.to_excel(writer, sheet_name='Данные 5 октября', index=False)
    
    print(f"  ✅ Создан: {excel_file}")

def main():
    """Основная функция анализа динамики"""
    print("📈 АНАЛИЗ ДИНАМИКИ РЫНКА ТРУДА ВЛАДИВОСТОКА")
    print("26 сентября vs 5 октября 2025")
    print("=" * 60)
    
    try:
        # 1. Создаём папку для отчётов
        report_dir = setup_report_folder()
        
        # 2. Загружаем данные по датам
        df_26sep, df_5oct = load_data_by_date()
        
        if len(df_26sep) == 0 and len(df_5oct) == 0:
            print("❌ Нет данных для анализа!")
            return False
        
        # 3. Очищаем данные
        df_26sep = clean_salary_data(df_26sep, "26 сентября")
        df_5oct = clean_salary_data(df_5oct, "5 октября")
        
        # 4. Вычисляем сравнительную статистику
        stats_26sep, stats_5oct, changes = calculate_comparison_stats(df_26sep, df_5oct)
        
        # 5. Создаём визуализации динамики
        create_dynamics_visualizations(df_26sep, df_5oct, stats_26sep, stats_5oct, changes, report_dir)
        
        # 6. Создаём отчёт по динамике
        create_dynamics_report(df_26sep, df_5oct, stats_26sep, stats_5oct, changes, report_dir)
        
        print("\n🎉 АНАЛИЗ ДИНАМИКИ ЗАВЕРШЁН!")
        print(f"📁 Все файлы сохранены в папке: {report_dir.absolute()}")
        print("\n📊 Созданные файлы:")
        print("  • dynamics_comparison.png - Сравнение основных показателей")
        print("  • dynamics_by_roles.png - Сравнение по категориям ролей")
        print("  • dynamics_report.xlsx - Полный отчёт по динамике")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
