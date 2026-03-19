import hashlib
from flask import Blueprint, request, jsonify
from concurrent.futures import ThreadPoolExecutor, as_completed

from services.cache_service import get_cached_result, set_cached_result
from services.physics_service import calculate_trajectory
from services.supabase_client import store_simulation
from services.speech_service import generate_explanation_text, synthesize_speech, generate_explanation_text_telugu, generate_chunked_explanations, synthesize_chunk, combine_audio_chunks

simulation_bp = Blueprint('simulation', __name__)

MAX_WORKERS = 4


def _generate_cache_key(angle, velocity, gravity, custom_formula=None, language=None):
    key_str = f"{angle}:{velocity}:{gravity}:{custom_formula or ''}:{language or ''}"
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
    
    print(f"=== Slider Changed ===")
    print(f"angle: {angle}, velocity: {velocity}, gravity: {gravity}")
    print(f"angle: {angle}, velocity: {velocity}, gravity: {gravity}, language: {language}")
    print(f"custom_formula: {custom_formula}, include_formula: {include_formula}")
    
    cache_key = _generate_cache_key(angle, velocity, gravity, custom_formula, language)
    
    cached_result = get_cached_result(cache_key)
    if cached_result:
        print("Cache: HIT")
        return jsonify(cached_result)
    
    print("Cache: MISS → calculating new data...")
    physics_result = calculate_trajectory(angle, velocity, gravity)
    print(f"Physics calculated: max_height={physics_result['max_height']:.4f}, range={physics_result['range']:.4f}")
    
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
    
    print("Calling Sarvam TTS API...")
    speech_result = synthesize_speech(explanation_text, target_language_code=language, save_file=True)
    print(f"TTS completed: audio_url={'present' if speech_result.get('audio_url') else 'not generated'}")
    
    store_simulation(angle, velocity, gravity)
    print("Saved to database")
    
    full_result = {
        'trajectory': physics_result['trajectory'],
        'max_height': physics_result['max_height'],
        'range': physics_result['range'],
        'time_of_flight': physics_result['time_of_flight'],
        'explanation_text': explanation_text,
        'speech_audio_url': speech_result.get('audio_url')
    }
    
    set_cached_result(cache_key, full_result)
    print("Cached result saved")
    
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
    
    print(f"=== Slider Changed ===")
    print(f"angle: {angle}, velocity: {velocity}, gravity: {gravity}")
    print(f"angle: {angle}, velocity: {velocity}, gravity: {gravity}, language: {language}")
    print(f"custom_formula: {custom_formula}, include_formula: {include_formula}")
    
    chunks = generate_chunked_explanations(
        angle, velocity, gravity,
        custom_formula=custom_formula,
        include_formula=include_formula
    )
    print(f"Generated {len(chunks)} explanation chunks")
    print("Calling Sarvam TTS API...")
    
    def synthesize_single_chunk(chunk):
        try:
            return synthesize_chunk(chunk, language=language)
        except Exception as e:
            return None
    
    chunk_data = []
    audio_urls = []
    failed_chunks = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(synthesize_single_chunk, chunk): chunk for chunk in chunks}
        for future in as_completed(futures):
            chunk = future.result()
            if chunk:
                chunk_data.append(chunk.to_dict())
                audio_url = chunk.audio_url_te if language == "te-IN" else chunk.audio_url_en
                if audio_url:
                    audio_urls.append(audio_url)
                else:
                    failed_chunks += 1
            else:
                failed_chunks += 1
    
    print(f"TTS completed: audio_url={'present' if audio_urls else 'not generated'}")
    
    combined_audio_url = None
    if audio_urls:
        combined_audio_url = combine_audio_chunks(audio_urls)
    
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
