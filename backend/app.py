from flask import Flask, send_from_directory, make_response
from flask_cors import CORS
from routes.simulation_routes import simulation_bp
from dotenv import load_dotenv
import os
import logging
import sys
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('visual-interaction-backend')

media_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media")
os.makedirs(media_dir, exist_ok=True)

app.register_blueprint(simulation_bp, url_prefix='/api')

logger.info("=" * 60)
logger.info("  Visual Interaction Backend Starting...")
logger.info("=" * 60)
logger.info(f"  Time: {datetime.now().isoformat()}")
logger.info(f"  Flask Env: {os.getenv('FLASK_ENV', 'not set')}")
logger.info(f"  Media Directory: {media_dir}")
logger.info(f"  Redis URL: {'configured' if os.getenv('REDIS_URL') else 'NOT CONFIGURED'}")
logger.info(f"  Supabase: {'configured' if os.getenv('SUPABASE_CONNECTION_STRING') else 'NOT CONFIGURED'}")
logger.info(f"  Sarvam API: {'configured' if os.getenv('SARVAM_API_KEY') else 'NOT CONFIGURED'}")
logger.info("=" * 60)
logger.info("  Server ready at http://0.0.0.0:5000")
logger.info("  Health check: http://0.0.0.0:5000/health")
logger.info("  API endpoints: /api/simulation, /api/chunks")
logger.info("=" * 60)

@app.before_request
def log_request():
    logger.info(f"REQUEST: {request.method} {request.path}")

@app.after_request
def log_response(response):
    logger.info(f"RESPONSE: {request.method} {request.path} → {response.status_code}")
    return response

@app.route('/health')
def health():
    import subprocess
    import importlib.util
    
    pydub_ok = importlib.util.find_spec("pydub") is not None
    ffmpeg_ok = False
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        ffmpeg_ok = result.returncode == 0
    except Exception:
        pass
    
    redis_ok = os.getenv('REDIS_URL') is not None
    supabase_ok = os.getenv('SUPABASE_CONNECTION_STRING') is not None
    sarvam_ok = os.getenv('SARVAM_API_KEY') is not None
    
    media_files = len(os.listdir(media_dir)) if os.path.exists(media_dir) else 0
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'audio': {
            'pydub': pydub_ok,
            'ffmpeg': ffmpeg_ok
        },
        'services': {
            'redis': redis_ok,
            'supabase': supabase_ok,
            'sarvam': sarvam_ok
        },
        'media': {
            'files_count': media_files
        }
    }
    
    if not (pydub_ok and ffmpeg_ok and sarvam_ok):
        health_status['warnings'] = 'Some audio services may not work properly'
    
    logger.info(f"Health check: OK - {health_status}")
    return health_status

@app.route('/media/<path:filename>')
def serve_media(filename):
    import os
    from flask import abort
    
    file_path = os.path.join(media_dir, filename)
    
    if not os.path.exists(file_path):
        logger.warning(f"MEDIA 404: File not found - {filename}")
        abort(404)
    
    ext = os.path.splitext(filename)[1].lower()
    mime_types = {
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.ogg': 'audio/ogg',
        '.m4a': 'audio/mp4',
        '.json': 'application/json'
    }
    mimetype = mime_types.get(ext, 'application/octet-stream')
    
    logger.info(f"MEDIA 200: Serving {filename} as {mimetype}")
    
    response = make_response(send_from_directory(media_dir, filename))
    response.headers['Content-Type'] = mimetype
    response.headers['Accept-Ranges'] = 'bytes'
    return response

if __name__ == '__main__':
    from flask import request
    logger.info("Starting Flask development server...")
    logger.info("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
