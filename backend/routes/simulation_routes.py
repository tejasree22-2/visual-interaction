from flask import Blueprint, request, jsonify

simulation_bp = Blueprint('simulation', __name__)

@simulation_bp.route('/simulate', methods=['POST'])
def simulate():
    data = request.get_json()
    
    angle = data.get('angle')
    velocity = data.get('velocity')
    gravity = data.get('gravity')
    
    return jsonify({
        'message': 'Placeholder response - physics not implemented',
        'received': {
            'angle': angle,
            'velocity': velocity,
            'gravity': gravity
        }
    })
