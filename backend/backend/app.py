from flask import Flask
from routes.auth import auth_bp
from routes.gateway import gateway_bp
from database import init_db
from flask_cors import CORS
from telemetry import configure_telemetry


app = Flask(__name__)
app.secret_key = 'secret_key'

CORS(app, supports_credentials=True)

app.register_blueprint(auth_bp)
app.register_blueprint(gateway_bp)

init_db(app)

configure_telemetry(app, "backend")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

