from flask import Flask 
from routes.checkout import checkout_bp
from flask_cors import CORS 
from telemetry import configure_telemetry

app = Flask(__name__)

app.secret_key = 'secret_key_checkout'

CORS(app, supports_credentials = True)

app.register_blueprint(checkout_bp)

configure_telemetry(app, "checkout")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)

