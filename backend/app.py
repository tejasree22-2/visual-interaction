from flask import Flask
from routes.simulation_routes import simulation_bp

app = Flask(__name__)

app.register_blueprint(simulation_bp, url_prefix='/api')

@app.route('/health')
def health():
    return {'status': 'healthy'}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
