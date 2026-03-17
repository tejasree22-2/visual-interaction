import hashlib
from flask import Blueprint, request, jsonify

from services.cache_service import get_cached_result, set_cached_result
from services.physics_service import calculate_trajectory
from services.supabase_client import store_simulation
from services.speech_service import generate_explanation_text, synthesize_speech

simulation_bp = Blueprint('simulation', __name__)


def _generate_cache_key(angle, velocity, gravity):
    key_str = f"{angle}:{velocity}:{gravity}"
    return f"simulation:{hashlib.md5(key_str.encode()).hexdigest()}"


@simulation_bp.route('/simulate', methods=['POST'])
def simulate():
    data = request.get_json()
    
    angle = data.get('angle')
    velocity = data.get('velocity')
    gravity = data.get('gravity')
    
    cache_key = _generate_cache_key(angle, velocity, gravity)
    
    cached_result = get_cached_result(cache_key)
    if cached_result:
        physics_result = cached_result
    else:
        physics_result = calculate_trajectory(angle, velocity, gravity)
        set_cached_result(cache_key, physics_result)
    
    store_simulation(angle, velocity, gravity)
    
    explanation_text = generate_explanation_text(angle, velocity, gravity)
    speech_result = synthesize_speech(explanation_text)
    
    return jsonify({
        'trajectory': physics_result['trajectory'],
        'max_height': physics_result['max_height'],
        'range': physics_result['range'],
        'time_of_flight': physics_result['time_of_flight'],
        'explanation_text': explanation_text,
        'speech_audio_url': speech_result.get('audio_url')
    })
