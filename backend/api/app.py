# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import numpy as np
from datetime import datetime
import redis
import psycopg2
# from behavioral_analyzer import BehavioralAnalyzer

app = Flask(__name__)
CORS(app)

# Database connections
redis_client = redis.Redis(host='localhost', port=6379, db=0)
# analyzer = BehavioralAnalyzer()

@app.route('/api/behavioral-data', methods=['POST'])
def receive_behavioral_data():
    try:
        data = request.json
        session_id = data['sessionId']
        keystroke_data = data['keystrokeData']
        mouse_data = data['mouseData']
        
        # Store in Redis for real-time processing
        redis_client.setex(f"session:{session_id}", 3600, json.dumps(data))
        
        # Process for real-time analysis
        # risk_score = analyzer.analyze_real_time(keystroke_data, mouse_data)
        risk_score = 0.5 # Placeholder
        
        # Store in PostgreSQL for long-term analysis
        store_behavioral_data(session_id, keystroke_data, mouse_data)
        
        response = {
            'status': 'success',
            'riskScore': risk_score,
            'timestamp': datetime.now().isoformat()
        }
        
        # Alert if high risk
        if risk_score > 0.7:
            response['alert'] = 'HIGH_RISK_DETECTED'
            
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def store_behavioral_data(session_id, keystroke_data, mouse_data):
    """Store behavioral data in PostgreSQL"""
    conn = psycopg2.connect(
        host="localhost",
        database="behavioral_auth",
        user="postgres",
        password="password"
    )
    
    cursor = conn.cursor()
    
    # Store keystroke data
    for keystroke in keystroke_data:
        cursor.execute("""
            INSERT INTO keystroke_data (session_id, key_code, timestamp, dwell_time, event_type)
            VALUES (%s, %s, %s, %s, %s)
        """, (session_id, keystroke.get('keyCode'), keystroke.get('timestamp'),
              keystroke.get('dwellTime'), keystroke.get('type')))
    
    # Store mouse data
    for mouse_event in mouse_data:
        cursor.execute("""
            INSERT INTO mouse_data (session_id, x, y, timestamp, event_type)
            VALUES (%s, %s, %s, %s, %s)
        """, (session_id, mouse_event.get('x'), mouse_event.get('y'),
              mouse_event.get('timestamp'), mouse_event.get('type')))
    
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)