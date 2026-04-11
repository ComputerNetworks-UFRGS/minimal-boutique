import requests
import datetime
from flask import Blueprint, request, jsonify, session
from models import CartItem
from database import db
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

PRODUCTS_API_URL = "http://products:5001/products"

# ===============================================================
# Cache local simples
# ===============================================================
product_cache = {}
CACHE_TTL_SECONDS = 300  # 5 minutos

def get_product_from_cache(product_id):
    """Retorna produto do cache se ainda for válido"""
    entry = product_cache.get(product_id)
    if not entry:
        return None
    if (datetime.datetime.now() - entry["timestamp"]).total_seconds() > CACHE_TTL_SECONDS:
        del product_cache[product_id]
        return None
    return entry["data"]

def fetch_product(product_id):
    """Busca produto do cache ou do serviço de produtos"""
    cached = get_product_from_cache(product_id)
    if cached:
        return cached, True  # True = veio do cache

    try:
        response = requests.get(f"{PRODUCTS_API_URL}/{product_id}", timeout=3)
        if response.status_code == 200:
            product_data = response.json()
            product_cache[product_id] = {
                "data": product_data,
                "timestamp": datetime.datetime.now()
            }
            return product_data, False
        else:
            print(f"[WARN] Falha ao buscar produto {product_id}: {response.status_code}")
            return None, False
    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Falha ao buscar produto {product_id}: {e}")
        return None, False


# ===============================================================
# ADD TO CART
# ===============================================================
@cart_bp.route('/', methods=['POST'])
def add_to_cart():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Usuário não encontrado'}), 401

    span = trace.get_current_span()
    span.set_attribute("user.id", user_id)

    data = request.json
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    span.set_attribute("product.id", product_id)
    span.set_attribute("quantity", quantity)

    try:
        reserve_response = requests.post(f"{PRODUCTS_API_URL}/{product_id}/reserve", json={'quantity': quantity})
        if reserve_response.status_code != 200:
            error_data = reserve_response.json()
            return jsonify({"error": error_data.get("error", "Não foi possível reservar o produto")}), reserve_response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Erro de comunicação com o serviço de produtos', 'details': str(e)}), 503

    item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()

    if item:
        item.quantity += quantity
    else:
        item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(item)
    
    db.session.commit()
    span.set_attribute("stock.items", item.quantity)
    return jsonify({"message": "Item adicionado ao carrinho"}), 201


# ===============================================================
# REMOVE ITEM FROM CART
# ===============================================================
@cart_bp.route('/<int:item_id>', methods=['DELETE'])
def remove_from_cart(item_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    span = trace.get_current_span()
    span.set_attribute("user.id", user_id)
    
    item = CartItem.query.filter_by(id=item_id, user_id=user_id).first()
    if not item:
        return jsonify({"error": "Item não encontrado"}), 404

    product_id = item.product_id
    quantity_to_release = item.quantity
    db.session.delete(item)
    db.session.commit()

    span.set_attribute("product.id", product_id)
    span.set_attribute("deleted.quantity", quantity_to_release)

    try:
        requests.post(f"{PRODUCTS_API_URL}/{product_id}/release", json={'quantity': quantity_to_release})
    except requests.exceptions.RequestException as e:
        print(f"ERRO CRÍTICO: Falha ao liberar estoque para product_id {product_id}. Detalhes: {e}")

    return jsonify({"message": "Item removido"}), 200


# ===============================================================
# CLEAR CART
# ===============================================================
@cart_bp.route('/clear', methods=['POST'])
def clear_cart():
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id é obrigatório"}), 400
    span = trace.get_current_span()
    span.set_attribute("user.id", user_id)
    
    try:
        CartItem.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return jsonify({"message": "Carrinho limpo com sucesso"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Falha ao limpar o carrinho", "details": str(e)}), 500


# ===============================================================
# GET CART (agora com cache local)
# ===============================================================
@cart_bp.route('/', methods=['GET'])
def get_cart():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Usuário não encontrado'}), 401

    span = trace.get_current_span()
    span.set_attribute("user.id", user_id)

    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return jsonify([])

    product_ids = [item.product_id for item in cart_items]
    span.set_attribute("cart.product.count", len(product_ids))

    result = []
    cache_hits = 0
    cache_misses = 0

    for item in cart_items:
        product_data, from_cache = fetch_product(item.product_id)
        if from_cache:
            cache_hits += 1
        else:
            cache_misses += 1

        if product_data:
            result.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product_data.get('name'),
                "quantity": item.quantity,
                "price": product_data.get('price')
            })
        else:
            result.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": "Produto não encontrado",
                "quantity": item.quantity,
                "price": None
            })

    span.set_attribute("cache.hits", cache_hits)
    span.set_attribute("cache.misses", cache_misses)

    return jsonify(result)
