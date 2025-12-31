from flask import Flask
from routes.orders import orders_bp
from database import init_db
from flask_cors import CORS 
from telemetry import configure_telemetry

app = Flask(__name__)
app.secret_key = 'secret_key_orders'

CORS(app, supports_credentials=True)

app.register_blueprint(orders_bp)

init_db(app)

configure_telemetry(app, "orders")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port = 5002, debug=True)