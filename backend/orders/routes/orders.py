from flask import Blueprint, jsonify, request
from models import Order, OrderItem
from database import db
import requests
from opentelemetry import trace
import datetime
from sqlalchemy.orm import joinedload

tracer = trace.get_tracer(__name__)

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

# Cache simples em memória
product_cache = {}
CACHE_TTL_SECONDS = 300  # 5 minutos

def get_product_from_cache(product_id):
    """Retorna produto do cache se ainda for válido"""
    entry = product_cache.get(product_id)
    if not entry:
        return None

    # Verifica expiração
    if (datetime.datetime.now() - entry["timestamp"]).total_seconds() > CACHE_TTL_SECONDS:
        del product_cache[product_id]
        return None

    return entry["data"]

def fetch_product(product_id):
    """Busca o produto no cache ou via requisição HTTP"""
    # 1️⃣ Tenta cache
    cached = get_product_from_cache(product_id)
    if cached:
        return cached, True  # True indica que veio do cache

    # 2️⃣ Se não está no cache, busca no serviço products
    try:
        response = requests.get(f"http://products:5001/products/{product_id}", timeout=3)
        if response.status_code == 200:
            product_data = response.json()
            # Atualiza cache
            product_cache[product_id] = {
                "data": product_data,
                "timestamp": datetime.datetime.now()
            }
            return product_data, False
        else:
            print(f"[WARN] Falha ao buscar produto {product_id}: {response.status_code}")
            return None, False
    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Requisição ao serviço de produtos falhou: {e}")
        return None, False


# ===============================================================
# CREATE ORDER
# ===============================================================
@orders_bp.route('/', methods=['POST'])
def create_order():
    span = trace.get_current_span()

    data = request.json
    user_id = data.get('user_id')
    total = data.get('total')
    items = data.get('items')

    if not all([user_id, total, items]):
        return jsonify({'error': 'Dados incompletos para criar o pedido'}), 400
    
    span.set_attribute("user.id", user_id)
    span.set_attribute("total", total)
    span.set_attribute("number.of.items", len(items))

    order = Order(user_id=user_id, total=total)
    db.session.add(order)
    db.session.flush() 
    span.set_attribute("order.id", order.id)

    for item_data in items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data['product_id'],
            quantity=item_data['quantity'],
            price=item_data['price']
        )
        db.session.add(order_item)

    db.session.commit()
    return jsonify({'message': 'Pedido criado com sucesso', 'order_id': order.id}), 201


# ===============================================================
# GET ORDERS (agora com cache item a item)
# ===============================================================
@orders_bp.route('/', methods=['GET'])
def get_orders():
    span = trace.get_current_span()

    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id é obrigatório'}), 400
    span.set_attribute("user.id", user_id)

    # Parâmetros opcionais de paginação (default: últimos 20)
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))

    orders = (
        Order.query
        .options(joinedload(Order.items))
        .filter_by(user_id=user_id)
        .order_by(Order.id.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    span.set_attribute("number.of.orders", len(orders))
    span.set_attribute("pagination.limit", limit)
    span.set_attribute("pagination.offset", offset)

    result = []
    cache_hits = 0
    cache_misses = 0

    for order in orders:
        items_data = []
        for item in order.items:
            product_data, from_cache = fetch_product(item.product_id)
            if from_cache:
                cache_hits += 1
            else:
                cache_misses += 1

            if product_data:
                product_name = product_data.get('name', 'Nome não encontrado')
            else:
                product_name = 'Produto não encontrado ou erro no serviço'

            items_data.append({
                'product_name': product_name,
                'quantity': item.quantity,
                'price': item.price
            })

        result.append({
            'id': order.id,
            'total': order.total,
            'status': order.status,
            'items': items_data
        })

    span.set_attribute("cache.hits", cache_hits)
    span.set_attribute("cache.misses", cache_misses)

    return jsonify(result)


# ===============================================================
# CONFIRM PAYMENT
# ===============================================================
@orders_bp.route('/<int:order_id>/confirm_payment', methods=['POST'])
def confirm_payment(order_id):
    span = trace.get_current_span()

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Pedido não encontrado"}), 404
    span.set_attribute("order.id", order.id)
    
    order.status = 'paid'
    span.set_attribute("payment.status", "paid")
    db.session.commit()

    return jsonify({"message": "Pagamento do pedido confirmado com sucesso"}), 200


# ===============================================================
# DELETE ORDER
# ===============================================================
@orders_bp.route('/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    span = trace.get_current_span()
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Pedido não encontrado"}), 404
    span.set_attribute("order.id", order.id)
    
    if order.status != 'pending':
        return jsonify({"error": "Apenas pedidos pendentes podem ser cancelados"}), 400
    
    for item in order.items:
        try:
            requests.post(
                f"http://products:5001/products/{item.product_id}/release",
                json={'quantity': item.quantity},
                timeout=3
            )
        except requests.exceptions.RequestException as e:
            print(f"ERRO CRÍTICO: Falha ao liberar estoque para product_id {item.product_id}. Detalhes: {e}")
    
    db.session.delete(order)
    db.session.commit()

    return jsonify({"message": "Pedido cancelado com sucesso"}), 200
