from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import time
import os
from analytics_no_pandas import QuestAnalytics

app = Flask(__name__)
CORS(app)

API_KEY = os.environ.get('API_KEY', 'apf_i6fhd1fenfma3zg2ceoaa5y5')
API_URL = "https://apifreellm.com/api/v1/chat"

analytics = QuestAnalytics()

last_request_time = 0
RATE_LIMIT_SECONDS = 25

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    global last_request_time
    
    data = request.get_json()
    user_message = data.get('message')
    
    if not user_message:
        return jsonify({"error": "Сообщение отсутствует"}), 400
    
    stats = analytics.get_stats()
    
    context = f"""Ты - ИИ-помощник квест-комнаты в Екатеринбурге.

💰 ТЕКУЩАЯ СТАТИСТИКА:
• Всего выручка: {stats['total_revenue']:,} ₽
• Средняя в день: {stats['avg_daily']:,} ₽
• За 30 дней: {stats['revenue_last_30']:,} ₽

Ответь на вопрос: {user_message}"""
    
    now = time.time()
    if now - last_request_time < RATE_LIMIT_SECONDS:
        remaining = RATE_LIMIT_SECONDS - (now - last_request_time)
        return jsonify({"error": f"Подожди {int(remaining)+1} сек"}), 429
    
    try:
        response = requests.post(
            API_URL,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
            json={"message": context},
            timeout=90
        )
        
        data = response.json()
        if data.get("success"):
            last_request_time = time.time()
            return jsonify({"response": data["response"]})
        else:
            return jsonify({"error": "Ошибка API"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        stats = analytics.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recent', methods=['GET'])
def get_recent():
    try:
        recent = analytics.get_recent(10)
        return jsonify(recent)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/add_revenue', methods=['POST'])
def add_revenue():
    try:
        data = request.get_json()
        
        if not data or not data.get('date') or not data.get('revenue'):
            return jsonify({"error": "Дата и выручка обязательны"}), 400
        
        stats = analytics.add_revenue(data['date'], data['revenue'])
        return jsonify({"success": True, "stats": stats})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/day_stats', methods=['GET'])
def day_stats():
    try:
        day = request.args.get('day')
        stats = analytics.get_day_stats(day)
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/predict_day', methods=['GET'])
def predict_day():
    try:
        day = request.args.get('day', 'понедельник')
        count = request.args.get('count', 4, type=int)
        
        predictions = analytics.predict_specific_days(day, count)
        return jsonify(predictions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/charts/revenue', methods=['GET'])
def get_revenue_chart():
    try:
        days = request.args.get('days', 30, type=int)
        chart = analytics.generate_revenue_chart(days)
        return jsonify({"chart": chart})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/charts/day_comparison', methods=['GET'])
def get_day_comparison_chart():
    try:
        chart = analytics.generate_day_comparison_chart()
        return jsonify({"chart": chart})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
