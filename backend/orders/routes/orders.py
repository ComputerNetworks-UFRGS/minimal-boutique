from flask import Blueprint, jsonify, request
from models import Order, OrderItem
from database import db
import requests
from opentelemetry import trace
import datetime
from sqlalchemy.orm import joinedload

tracer = trace.get_tracer(__name__)

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

# ===============================================================
# CACHE
# ===============================================================
product_cache = {}
CACHE_TTL_SECONDS = 300  # 5 minutos

def get_product_from_cache(product_id):
    """Retorna produto do cache se ainda for válido"""
    # Tenta pegar item da cache e retorna vazio se produto não for encontrado
    entry = product_cache.get(product_id)
    if not entry:
        return None

    # Verifica expiração do tempo e se expirou retorna vazio
    if (datetime.datetime.now() - entry["timestamp"]).total_seconds() > CACHE_TTL_SECONDS:
        del product_cache[product_id]
        return None

    # Se encontrou e dado está dentro do prazo de validade, retorna ele
    return entry["data"]

def fetch_product(product_id):
    """Busca o produto no cache ou via requisição HTTP"""
    # Tenta cache
    cached = get_product_from_cache(product_id)
    if cached:
        return cached, True  # True indica que veio do cache

    # Se não está no cache, busca no serviço products
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
    # Configura o tracing
    span = trace.get_current_span()

    # Pega os dados da requisição
    data = request.json
    user_id = data.get('user_id')
    total = data.get('total')
    items = data.get('items')

    # Se falta algum dado, avisa o usuário
    if not all([user_id, total, items]):
        return jsonify({'error': 'Dados incompletos para criar o pedido'}), 400
    
    # Coloca os dados da requisição no span
    span.set_attribute("user.id", user_id)
    span.set_attribute("total", total)
    span.set_attribute("number.of.items", len(items))

    # Cria o pedido e salva ele no banco de dados
    order = Order(user_id=user_id, total=total)
    db.session.add(order)
    db.session.flush() 
    # Salva id do pedido no span
    span.set_attribute("order.id", order.id)

    # Adiciona cada item do pedido na entrada do banco de dados do pedido
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

    # Configura tracing
    span = trace.get_current_span()

    # Verifica se pedido está atrelado a um usuário, caso não retorna mensagem de erro
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id é obrigatório'}), 400
    
    #Adiciona o id do usuário no span
    span.set_attribute("user.id", user_id)

    # Parâmetros opcionais de paginação (default: últimos 20)
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))

    # Busca pedidos baseados no limite imposto acima
    orders = (
        Order.query
        .options(joinedload(Order.items))
        .filter_by(user_id=user_id)
        .order_by(Order.id.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    # Adiciona dados ao span
    span.set_attribute("number.of.orders", len(orders))
    span.set_attribute("pagination.limit", limit)
    span.set_attribute("pagination.offset", offset)

    # Variáveis para cache
    result = []
    cache_hits = 0
    cache_misses = 0

    # Busca os dados dos produtos dos pedidos para visualização
    for order in orders:
        items_data = []
        # Para cada item em cada pedido busca dados do item e salva em items_data
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

        # Salva os dados do pedido completo, agora com dados dos itens para visualização e retorno da requisição
        result.append({
            'id': order.id,
            'total': order.total,
            'status': order.status,
            'items': items_data
        })

    # Salva dados da cache no span
    span.set_attribute("cache.hits", cache_hits)
    span.set_attribute("cache.misses", cache_misses)

    return jsonify(result)


# ===============================================================
# CONFIRM PAYMENT
# ===============================================================
@orders_bp.route('/<int:order_id>/confirm_payment', methods=['POST'])
def confirm_payment(order_id):
    # Configuração do tracing
    span = trace.get_current_span()

    # Busca pedido no banco de dados e caso não encontre retorna mensagem de erro
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Pedido não encontrado"}), 404
    
    # Salva a id do pedido no span
    span.set_attribute("order.id", order.id)
    
    # Muda status do pedido para pago
    order.status = 'paid'
    # Salva novo status do pedido no span
    span.set_attribute("payment.status", "paid")
    # Salva banco de dados
    db.session.commit()

    return jsonify({"message": "Pagamento do pedido confirmado com sucesso"}), 200


# ===============================================================
# DELETE ORDER
# ===============================================================
@orders_bp.route('/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):

    # Configura tracing
    span = trace.get_current_span()

    # Busca pedido baseado no id
    order = Order.query.get(order_id)

    # Se não encontrou pedido, retorna erro
    if not order:
        return jsonify({"error": "Pedido não encontrado"}), 404
    # Salva id do pedido no span
    span.set_attribute("order.id", order.id)
    
    # Se tentar cancelar pedidos que já foram pagos retorna mensagem de erro
    if order.status != 'pending':
        return jsonify({"error": "Apenas pedidos pendentes podem ser cancelados"}), 400
    
    # Libera todos os itens do pedido que até então estavam com o estoque reservado
    for item in order.items:
        try:
            requests.post(
                f"http://products:5001/products/{item.product_id}/release",
                json={'quantity': item.quantity},
                timeout=3
            )
        except requests.exceptions.RequestException as e:
            print(f"ERRO CRÍTICO: Falha ao liberar estoque para product_id {item.product_id}. Detalhes: {e}")
    
    # Deleta o item do banco de dados e salva
    db.session.delete(order)
    db.session.commit()

    return jsonify({"message": "Pedido cancelado com sucesso"}), 200
