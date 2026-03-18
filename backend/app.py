from flask import Flask, send_from_directory
from flask_cors import CORS
from routes.simulation_routes import simulation_bp
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

media_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media")
os.makedirs(media_dir, exist_ok=True)

app.register_blueprint(simulation_bp, url_prefix='/api')

@app.route('/health')
def health():
    return {'status': 'healthy'}

@app.route('/media/<path:filename>')
def serve_media(filename):
    return send_from_directory(media_dir, filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
