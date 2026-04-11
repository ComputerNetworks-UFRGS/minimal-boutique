from flask import Blueprint, jsonify, session, request
import requests
from opentelemetry import trace

gateway_bp = Blueprint('gateway', __name__)

ORDERS_API_URL = "http://orders:5002/orders/"
PRODUCTS_API_URL = "http://products:5001/products/"
CHECKOUT_API_URL = "http://checkout:5003/checkout/"
PAYMENT_API_URL = "http://payment:5004/payment/"
CART_API_URL = "http://cart:5005/cart/"


tracer = trace.get_tracer(__name__)

@gateway_bp.route('/orders/', methods=['GET'])
def get_user_orders():
    #Inicialização da telemetria
    span = trace.get_current_span()

    #Verificação de autenticação do usuário
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Usuário não autenticado"}), 401
    span.set_attribute("user.id", user_id)

    try:
        # Repassando os cookies para o serviço de pedidos
        response = requests.get(ORDERS_API_URL, params={'user_id': user_id}, cookies=request.cookies)
        return response.content, response.status_code, response.headers.items()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Não foi possível conectar ao serviço de pedidos", "details": str(e)}), 503

@gateway_bp.route('/products/', methods=['GET'])
def get_all_products():
    try:
        response = requests.get(PRODUCTS_API_URL)
        return response.content, response.status_code, response.headers.items()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Não foi possível conectar ao serviço de produtos", "details": str(e)}), 503

@gateway_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    try:
        response = requests.get(f"{PRODUCTS_API_URL}{product_id}")
        return response.content, response.status_code, response.headers.items()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Não foi possível conectar ao serviço de produtos", "details": str(e)}), 503

@gateway_bp.route('/checkout/', methods=['POST'])
def checkout_gateway():
    span = trace.get_current_span()
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Usuário não autenticado"}), 401
    span.set_attribute("user.id", user_id)

    try:
        cart_response = requests.get(CART_API_URL, params={'user_id': user_id}, cookies=request.cookies)
        if cart_response.status_code != 200:
            return jsonify({"error": "Não foi possível buscar os itens do carrinho"}), cart_response.status_code
        
        cart_items = cart_response.json()
        if not cart_items:
            return jsonify({"error": "Carrinho vazio"}), 400

        payload = {
            "user_id": user_id,
            "cart_items": cart_items
        }

        checkout_response = requests.post(CHECKOUT_API_URL, json=payload, cookies=request.cookies)
        return checkout_response.content, checkout_response.status_code, checkout_response.headers.items()

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Erro de comunicação com os serviços", "details": str(e)}), 503


@gateway_bp.route('/payment/charge', methods=['POST'])
def payment_gateway():
    span = trace.get_current_span()
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Usuário não autenticado"}), 401
    span.set_attribute("user.id", user_id)
    
    payload = request.json
    payload['user_id'] = user_id
    try:
        response = requests.post(f"{PAYMENT_API_URL}charge", json=payload, cookies=request.cookies)
        return response.content, response.status_code, response.headers.items()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Não foi possível conectar ao serviço de pagamento"}), 503

 
@gateway_bp.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order_gateway(order_id):
    try:
        response = requests.delete(f"{ORDERS_API_URL}{order_id}", cookies=request.cookies)
        return response.content, response.status_code, response.headers.items()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Não foi possível conectar ao serviço de pedidos", "details": str(e)}), 503


 
@gateway_bp.route('/cart/', methods=['GET', 'POST'])
def cart_gateway():

    if 'user_id' not in session:
        return jsonify({"error": "Usuário não autenticado"}), 401

    if request.method == 'POST':
        try:

            response = requests.post(CART_API_URL, json=request.json, cookies=request.cookies)
            return response.content, response.status_code, response.headers.items()
        except requests.exceptions.RequestException as e:
            return jsonify({"error": "Não foi possível conectar ao serviço de carrinho", "details": str(e)}), 503
    else: # GET
        try:

            response = requests.get(CART_API_URL, cookies=request.cookies)
            return response.content, response.status_code, response.headers.items()
        except requests.exceptions.RequestException as e:
            return jsonify({"error": "Não foi possível conectar ao serviço de carrinho", "details": str(e)}), 503


@gateway_bp.route('/cart/<int:item_id>', methods=['DELETE'])
def delete_cart_item_gateway(item_id):
    if 'user_id' not in session:
        return jsonify({"error": "Usuário não autenticado"}), 401

    try:

        response = requests.delete(f"{CART_API_URL}{item_id}", cookies=request.cookies)
        return response.content, response.status_code, response.headers.items()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Não foi possível conectar ao serviço de carrinho", "details": str(e)}), 503




@gateway_bp.route('/cart/clear', methods=['POST'])
def clear_cart_gateway():
    if 'user_id' not in session:
        return jsonify({"error": "Usuário não autenticado"}), 401

    try:
        response = requests.post(f"{CART_API_URL}clear", json=request.json, cookies=request.cookies)
        return response.content, response.status_code, response.headers.items()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Não foi possível conectar ao serviço de carrinho", "details": str(e)}), 503