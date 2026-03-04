import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import json
import os
from typing import Dict, List, Tuple
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from sklearn.linear_model import LinearRegression
import requests
import warnings
warnings.filterwarnings('ignore')

class QuestAnalytics:
    def __init__(self, data_path='data/revenue.csv'):
        self.data_path = data_path
        self.df = self.load_data()
        
        # Координаты для Екатеринбурга
        self.latitude = 56.8389
        self.longitude = 60.6057
        self.timezone = "Asia/Yekaterinburg"
        self.city_name = "Екатеринбург"
        
        # База праздников
        self.holidays = self._init_holidays()
        
    def _init_holidays(self):
        """Инициализирует базу праздников"""
        return {
            '01-01': '🎄 Новый год',
            '01-02': '🎄 Новогодние каникулы',
            '01-03': '🎄 Новогодние каникулы',
            '01-04': '🎄 Новогодние каникулы',
            '01-05': '🎄 Новогодние каникулы',
            '01-06': '🎄 Новогодние каникулы',
            '01-07': '⛪ Рождество',
            '01-08': '🎄 Новогодние каникулы',
            '02-23': '🎖 День защитника',
            '03-08': '🌸 8 марта',
            '05-01': '💪 День труда',
            '05-09': '🎗 День Победы',
            '06-12': '🇷🇺 День России',
            '11-04': '🤝 Единство',
            '12-31': '🎅 Новый год'
        }
    
    def load_data(self):
        """Загружает или создает данные о выручке"""
        try:
            if os.path.exists(self.data_path):
                df = pd.read_csv(self.data_path)
                if len(df) > 0:
                    df['date'] = pd.to_datetime(df['date'])
                    df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce').fillna(0)
                    print(f"Загружено {len(df)} записей из {self.data_path}")
                    return df
                else:
                    print("Файл пуст, создаем новые данные")
                    return self._create_initial_data()
            else:
                print("Файл не найден, создаем новые данные")
                return self._create_initial_data()
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return self._create_initial_data()
    
    def _create_initial_data(self):
        """Создает начальные данные (180 дней для статистики)"""
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=180)  # 6 месяцев данных
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        data = []
        for date in dates:
            # Базовый тренд (рост бизнеса)
            days_from_start = (date - dates[0]).days
            base = 15000 + days_from_start * 20  # Рост 20₽ в день
            
            # День недели (выходные выше)
            day_of_week = date.dayofweek
            if day_of_week >= 4:  # пятница, суббота
                base *= 1.3
            elif day_of_week == 3:  # четверг
                base *= 1.1
            
            # Праздники
            date_key = date.strftime('%m-%d')
            if date_key in self.holidays:
                base *= 1.5
            
            # Случайные колебания
            revenue = int(base * np.random.uniform(0.85, 1.15))
            
            data.append({
                'date': date,
                'revenue': revenue
            })
        
        df = pd.DataFrame(data)
        df.to_csv(self.data_path, index=False)
        print(f"Созданы начальные данные: {len(df)} записей")
        return df
    
    def add_revenue(self, date: str, revenue: float):
        """Добавляет или обновляет выручку за конкретный день"""
        try:
            date = pd.to_datetime(date)
            revenue = float(revenue)
            
            # Проверяем существующую запись
            mask = self.df['date'] == date
            if mask.any():
                # Обновляем существующую запись
                idx = self.df[mask].index[0]
                self.df.at[idx, 'revenue'] = revenue
                print(f"Обновлена выручка за {date.strftime('%Y-%m-%d')}: {revenue} ₽")
            else:
                # Добавляем новую запись
                new_row = pd.DataFrame({
                    'date': [date],
                    'revenue': [revenue]
                })
                self.df = pd.concat([self.df, new_row], ignore_index=True)
                print(f"Добавлена выручка за {date.strftime('%Y-%m-%d')}: {revenue} ₽")
            
            # Сортируем по дате и сохраняем
            self.df = self.df.sort_values('date').reset_index(drop=True)
            self.df.to_csv(self.data_path, index=False)
            
            return self.get_stats()
            
        except Exception as e:
            print(f"Ошибка при добавлении данных: {e}")
            raise
    
    def get_stats(self):
        """Возвращает основную статистику"""
        if self.df.empty:
            return {
                'total_revenue': 0,
                'avg_daily': 0,
                'max_daily': 0,
                'min_daily': 0,
                'revenue_last_30': 0,
                'trend_percent': 0,
                'total_days': 0,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'date_start': 'Нет данных',
                'date_end': 'Нет данных'
            }
        
        total_revenue = int(self.df['revenue'].sum())
        avg_daily = int(self.df['revenue'].mean())
        max_daily = int(self.df['revenue'].max())
        min_daily = int(self.df['revenue'].min())
        
        last_30 = self.df.tail(30)
        revenue_last_30 = int(last_30['revenue'].sum()) if not last_30.empty else 0
        
        # Тренд за последние 30 дней
        if len(last_30) >= 14:
            week1 = last_30.head(7)['revenue'].mean()
            week4 = last_30.tail(7)['revenue'].mean()
            trend_percent = ((week4 - week1) / week1 * 100) if week1 > 0 else 0
        else:
            trend_percent = 0
        
        stats = {
            'total_revenue': total_revenue,
            'avg_daily': avg_daily,
            'max_daily': max_daily,
            'min_daily': min_daily,
            'revenue_last_30': revenue_last_30,
            'trend_percent': round(trend_percent, 1),
            'total_days': len(self.df),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'date_start': self.df['date'].min().strftime('%Y-%m-%d') if not self.df.empty else 'Нет данных',
            'date_end': self.df['date'].max().strftime('%Y-%m-%d') if not self.df.empty else 'Нет данных'
        }
        
        return stats
    
    def get_day_stats(self, day_short=None):
        """Возвращает статистику по дням недели"""
        if self.df.empty:
            return {} if day_short else []
        
        df = self.df.copy()
        df['day_num'] = df['date'].dt.dayofweek
        df['day'] = df['date'].dt.day_name().map({
            'Monday': 'Пн', 'Tuesday': 'Вт', 'Wednesday': 'Ср',
            'Thursday': 'Чт', 'Friday': 'Пт', 'Saturday': 'Сб', 'Sunday': 'Вс'
        })
        
        # Если запрошен конкретный день
        if day_short:
            day_data = df[df['day'] == day_short]
            if not day_data.empty:
                return {
                    'day': day_short,
                    'avg': int(day_data['revenue'].mean()),
                    'count': len(day_data),
                    'total': int(day_data['revenue'].sum()),
                    'min': int(day_data['revenue'].min()),
                    'max': int(day_data['revenue'].max())
                }
            else:
                return {'error': f'Нет данных за {day_short}'}
        
        # Статистика по всем дням
        stats = []
        day_order = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        
        for day in day_order:
            day_data = df[df['day'] == day]
            if not day_data.empty:
                stats.append({
                    'day': day,
                    'avg': int(day_data['revenue'].mean()),
                    'count': len(day_data),
                    'total': int(day_data['revenue'].sum())
                })
            else:
                stats.append({
                    'day': day,
                    'avg': 0,
                    'count': 0,
                    'total': 0
                })
        
        return stats
    
    def get_weather(self, target_date):
        """Получает прогноз погоды для Екатеринбурга"""
        try:
            params = {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "daily": ["temperature_2m_max", "temperature_2m_min", "weathercode"],
                "timezone": self.timezone,
                "forecast_days": 16
            }
            
            response = requests.get(
                "https://api.open-meteo.com/v1/forecast", 
                params=params, 
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                date_str = target_date.strftime('%Y-%m-%d')
                
                for i, forecast_date in enumerate(data['daily']['time']):
                    if forecast_date == date_str:
                        code = data['daily']['weathercode'][i]
                        return {
                            'success': True,
                            'temp_max': data['daily']['temperature_2m_max'][i],
                            'temp_min': data['daily']['temperature_2m_min'][i],
                            'code': code,
                            'description': self._get_weather_desc(code)
                        }
            return {'success': False}
        except Exception as e:
            print(f"Ошибка получения погоды: {e}")
            return {'success': False}
    
    def _get_weather_desc(self, code):
        """Описание погоды по коду"""
        weather_map = {
            0: '☀️ Ясно',
            1: '🌤 Малооблачно',
            2: '⛅ Переменная облачность',
            3: '☁️ Пасмурно',
            45: '🌫 Туман',
            48: '🌫 Иней',
            51: '🌧 Легкая морось',
            53: '🌧 Морось',
            55: '🌧 Сильная морось',
            61: '🌧 Небольшой дождь',
            63: '🌧 Дождь',
            65: '🌧 Сильный дождь',
            71: '🌨 Небольшой снег',
            73: '🌨 Снег',
            75: '🌨 Сильный снег',
            77: '🌨 Снежная крупа',
            80: '🌧 Ливень',
            81: '🌧 Сильный ливень',
            82: '🌧 Шквал',
            85: '🌨 Снегопад',
            86: '🌨 Сильный снегопад',
            95: '⛈ Гроза',
            96: '⛈ Гроза с градом',
            99: '⛈ Сильная гроза'
        }
        return weather_map.get(code, '☁️ Облачно')
    
    def get_holiday(self, target_date):
        """Проверяет, есть ли праздник в указанную дату"""
        date_key = target_date.strftime('%m-%d')
        return self.holidays.get(date_key)
    
    def predict_specific_days(self, day_name, count=4):
        """Прогнозирует выручку для конкретных дней (например, ближайшие 4 понедельника)"""
        days_map = {
            'понедельник': 0, 'пн': 0,
            'вторник': 1, 'вт': 1,
            'среда': 2, 'ср': 2,
            'четверг': 3, 'чт': 3,
            'пятница': 4, 'пт': 4,
            'суббота': 5, 'сб': 5,
            'воскресенье': 6, 'вс': 6
        }
        
        day_num = days_map.get(day_name.lower(), 0)
        today = datetime.now().date()
        
        # Находим ближайший целевой день
        days_ahead = day_num - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        
        predictions = []
        
        for i in range(count):
            target_date = today + timedelta(days=days_ahead + i*7)
            
            # Базовый прогноз на основе исторических данных
            base_prediction = self._get_base_prediction(target_date)
            
            # Учитываем праздники
            holiday = self.get_holiday(target_date)
            holiday_factor = 1.4 if holiday else 1.0
            
            # Учитываем погоду
            weather = self.get_weather(target_date)
            weather_factor = 1.0
            weather_desc = None
            temp_range = None
            
            if weather.get('success'):
                weather_desc = weather['description']
                temp_range = f"{weather['temp_min']:.0f}°..{weather['temp_max']:.0f}°"
                
                if 'дождь' in weather_desc.lower() or 'снег' in weather_desc.lower():
                    weather_factor = 0.85  # -15% в плохую погоду
                elif 'ясно' in weather_desc.lower():
                    weather_factor = 1.1   # +10% в хорошую погоду
                
                if weather['temp_max'] < -15:
                    weather_factor *= 0.8   # -20% в сильный мороз
                elif weather['temp_max'] > 25:
                    weather_factor *= 1.05  # +5% в жару
            
            # Учитываем день недели
            day_factor = 1.2 if target_date.weekday() >= 4 else 1.0  # выходные выше
            
            final_prediction = int(base_prediction * holiday_factor * weather_factor * day_factor)
            
            # Определяем уверенность прогноза
            confidence = 'Средний'
            if i < 2 and weather.get('success'):
                confidence = 'Высокий'
            elif i > 3:
                confidence = 'Низкий'
            
            # Полное название дня
            day_names = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 
                        'Пятница', 'Суббота', 'Воскресенье']
            
            predictions.append({
                'date': target_date.strftime('%Y-%m-%d'),
                'day_name': day_names[target_date.weekday()],
                'predicted_revenue': final_prediction,
                'holiday': holiday,
                'weather': weather_desc,
                'temperature': temp_range,
                'confidence': confidence
            })
        
        return predictions
    
    def _get_base_prediction(self, target_date):
        """Базовый прогноз на основе исторических данных"""
        if len(self.df) < 10:
            return 20000  # Значение по умолчанию
        
        # Ищем похожие даты (тот же месяц, день недели)
        similar_dates = self.df[
            (self.df['date'].dt.month == target_date.month) &
            (self.df['date'].dt.dayofweek == target_date.weekday())
        ]
        
        if len(similar_dates) > 0:
            return int(similar_dates['revenue'].mean())
        
        # Если нет похожих, используем среднее по дню недели
        same_weekday = self.df[self.df['date'].dt.dayofweek == target_date.weekday()]
        if len(same_weekday) > 0:
            return int(same_weekday['revenue'].mean())
        
        return 20000
    
    def generate_revenue_chart(self, days=30):
        """Генерирует график динамики выручки"""
        if self.df.empty:
            return None
        
        # Берем последние N дней или все если days=0
        if days > 0:
            df_plot = self.df.tail(days).copy()
        else:
            df_plot = self.df.copy()
        
        plt.figure(figsize=(12, 6))
        plt.plot(df_plot['date'], df_plot['revenue'], 
                marker='o', linestyle='-', linewidth=2, markersize=4, color='#2563eb')
        plt.fill_between(df_plot['date'], df_plot['revenue'], 
                        alpha=0.1, color='#2563eb')
        
        # Добавляем среднюю линию
        avg_revenue = df_plot['revenue'].mean()
        plt.axhline(y=avg_revenue, color='#f59e0b', linestyle='--', 
                   alpha=0.7, label=f'Средняя: {avg_revenue:,.0f} ₽')
        
        period_text = f"последние {days} дней" if days > 0 else "за все время"
        plt.title(f'Динамика выручки {period_text}', fontsize=14, fontweight='bold')
        plt.xlabel('Дата')
        plt.ylabel('Выручка (₽)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Форматирование дат
        if len(df_plot) > 10:
            plt.xticks(rotation=45, ha='right')
        else:
            plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # Сохраняем в base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        
        return image_base64
    
    def generate_day_comparison_chart(self):
        """Генерирует график сравнения дней недели"""
        if self.df.empty:
            return None
        
        df = self.df.copy()
        df['day_num'] = df['date'].dt.dayofweek
        df['day_name'] = df['date'].dt.day_name().map({
            'Monday': 'Пн', 'Tuesday': 'Вт', 'Wednesday': 'Ср',
            'Thursday': 'Чт', 'Friday': 'Пт', 'Saturday': 'Сб', 'Sunday': 'Вс'
        })
        
        # Группируем по дням
        day_stats = df.groupby('day_name')['revenue'].agg(['mean', 'std', 'count']).reset_index()
        
        # Сортируем по дню недели
        day_order = {'Пн': 0, 'Вт': 1, 'Ср': 2, 'Чт': 3, 'Пт': 4, 'Сб': 5, 'Вс': 6}
        day_stats['order'] = day_stats['day_name'].map(day_order)
        day_stats = day_stats.sort_values('order')
        
        plt.figure(figsize=(10, 6))
        
        # Столбцы с погрешностью
        bars = plt.bar(day_stats['day_name'], day_stats['mean'], 
                      yerr=day_stats['std'], capsize=5, alpha=0.8,
                      color=['#3b82f6', '#3b82f6', '#3b82f6', '#3b82f6', 
                             '#f59e0b', '#f59e0b', '#f59e0b'])
        
        plt.title('Средняя выручка по дням недели', fontsize=14, fontweight='bold')
        plt.xlabel('День недели')
        plt.ylabel('Средняя выручка (₽)')
        plt.grid(True, alpha=0.3, axis='y')
        
        # Добавляем значения над столбцами
        for i, (_, row) in enumerate(day_stats.iterrows()):
            if row['count'] > 0:
                plt.text(i, row['mean'] + row['std'] + 500, 
                        f"{int(row['mean']):,} ₽", 
                        ha='center', va='bottom', fontsize=9)
        
        # Добавляем количество дней
        for i, (_, row) in enumerate(day_stats.iterrows()):
            plt.text(i, 1000, f"n={row['count']}", 
                    ha='center', va='bottom', fontsize=8, color='#64748b')
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        
        return image_base64