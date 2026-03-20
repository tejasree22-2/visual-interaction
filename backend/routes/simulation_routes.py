import hashlib
import json
import logging
from flask import Blueprint, request, jsonify
from concurrent.futures import ThreadPoolExecutor, as_completed

from services.cache_service import get_cached_result, set_cached_result, track_user_change, get_user_changes, clear_user_changes
from services.physics_service import calculate_trajectory
from services.supabase_client import store_simulation
from services.speech_service import generate_explanation_text, synthesize_speech, generate_explanation_text_telugu, generate_chunked_explanations, synthesize_chunk, combine_audio_chunks

simulation_bp = Blueprint('simulation', __name__)
logger = logging.getLogger('visual-interaction-backend.routes')

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
        logger.info(f"Text-to-speech request | language={language} | text_length={len(text)}")
        speech_result = synthesize_speech(text, target_language_code=language)
        logger.info(f"TTS result | audio_url={'present' if speech_result.get('audio_url') else 'MISSING'} | error={speech_result.get('error')}")
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
    
    logger.info("=" * 50)
    logger.info("SIMULATION REQUEST RECEIVED")
    logger.info("=" * 50)
    logger.info(f"Parameters: angle={angle}, velocity={velocity}, gravity={gravity}")
    logger.info(f"Language: {language}")
    logger.info(f"Custom formula: {custom_formula} | include_formula: {include_formula}")
    
    cache_key = _generate_cache_key(angle, velocity, gravity, custom_formula, language)
    
    cached_result = get_cached_result(cache_key)
    if cached_result:
        logger.info("CACHE: HIT - Returning cached result")
        return jsonify(cached_result)
    
    logger.info("CACHE: MISS - Calculating new simulation data...")
    physics_result = calculate_trajectory(angle, velocity, gravity)
    logger.info(f"SUCCESS: Physics calculated | max_height={physics_result['max_height']:.4f}m | range={physics_result['range']:.4f}m | time_of_flight={physics_result['time_of_flight']:.4f}s")
    
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
    logger.info(f"Explanation text generated | length={len(explanation_text)} chars")
    
    logger.info("Calling Sarvam TTS API...")
    speech_result = synthesize_speech(explanation_text, target_language_code=language, save_file=True)
    
    if speech_result.get('audio_url'):
        logger.info(f"SUCCESS: TTS completed | audio_url={speech_result.get('audio_url')}")
    else:
        logger.warning(f"FAILED: TTS failed | error={speech_result.get('error')}")
    
    db_result = store_simulation(angle, velocity, gravity)
    if db_result:
        logger.info("SUCCESS: Saved to database")
    else:
        logger.warning("WARNING: Database save failed (continuing anyway)")
    
    full_result = {
        'trajectory': physics_result['trajectory'],
        'max_height': physics_result['max_height'],
        'range': physics_result['range'],
        'time_of_flight': physics_result['time_of_flight'],
        'explanation_text': explanation_text,
        'speech_audio_url': speech_result.get('audio_url'),
        'error': speech_result.get('error')
    }
    
    set_cached_result(cache_key, full_result)
    logger.info("SUCCESS: Cached result saved")
    logger.info("=" * 50)
    
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
    
    logger.info("=" * 50)
    logger.info("CHUNKS REQUEST RECEIVED")
    logger.info("=" * 50)
    logger.info(f"Parameters: angle={angle}, velocity={velocity}, gravity={gravity}")
    logger.info(f"Language: {language}")
    logger.info(f"Custom formula: {custom_formula} | include_formula: {include_formula}")
    
    chunks = generate_chunked_explanations(
        angle, velocity, gravity,
        custom_formula=custom_formula,
        include_formula=include_formula
    )
    logger.info(f"Generated {len(chunks)} explanation chunks")
    logger.info("Calling Sarvam TTS API for all chunks...")
    
    def synthesize_single_chunk(chunk):
        try:
            result = synthesize_chunk(chunk, language=language)
            if result.audio_url_te if language == "te-IN" else result.audio_url_en:
                logger.info(f"SUCCESS: Chunk '{chunk.chunk_id}' TTS completed")
            else:
                logger.warning(f"FAILED: Chunk '{chunk.chunk_id}' TTS failed")
            return result
        except Exception as e:
            logger.error(f"ERROR: Chunk '{chunk.chunk_id}' exception: {e}")
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
    
    logger.info(f"TTS Summary: {len(audio_urls)} succeeded, {failed_chunks} failed")
    
    combined_audio_url = None
    if audio_urls:
        logger.info("Combining audio chunks...")
        combined_audio_url = combine_audio_chunks(audio_urls)
        if combined_audio_url:
            logger.info(f"SUCCESS: Combined audio created | url={combined_audio_url}")
        else:
            logger.error("FAILED: Could not combine audio chunks (check pydub/ffmpeg installation)")
    else:
        logger.error("FAILED: No audio URLs to combine")
    
    logger.info("=" * 50)
    
    return jsonify({
        'chunks': chunk_data,
        'total_chunks': len(chunk_data),
        'combined_audio_url': combined_audio_url,
        'failed_chunks': failed_chunks
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
    
    logger.info(f"SINGLE CHUNK REQUEST | chunk_id={chunk_id} | language={language}")
    
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
        logger.warning(f"CHUNK NOT FOUND | chunk_id={chunk_id}")
        return jsonify({'error': 'Chunk not found', 'chunk_id': chunk_id}), 404
    
    logger.info(f"Synthesizing chunk '{chunk_id}'...")
    target_chunk = synthesize_chunk(target_chunk, language=language)
    
    audio_url = target_chunk.audio_url_te if language == "te-IN" else target_chunk.audio_url_en
    if audio_url:
        logger.info(f"SUCCESS: Chunk '{chunk_id}' audio generated | url={audio_url}")
    else:
        logger.error(f"FAILED: Chunk '{chunk_id}' audio generation failed")
    
    return jsonify({
        'chunk': target_chunk.to_dict()
    })


@simulation_bp.route('/combine-chunks', methods=['POST'])
def combine_audio_chunks_endpoint():
    data = request.get_json() or {}
    
    audio_urls = data.get('audio_urls', [])
    
    if not audio_urls:
        logger.warning("COMBINE CHUNKS: No audio URLs provided")
        return jsonify({'error': 'No audio URLs provided'}), 400
    
    logger.info(f"COMBINE CHUNKS: Received {len(audio_urls)} URLs")
    combined_audio = combine_audio_chunks(audio_urls)
    
    if combined_audio is None:
        logger.error("FAILED: Could not combine audio chunks")
        return jsonify({'error': 'Failed to combine audio chunks. Make sure pydub is installed and ffmpeg is available.'}), 500
    
    logger.info(f"SUCCESS: Combined audio created | url={combined_audio}")
    return jsonify({
        'combined_audio_url': combined_audio
    })


@simulation_bp.route('/track-changes', methods=['POST'])
def track_changes():
    data = request.get_json() or {}
    
    session_id = data.get('session_id', 'default')
    changes = data.get('changes', {})
    action = data.get('action', 'update')
    
    logger.info("=" * 60)
    logger.info("🔔 USER CHANGE TRACKED")
    logger.info("=" * 60)
    logger.info(f"📱 Session ID: {session_id}")
    logger.info(f"⚡ Action: {action}")
    logger.info(f"📝 Changes: {json.dumps(changes, indent=2)}")
    
    if action == 'clear':
        clear_user_changes(session_id)
        logger.info(f"✅ USER CHANGES: Cleared for session {session_id}")
        return jsonify({
            'status': 'cleared',
            'session_id': session_id
        })
    
    if not changes:
        logger.warning("⚠️ USER CHANGES: No changes provided")
        return jsonify({'error': 'No changes provided'}), 400
    
    change_entry = track_user_change(session_id, changes)
    
    logger.info("=" * 60)
    logger.info(f"📊 CHANGE SUMMARY:")
    logger.info(f"   Field: {change_entry['field']}")
    logger.info(f"   Old Value: {change_entry['old_value']}")
    logger.info(f"   New Value: {change_entry['new_value']}")
    logger.info(f"   Time: {change_entry['timestamp']}")
    logger.info("=" * 60)
    
    return jsonify({
        'status': 'tracked',
        'change': change_entry,
        'session_id': session_id
    })


@simulation_bp.route('/get-changes', methods=['GET'])
def get_changes():
    session_id = request.args.get('session_id', 'default')
    limit = int(request.args.get('limit', 50))
    
    logger.info(f"USER CHANGES: Retrieving changes for session {session_id}, limit={limit}")
    
    changes = get_user_changes(session_id, limit)
    
    logger.info(f"USER CHANGES: Retrieved {len(changes)} changes")
    
    return jsonify({
        'session_id': session_id,
        'changes': changes,
        'total': len(changes)
    })


@simulation_bp.route('/debug/changes-dashboard')
def changes_dashboard():
    from flask import render_template_string
    from services.cache_service import _changes_history
    
    all_changes_list = []
    for session_id, changes in _changes_history.items():
        for change in changes:
            change_copy = change.copy()
            change_copy['session_id'] = session_id
            all_changes_list.append(change_copy)
    
    all_changes_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    all_changes_list = all_changes_list[:50]
    
    rows_html = ''
    for change in all_changes_list:
        rows_html += f'''
            <tr>
                <td class="timestamp">{change.get('timestamp', '')[:19]}</td>
                <td class="session">{change.get('session_id', 'unknown')}</td>
                <td class="field">{change.get('field', 'unknown')}</td>
                <td class="old">{change.get('old_value', '-')}</td>
                <td class="new">{change.get('new_value', '-')}</td>
            </tr>
        '''
    
    if not rows_html:
        rows_html = '<tr><td colspan="5" style="text-align:center;color:#808080;">No changes tracked yet</td></tr>'
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>User Changes Debug Dashboard</title>
        <meta http-equiv="refresh" content="2">
        <style>
            body {{ font-family: 'Courier New', monospace; background: #1e1e1e; color: #d4d4d4; padding: 20px; }}
            h1 {{ color: #4ec9b0; }}
            .change {{ background: #2d2d2d; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #4ec9b0; }}
            .timestamp {{ color: #808080; font-size: 12px; }}
            .field {{ color: #569cd6; font-weight: bold; }}
            .old {{ color: #f14c4c; text-decoration: line-through; }}
            .new {{ color: #4ec9b0; font-weight: bold; }}
            .session {{ color: #dcdcaa; }}
            .arrow {{ color: #c586c0; margin: 0 10px; }}
            .total {{ color: #ce9178; margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #3e3e3e; }}
            th {{ background: #2d2d2d; color: #4ec9b0; }}
        </style>
    </head>
    <body>
        <h1>🔔 User Changes Debug Dashboard</h1>
        <p class="total">Auto-refreshes every 2 seconds | <a href="/api/debug/changes-dashboard" style="color:#4ec9b0;">Refresh Now</a></p>
        <h2 style="color:#569cd6;">Recent Changes (All Sessions)</h2>
        <table>
            <tr>
                <th>Time</th>
                <th>Session</th>
                <th>Field</th>
                <th>Old Value</th>
                <th>New Value</th>
            </tr>
            {rows_html}
        </table>
        <p style="color:#808080; margin-top:20px;">Total changes tracked: {len(all_changes_list)}</p>
    </body>
    </html>
    '''
    
    return html
