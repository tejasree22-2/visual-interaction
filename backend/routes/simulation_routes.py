import hashlib
import logging
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

from services.cache_service import get_cached_result, set_cached_result
from services.physics_service import calculate_trajectory
from services.supabase_client import store_simulation
from services.speech_service import generate_explanation_text, synthesize_speech

simulation_bp = Blueprint('simulation', __name__)


def _generate_cache_key(angle, velocity, gravity, custom_formula=None):
    key_str = f"{angle}:{velocity}:{gravity}:{custom_formula or ''}"
    return f"simulation:{hashlib.md5(key_str.encode()).hexdigest()}"


@simulation_bp.route('/simulation', methods=['POST'])
@simulation_bp.route('/simulate', methods=['POST'])
def simulate():
    data = request.get_json() or {}
    
    text = data.get('text')
    if text:
        speech_result = synthesize_speech(text)
        return jsonify({
            'speech_audio_url': speech_result.get('audio_url'),
            'error': speech_result.get('error')
        })
    
    angle = data.get('angle')
    velocity = data.get('velocity')
    gravity = data.get('gravity')
    custom_formula = data.get('custom_formula')
    include_formula = data.get('include_formula', False)
    
    print(f"\n=== Slider Changed ===")
    print(f"angle: {angle}, velocity: {velocity}, gravity: {gravity}")
    print(f"custom_formula: {custom_formula}, include_formula: {include_formula}")
    logger.info(f"Slider Changed: angle={angle}, velocity={velocity}, gravity={gravity}, custom_formula={custom_formula}")
    
    cache_key = _generate_cache_key(angle, velocity, gravity, custom_formula)
    
    cached_result = get_cached_result(cache_key)
    if cached_result:
        print(f"Cache: HIT → returning cached data")
        logger.info("Cache: HIT → returning cached data")
        return jsonify(cached_result)
    
    print(f"Cache: MISS → calculating new data...")
    logger.info("Cache: MISS → calculating new data...")
    physics_result = calculate_trajectory(angle, velocity, gravity)
    print(f"Physics calculated: max_height={physics_result['max_height']}, range={physics_result['range']}")
    logger.info(f"Physics: max_height={physics_result['max_height']}, range={physics_result['range']}")
    
    explanation_text = generate_explanation_text(
        angle, velocity, gravity,
        custom_formula=custom_formula,
        include_formula=include_formula
    )
    print(f"Calling Sarvam TTS API...")
    logger.info("Calling Sarvam TTS API...")
    speech_result = synthesize_speech(explanation_text)
    print(f"TTS completed: audio_url={'present' if speech_result.get('audio_url') else 'NOT present'}")
    logger.info(f"TTS: audio_url={'present' if speech_result.get('audio_url') else 'NOT present'}")
    
    store_simulation(angle, velocity, gravity)
    print(f"Saved to database")
    logger.info("Saved to database")
    
    full_result = {
        'trajectory': physics_result['trajectory'],
        'max_height': physics_result['max_height'],
        'range': physics_result['range'],
        'time_of_flight': physics_result['time_of_flight'],
        'explanation_text': explanation_text,
        'speech_audio_url': speech_result.get('audio_url')
    }
    
    set_cached_result(cache_key, full_result)
    print(f"Cached result saved\n")
    logger.info("Cached result saved")
    
    return jsonify(full_result)
