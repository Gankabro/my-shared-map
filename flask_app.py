from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import uuid
from datetime import datetime
import pytz

# --- הגדרות האפליקציה ---
app = Flask(__name__)
CORS(app) 

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "YAMARHAZAK")

# --- מסד נתונים ---
pins_database = { "red": [], "orange": [], "purple": [], "brown": [] }
drawings_database = { "red": [], "orange": [], "purple": [], "brown": [] }
route_legends = { "red": "מסלול אדום", "orange": "מסלול כתום", "purple": "מסלול סגול", "brown": "מסלול חום" }

# --- נתיבים (Routes) ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/verify_password', methods=['POST'])
def verify_password():
    data = request.get_json()
    if data and data.get('password') == ADMIN_PASSWORD:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Incorrect password'}), 401

@app.route('/add_pin', methods=['POST'])
def add_pin():
    data = request.get_json()
    if data.get('password') != ADMIN_PASSWORD: 
        return jsonify({'status': 'error', 'message': 'Authentication failed'}), 403
    color = data.get('color')
    if color not in pins_database: 
        return jsonify({'status': 'error', 'message': 'Invalid color'}), 400
    
    israel_tz = pytz.timezone("Asia/Jerusalem") 
    now_israel = datetime.now(israel_tz)

    new_pin = { 
        'id': str(uuid.uuid4()), 
        'lat': data['lat'], 
        'lng': data['lng'], 
        'text': data.get('text', ''), 
        'timestamp': now_israel.isoformat(),
        'radius': data.get('radius', 0)
    }
    pins_database[color].append(new_pin)
    return jsonify({'status': 'success'}), 201

@app.route('/delete_pin', methods=['POST'])
def delete_pin():
    data = request.get_json()
    if data.get('password') != ADMIN_PASSWORD: 
        return jsonify({'status': 'error', 'message': 'Authentication failed'}), 403
    pin_id_to_delete = data.get('id')
    for color in pins_database:
        initial_length = len(pins_database[color])
        pins_database[color] = [pin for pin in pins_database[color] if pin['id'] != pin_id_to_delete]
        if len(pins_database[color]) < initial_length:
            return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Pin not found'}), 404

@app.route('/update_legend', methods=['POST'])
def update_legend():
    data = request.get_json()
    if data.get('password') != ADMIN_PASSWORD: 
        return jsonify({'status': 'error', 'message': 'Authentication failed'}), 403
    color, text = data.get('color'), data.get('text')
    if color not in route_legends: 
        return jsonify({'status': 'error', 'message': 'Invalid color'}), 400
    route_legends[color] = text
    return jsonify({'status': 'success'})

@app.route('/update_radius', methods=['POST'])
def update_radius():
    data = request.get_json()
    if data.get('password') != ADMIN_PASSWORD: 
        return jsonify({'status': 'error', 'message': 'Authentication failed'}), 403
    pin_id, new_radius = data.get('id'), data.get('radius')
    if not pin_id or new_radius is None: 
        return jsonify({'status': 'error', 'message': 'Missing data'}), 400
    for color in pins_database:
        for pin in pins_database[color]:
            if pin['id'] == pin_id:
                pin['radius'] = new_radius
                return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Pin not found'}), 404

@app.route('/add_drawing', methods=['POST'])
def add_drawing():
    data = request.get_json()
    if data.get('password') != ADMIN_PASSWORD:
        return jsonify({'status': 'error', 'message': 'Authentication failed'}), 403
    
    color = data.get('color')
    if color not in drawings_database:
        return jsonify({'status': 'error', 'message': 'Invalid color'}), 400
    
    israel_tz = pytz.timezone("Asia/Jerusalem")
    now_israel = datetime.now(israel_tz)
    
    new_drawing = {
        'id': str(uuid.uuid4()),
        'type': data.get('type'),  # 'freehand', 'polygon', 'rectangle', 'circle'
        'data': data.get('data'),
        'timestamp': now_israel.isoformat()
    }
    
    drawings_database[color].append(new_drawing)
    return jsonify({'status': 'success', 'id': new_drawing['id']}), 201

@app.route('/delete_drawing', methods=['POST'])
def delete_drawing():
    data = request.get_json()
    if data.get('password') != ADMIN_PASSWORD:
        return jsonify({'status': 'error', 'message': 'Authentication failed'}), 403
    
    drawing_id_to_delete = data.get('id')
    for color in drawings_database:
        initial_length = len(drawings_database[color])
        drawings_database[color] = [drawing for drawing in drawings_database[color] if drawing['id'] != drawing_id_to_delete]
        if len(drawings_database[color]) < initial_length:
            return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error', 'message': 'Drawing not found'}), 404

@app.route('/get_data', methods=['GET'])
def get_data():
    sorted_pins = {color: sorted(pins, key=lambda p: p['timestamp']) for color, pins in pins_database.items()}
    sorted_drawings = {color: sorted(drawings, key=lambda d: d['timestamp']) for color, drawings in drawings_database.items()}
    return jsonify({ 
        "routes": sorted_pins, 
        "legends": route_legends,
        "drawings": sorted_drawings
    })