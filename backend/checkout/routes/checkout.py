from flask import Blueprint, jsonify, request
import requests

from opentelemetry import trace

tracer = trace.get_tracer(__name__)

checkout_bp = Blueprint('checkout', __name__, url_prefix='/checkout')

PRODUCTS_API_URL = "http://products:5001/products/"
ORDERS_API_URL = "http://orders:5002/orders/"

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

    # 2. Criar o pedido com status 'pending'
    if total > 0:
        span.set_attribute("total", total)
        order_payload = {"user_id": user_id, "total": total, "items": order_items_payload}
        try:
            order_response = requests.post(ORDERS_API_URL, json=order_payload)
            if order_response.status_code != 201:
                return jsonify({"error": "Falha ao criar o pedido pendente"}), 500
            
            # 3. Retornar os dados do pedido criado para o frontend
            return jsonify(order_response.json()), 201
        
        except requests.exceptions.RequestException:
            return jsonify({"error": "Erro de comunicação com o serviço de pedidos"}), 503
    
    return jsonify({"error": "Não foi possível calcular o total"}), 400