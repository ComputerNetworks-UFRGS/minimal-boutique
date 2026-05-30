from flask import Blueprint, jsonify, request
import requests
import time
import re
from hashlib import md5
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

checkout_bp = Blueprint('checkout', __name__, url_prefix='/checkout')

PRODUCTS_API_URL = "http://products:5001/products/"
ORDERS_API_URL = "http://orders:5002/orders/"

def detect_fraud(user_id, items):
    """
    Expensive fraud detection algorithm - CPU-bound operations.
    Triggered only for orders > R$500.
    """
    fraud_score = 0.0
    
    # Operação 1: Regex intensivo
    item_descriptions = "|".join([str(item) for item in items])
    for i in range(5000000):
        re.search(r"(\d+){1,50}", item_descriptions)
        fraud_score += 0.00001
    
    # Operação 2: Processamento de query
    for j in range(3000000):
        hash_val = md5(f"{user_id}{j}".encode()).hexdigest()
        if hash_val.startswith("0"):
            fraud_score += 0.0001
    
    # Operação 3: Chamada API síncrona
    time.sleep(60.0)
    
    return min(fraud_score + 0.1, 1.0)

@checkout_bp.route('/', methods=['POST'])
def process_checkout():
    data = request.json
    user_id = data.get('user_id')
    cart_items = data.get('cart_items')

    if not user_id or not cart_items:
        return jsonify({"error": "Dados do usuário ou do carrinho ausentes"}), 400

    span = trace.get_current_span()
    span.set_attribute("user.id", user_id)

    total = 0
    order_items_payload = []

    # 1. Validar produtos e calcular o total
    for item in cart_items:
        try:
            product_response = requests.get(f"{PRODUCTS_API_URL}{item['product_id']}")
            if product_response.status_code != 200:
                return jsonify({"error": f"Produto com ID {item['product_id']} não encontrado"}), 404
            product_data = product_response.json()
            price = product_data.get('price')
            total += price * item['quantity']

            span.set_attribute(f"product.{item['product_id']}.price:", price)
            span.set_attribute(f"product.{item['product_id']}.quantity", item['quantity'])

            order_items_payload.append({
                "product_id": item['product_id'], "quantity": item['quantity'], "price": price
            })
        except requests.exceptions.RequestException:
            return jsonify({"error": "Erro de comunicação com o serviço de produtos"}), 503
    # 2. Detecção de fraude para compras de alto valor (> R$500)
    if total > 500:  # ← NOVO: Trigger de fraude
        try:
            fraud_detection_span = tracer.start_span("fraud_detection")
            with fraud_detection_span:
                fraud_detection_span.set_attribute("order.total", total)
                fraud_detection_span.set_attribute("user.id", user_id)
                
                fraud_risk = detect_fraud(user_id, order_items_payload)
                
                fraud_detection_span.set_attribute("fraud_risk", fraud_risk)
                
                if fraud_risk > 0.8:
                    return jsonify({"error": "Order blocked: High fraud risk detected"}), 403
        except Exception as e:
            return jsonify({"error": f"Fraud detection error: {str(e)}"}), 500
    # 23. Criar o pedido com status 'pending'
    if total > 0:
        span.set_attribute("total", total)
        order_payload = {"user_id": user_id, "total": total, "items": order_items_payload}
        try:
            order_response = requests.post(ORDERS_API_URL, json=order_payload)
            if order_response.status_code != 201:
                return jsonify({"error": "Falha ao criar o pedido pendente"}), 500
            
            # 4. Retornar os dados do pedido criado para o frontend
            return jsonify(order_response.json()), 201
        
        except requests.exceptions.RequestException:
            return jsonify({"error": "Erro de comunicação com o serviço de pedidos"}), 503
    
    return jsonify({"error": "Não foi possível calcular o total"}), 400