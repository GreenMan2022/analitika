import json
import os
from datetime import datetime, timedelta, date
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import requests
import warnings
warnings.filterwarnings('ignore')

class QuestAnalytics:
    def __init__(self, data_path='data/revenue.json'):
        self.data_path = data_path
        self.data = self.load_data()
        
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
        """Загружает данные из JSON"""
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"Загружено {len(data)} записей")
                return data
            else:
                print("Файл не найден, создаем новые данные")
                return self._create_initial_data()
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return self._create_initial_data()
    
    def _create_initial_data(self):
        """Создает начальные данные (180 дней)"""
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=180)
        
        data = []
        for i in range(180):
            current_date = start_date + timedelta(days=i)
            
            # Базовый тренд
            base = 15000 + i * 20
            
            # День недели
            day_of_week = current_date.weekday()
            if day_of_week >= 4:  # выходные
                base = int(base * 1.3)
            
            # Праздники
            date_key = current_date.strftime('%m-%d')
            if date_key in self.holidays:
                base = int(base * 1.5)
            
            # Случайность
            import random
            revenue = int(base * random.uniform(0.85, 1.15))
            
            data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'revenue': revenue
            })
        
        self._save_data(data)
        print(f"Создано {len(data)} записей")
        return data
    
    def _save_data(self, data=None):
        """Сохраняет данные в JSON"""
        if data is None:
            data = self.data
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_revenue(self, date_str: str, revenue: float):
        """Добавляет или обновляет выручку"""
        try:
            # Проверяем существующую запись
            found = False
            for i, record in enumerate(self.data):
                if record['date'] == date_str:
                    self.data[i]['revenue'] = revenue
                    found = True
                    print(f"Обновлена запись за {date_str}: {revenue} ₽")
                    break
            
            if not found:
                self.data.append({
                    'date': date_str,
                    'revenue': revenue
                })
                print(f"Добавлена запись за {date_str}: {revenue} ₽")
            
            # Сортируем по дате
            self.data.sort(key=lambda x: x['date'])
            self._save_data()
            
            return self.get_stats()
            
        except Exception as e:
            print(f"Ошибка: {e}")
            raise
    
    def get_stats(self):
        """Возвращает основную статистику"""
        if not self.data:
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
        
        revenues = [r['revenue'] for r in self.data]
        total_revenue = sum(revenues)
        avg_daily = int(total_revenue / len(revenues))
        max_daily = max(revenues)
        min_daily = min(revenues)
        
        # Последние 30 дней
        last_30 = self.data[-30:] if len(self.data) >= 30 else self.data
        revenue_last_30 = sum(r['revenue'] for r in last_30)
        
        # Тренд
        trend_percent = 0
        if len(self.data) >= 14:
            week1 = sum(r['revenue'] for r in self.data[-14:-7]) / 7
            week2 = sum(r['revenue'] for r in self.data[-7:]) / 7
            if week1 > 0:
                trend_percent = ((week2 - week1) / week1 * 100)
        
        return {
            'total_revenue': total_revenue,
            'avg_daily': avg_daily,
            'max_daily': max_daily,
            'min_daily': min_daily,
            'revenue_last_30': revenue_last_30,
            'trend_percent': round(trend_percent, 1),
            'total_days': len(self.data),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'date_start': self.data[0]['date'],
            'date_end': self.data[-1]['date']
        }
    
    def get_day_stats(self, day_short=None):
        """Статистика по дням недели"""
        if not self.data:
            return {} if day_short else []
        
        # Словарь для сбора данных по дням
        day_stats = defaultdict(lambda: {'sum': 0, 'count': 0})
        day_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        
        for record in self.data:
            d = datetime.strptime(record['date'], '%Y-%m-%d')
            day_num = d.weekday()
            day_name = day_names[day_num]
            
            day_stats[day_name]['sum'] += record['revenue']
            day_stats[day_name]['count'] += 1
        
        if day_short:
            if day_short in day_stats and day_stats[day_short]['count'] > 0:
                stats = day_stats[day_short]
                return {
                    'day': day_short,
                    'avg': int(stats['sum'] / stats['count']),
                    'count': stats['count'],
                    'total': int(stats['sum'])
                }
            return {'error': f'Нет данных за {day_short}'}
        
        # Все дни
        result = []
        for day in day_names:
            if day in day_stats:
                stats = day_stats[day]
                result.append({
                    'day': day,
                    'avg': int(stats['sum'] / stats['count']),
                    'count': stats['count'],
                    'total': int(stats['sum'])
                })
            else:
                result.append({'day': day, 'avg': 0, 'count': 0, 'total': 0})
        
        return result
    
    def get_recent(self, limit=10):
        """Последние записи"""
        recent = self.data[-limit:][::-1]  # последние, в обратном порядке
        return [{'date': r['date'], 'revenue': r['revenue']} for r in recent]
    
    def get_weather(self, target_date):
        """Получает прогноз погоды"""
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
            print(f"Ошибка погоды: {e}")
            return {'success': False}
    
    def _get_weather_desc(self, code):
        """Описание погоды"""
        weather_map = {
            0: '☀️ Ясно', 1: '🌤 Малооблачно', 2: '⛅ Облачно',
            3: '☁️ Пасмурно', 45: '🌫 Туман', 48: '🌫 Иней',
            51: '🌧 Морось', 61: '🌧 Дождь', 71: '🌨 Снег',
            95: '⛈ Гроза'
        }
        return weather_map.get(code, '☁️ Облачно')
    
    def get_holiday(self, target_date):
        """Проверяет праздник"""
        date_key = target_date.strftime('%m-%d')
        return self.holidays.get(date_key)
    
    def predict_specific_days(self, day_name, count=4):
        """Прогноз на будущие даты"""
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
        
        days_ahead = day_num - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        
        predictions = []
        day_names = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 
                    'Пятница', 'Суббота', 'Воскресенье']
        
        # Собираем исторические средние по дням
        day_averages = {}
        for record in self.data:
            d = datetime.strptime(record['date'], '%Y-%m-%d')
            wd = d.weekday()
            if wd not in day_averages:
                day_averages[wd] = []
            day_averages[wd].append(record['revenue'])
        
        for i in range(count):
            target_date = today + timedelta(days=days_ahead + i*7)
            wd = target_date.weekday()
            
            # Базовое предсказание
            if wd in day_averages and day_averages[wd]:
                base_prediction = sum(day_averages[wd]) / len(day_averages[wd])
            else:
                base_prediction = 20000
            
            # Факторы
            holiday = self.get_holiday(target_date)
            weather = self.get_weather(target_date)
            
            # Корректировки
            holiday_factor = 1.4 if holiday else 1.0
            weather_factor = 1.0
            
            if weather.get('success'):
                if 'дождь' in weather['description'].lower() or 'снег' in weather['description'].lower():
                    weather_factor = 0.85
                elif 'ясно' in weather['description'].lower():
                    weather_factor = 1.1
                
                if weather['temp_max'] < -15:
                    weather_factor *= 0.8
                elif weather['temp_max'] > 25:
                    weather_factor *= 1.05
            
            day_factor = 1.2 if wd >= 4 else 1.0
            
            final_prediction = int(base_prediction * holiday_factor * weather_factor * day_factor)
            
            # Уверенность
            confidence = 'Средний'
            if i < 2 and weather.get('success'):
                confidence = 'Высокий'
            elif i > 3:
                confidence = 'Низкий'
            
            predictions.append({
                'date': target_date.strftime('%Y-%m-%d'),
                'day_name': day_names[wd],
                'predicted_revenue': final_prediction,
                'holiday': holiday,
                'weather': weather.get('description') if weather.get('success') else None,
                'temperature': f"{weather.get('temp_min', '?')}°..{weather.get('temp_max', '?')}°" if weather.get('success') else None,
                'confidence': confidence
            })
        
        return predictions
    
    def generate_revenue_chart(self, days=30):
        """Генерирует график динамики"""
        if not self.data:
            return None
        
        data_slice = self.data[-days:] if days > 0 else self.data
        
        dates = [d['date'] for d in data_slice]
        revenues = [d['revenue'] for d in data_slice]
        
        plt.figure(figsize=(12, 6))
        plt.plot(dates, revenues, marker='o', linestyle='-', linewidth=2, 
                markersize=4, color='#2563eb')
        plt.fill_between(dates, revenues, alpha=0.1, color='#2563eb')
        
        avg_revenue = sum(revenues) / len(revenues)
        plt.axhline(y=avg_revenue, color='#f59e0b', linestyle='--', 
                   alpha=0.7, label=f'Средняя: {avg_revenue:,.0f} ₽')
        
        period = f"последние {days} дней" if days > 0 else "за все время"
        plt.title(f'Динамика выручки {period}', fontsize=14, fontweight='bold')
        plt.xlabel('Дата')
        plt.ylabel('Выручка (₽)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        
        return image_base64
    
    def generate_day_comparison_chart(self):
        """Генерирует график сравнения дней"""
        if not self.data:
            return None
        
        day_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        day_data = defaultdict(list)
        
        for record in self.data:
            d = datetime.strptime(record['date'], '%Y-%m-%d')
            day_data[day_names[d.weekday()]].append(record['revenue'])
        
        days = []
        means = []
        errors = []
        
        for day in day_names:
            if day_data[day]:
                days.append(day)
                means.append(sum(day_data[day]) / len(day_data[day]))
                errors.append(np.std(day_data[day]) if len(day_data[day]) > 1 else 0)
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(days, means, yerr=errors, capsize=5, alpha=0.8,
                      color=['#3b82f6']*4 + ['#f59e0b']*3)
        
        plt.title('Средняя выручка по дням недели', fontsize=14, fontweight='bold')
        plt.xlabel('День недели')
        plt.ylabel('Средняя выручка (₽)')
        plt.grid(True, alpha=0.3, axis='y')
        
        for i, (day, mean) in enumerate(zip(days, means)):
            plt.text(i, mean + (errors[i] if errors else 0) + 500, 
                    f"{int(mean):,} ₽", ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        
        return image_base64
