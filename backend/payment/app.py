from flask import Flask 
from routes.payment import payment_bp
from telemetry import configure_telemetry

app = Flask(__name__)
app.register_blueprint(payment_bp)

configure_telemetry(app, "payment")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)