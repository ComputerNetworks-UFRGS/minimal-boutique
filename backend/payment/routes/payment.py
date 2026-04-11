from flask import Blueprint, jsonify, request
import requests
from opentelemetry import trace

payment_bp = Blueprint('payment', __name__, url_prefix = '/payment')

ORDERS_API_URL = "http://orders:5002/orders"
CART_API_URL = "http://backend:5000/cart/clear"


tracer =  trace.get_tracer(__name__)

@payment_bp.route('/charge', methods=['POST'])
def charge():

    span = trace.get_current_span()
    data = request.json
    order_id = data.get('order_id')
    user_id = data.get('user_id')

    if not order_id or not user_id:
        return jsonify({"error": "order_id e user_id são obrigatórios"}), 400
    
    span.set_attribute("order.id", order_id)
    span.set_attribute("user.id", user_id)
    
    print(f"Pagamento para o pedido {order_id} processado com sucesso.")

    try:
        confirm_url = f"{ORDERS_API_URL}/{order_id}/confirm_payment"
        confirm_response = requests.post(confirm_url)

        if confirm_response.status_code != 200:
            print(f"ERRO: Falha ao confirmar o pagamento para o pedido {order_id}")
            return jsonify({"error": "Falha ao atualizar o status do pedido"}), 500
            span.set_attribute("payment.status", "declined")
        span.set_attribute("payment.status", "paid")
    
    except requests.exceptions.RequestException as e:
        return jsonify({"error":"Não foi possível conectar ao serviço do pedido"}), 503

    try:
        clear_cart_response = requests.post(CART_API_URL, json={'user_id':user_id}, cookies=request.cookies)
        if clear_cart_response.status_code != 200:
            print(f"AVISO: Não foi possível limpar o carrinho do usuário {user_id}")
    except requests.exceptions.RequestException as e:
        print(f"Aviso: Não foi possível conectar ao backend para limpar o carrinho: {e}")
    
    return jsonify({"message": "Pagamento bem sucedido e pedido confirmado"}), 200

