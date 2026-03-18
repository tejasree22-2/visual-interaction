import hashlib
import logging
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

from services.cache_service import get_cached_result, set_cached_result
from services.physics_service import calculate_trajectory
from services.supabase_client import store_simulation
from services.speech_service import generate_explanation_text, synthesize_speech, generate_explanation_text_telugu, generate_chunked_explanations, synthesize_chunk, combine_audio_chunks

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
        language = data.get('language', 'en-IN')
        speech_result = synthesize_speech(text, target_language_code=language)
        return jsonify({
            'speech_audio_url': speech_result.get('audio_url'),
            'error': speech_result.get('error')
        })
    
    angle = data.get('angle')
    velocity = data.get('velocity')
    gravity = data.get('gravity')
    custom_formula = data.get('custom_formula')
    include_formula = data.get('include_formula', False)
    language = data.get('language', 'en-IN')
    
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
    
    if language == "te-IN":
        explanation_text = generate_explanation_text_telugu(
            angle, velocity, gravity,
            custom_formula=custom_formula,
            include_formula=include_formula
        )
    else:
        explanation_text = generate_explanation_text(
            angle, velocity, gravity,
            custom_formula=custom_formula,
            include_formula=include_formula
        )
    
    print(f"Calling Sarvam TTS API...")
    logger.info("Calling Sarvam TTS API...")
    speech_result = synthesize_speech(explanation_text, target_language_code=language)
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


@simulation_bp.route('/chunks', methods=['POST'])
def get_audio_chunks():
    data = request.get_json() or {}
    
    angle = data.get('angle', 45)
    velocity = data.get('velocity', 20)
    gravity = data.get('gravity', 9.81)
    custom_formula = data.get('custom_formula')
    include_formula = data.get('include_formula', False)
    language = data.get('language', 'te-IN')
    
    print(f"\n=== Chunked Audio Request ===")
    print(f"angle: {angle}, velocity: {velocity}, gravity: {gravity}, language: {language}")
    logger.info(f"Chunked audio request: angle={angle}, velocity={velocity}, gravity={gravity}, language={language}")
    
    chunks = generate_chunked_explanations(
        angle, velocity, gravity,
        custom_formula=custom_formula,
        include_formula=include_formula
    )
    
    print(f"Generated {len(chunks)} explanation chunks")
    logger.info(f"Generated {len(chunks)} explanation chunks")
    
    chunk_data = []
    audio_urls = []
    failed_chunks = 0
    for chunk in chunks:
        try:
            chunk = synthesize_chunk(chunk, language=language)
            chunk_data.append(chunk.to_dict())
            audio_url = chunk.audio_url_te if language == "te-IN" else chunk.audio_url_en
            if audio_url:
                audio_urls.append(audio_url)
            else:
                print(f"Warning: No audio generated for chunk {chunk.chunk_id}")
                failed_chunks += 1
        except Exception as e:
            print(f"Error synthesizing chunk {chunk.chunk_id}: {e}")
            failed_chunks += 1
    
    print(f"Audio chunks: {len(audio_urls)} successful, {failed_chunks} failed out of {len(chunks)} total")
    
    combined_audio_url = None
    if audio_urls:
        combined_audio_url = combine_audio_chunks(audio_urls)
        print(f"Combined audio created: {'success' if combined_audio_url else 'failed'}")
        logger.info(f"Combined audio: {'success' if combined_audio_url else 'failed'}")
    
    return jsonify({
        'chunks': chunk_data,
        'total_chunks': len(chunk_data),
        'combined_audio_url': combined_audio_url
    })


@simulation_bp.route('/chunk/<chunk_id>', methods=['POST'])
def get_single_chunk_audio(chunk_id):
    data = request.get_json() or {}
    
    angle = data.get('angle', 45)
    velocity = data.get('velocity', 20)
    gravity = data.get('gravity', 9.81)
    custom_formula = data.get('custom_formula')
    include_formula = data.get('include_formula', False)
    language = data.get('language', 'te-IN')
    
    print(f"\n=== Single Chunk Request: {chunk_id} ===")
    logger.info(f"Single chunk request: chunk_id={chunk_id}, language={language}")
    
    chunks = generate_chunked_explanations(
        angle, velocity, gravity,
        custom_formula=custom_formula,
        include_formula=include_formula
    )
    
    target_chunk = None
    for chunk in chunks:
        if chunk.chunk_id == chunk_id:
            target_chunk = chunk
            break
    
    if target_chunk is None:
        return jsonify({'error': 'Chunk not found', 'chunk_id': chunk_id}), 404
    
    target_chunk = synthesize_chunk(target_chunk, language=language)
    
    return jsonify({
        'chunk': target_chunk.to_dict()
    })


@simulation_bp.route('/combine-chunks', methods=['POST'])
def combine_audio_chunks_endpoint():
    data = request.get_json() or {}
    
    audio_urls = data.get('audio_urls', [])
    
    if not audio_urls:
        return jsonify({'error': 'No audio URLs provided'}), 400
    
    combined_audio = combine_audio_chunks(audio_urls)
    
    if combined_audio is None:
        return jsonify({'error': 'Failed to combine audio chunks. Make sure pydub is installed.'}), 500
    
    return jsonify({
        'combined_audio_url': combined_audio
    })
