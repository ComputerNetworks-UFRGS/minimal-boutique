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
CACHE_TTL_SECONDS = 300  # Tempo que os dados se mantem na cache

def get_product_from_cache(product_id):
    # Verifica se o produto está na cache
    entry = product_cache.get(product_id)
    # Se não estiver retorna vazio
    if not entry:
        return None
    # Se estiver, verifica se o dado estourou o tempo limite de permanência na cache
    if (datetime.datetime.now() - entry["timestamp"]).total_seconds() > CACHE_TTL_SECONDS:
        # Caso sim, deleta o produto da cache e retorna vazio
        del product_cache[product_id]
        return None
    #Se não estourou o tempo, retorna o dado armazenado na cache
    return entry["data"]

def fetch_product(product_id):
    #Busca o produto, na cache e no sistema de produtos
    cached = get_product_from_cache(product_id)

    # Se produto estava na cache, retorna ele
    if cached:
        return cached, True  # True = veio do cache

    # Senão busca no catálogo de produtos
    try:
        # Faz a requisição para o serviço de produtos com a id do produto selecionado
        response = requests.get(f"{PRODUCTS_API_URL}/{product_id}", timeout=3)

        # Se recebe ok, salva dados do produto e coloca ele na cacha, depois retorna o produto
        if response.status_code == 200:
            product_data = response.json()
            product_cache[product_id] = {
                "data": product_data,
                "timestamp": datetime.datetime.now()
            }
            return product_data, False
        
        #Senão avisa falha ao buscar o produto e retorna vazio
        else:
            print(f" Falha ao buscar produto {product_id}: {response.status_code}")
            return None, False
    # Tratamento de exceção
    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Falha ao buscar produto {product_id}: {e}")
        return None, False


# ===============================================================
# ADD TO CART
# ===============================================================
@cart_bp.route('/', methods=['POST'])
def add_to_cart():

    # Verificação de autenticação do usuário
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Usuário não encontrado'}), 401

    # Configuração da telemetria e adicionado ao span dado do id de usuário
    span = trace.get_current_span()
    span.set_attribute("user.id", user_id)

    # Extração dos dados do produto e da quantidade a ser adicionada do request
    data = request.json
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    #Adicionando dados da requisição ao span
    span.set_attribute("product.id", product_id)
    span.set_attribute("quantity", quantity)

    try:
        # Tenta reservar a quantidade de itens daquele produto para o usuário atual
        reserve_response = requests.post(f"{PRODUCTS_API_URL}/{product_id}/reserve", json={'quantity': quantity})

        #Se der erro, retorna mensagem de erro para a requisição e os dados do erro
        if reserve_response.status_code != 200:
            error_data = reserve_response.json()
            return jsonify({"error": error_data.get("error", "Não foi possível reservar o produto")}), reserve_response.status_code
    # Tratamento de exceção
    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Erro de comunicação com o serviço de produtos', 'details': str(e)}), 503

    # Procura se o item já está no carrinho
    item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()

    # Caso esteja, apenas aumenta a quantidade dele
    if item:
        item.quantity += quantity
    
    # Caso não, adiciona o item ao carrinho
    else:
        item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(item)
    
    # Commit do banco de dados e adicionando quantidade de itens reservados ao span
    db.session.commit()
    span.set_attribute("stock.items", item.quantity)
    return jsonify({"message": "Item adicionado ao carrinho"}), 201


# ===============================================================
# REMOVE ITEM FROM CART
# ===============================================================
@cart_bp.route('/<int:item_id>', methods=['DELETE'])
def remove_from_cart(item_id):

    #Verificação de autenticação do usuário
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    # Configuração de telemetria e adicionando o atributo de id do usuário ao span
    span = trace.get_current_span()
    span.set_attribute("user.id", user_id)
    
    # Busca do item a ser deletado no carrinho
    item = CartItem.query.filter_by(id=item_id, user_id=user_id).first()
    if not item:
        return jsonify({"error": "Item não encontrado"}), 404

    # Salva os dados do produto para liberar no estoque
    product_id = item.product_id
    quantity_to_release = item.quantity

    # Deleta o item do carrinho e salva o banco de dados
    db.session.delete(item)
    db.session.commit()

    # Salva no span os atributos 
    span.set_attribute("product.id", product_id)
    span.set_attribute("deleted.quantity", quantity_to_release)

    # Libera os itens no estoque que estava reservados para este usuário
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

    # Validação da autenticação do usuário
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id é obrigatório"}), 400

    # Configuração de telemetria e registro do user id no span
    span = trace.get_current_span()
    span.set_attribute("user.id", user_id)
    

    try:
        # Procura o carrinho do usuário e delete ele do banco de dados
        CartItem.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return jsonify({"message": "Carrinho limpo com sucesso"}), 200
    # Tratamento de exceção
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Falha ao limpar o carrinho", "details": str(e)}), 500


# ===============================================================
# GET CART
# ===============================================================
@cart_bp.route('/', methods=['GET'])
def get_cart():

    # Validação da autenticação do usuário
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Usuário não encontrado'}), 401

    # Configuração da telemetria e registro do user id no span
    span = trace.get_current_span()
    span.set_attribute("user.id", user_id)

    # Busca no banco de dados o carrinho do usuário
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return jsonify([])

    # Separa produto por produto do carrinho
    product_ids = [item.product_id for item in cart_items]

    #Registra o número de produtos no carrinho no span
    span.set_attribute("cart.product.count", len(product_ids))

    # Cria variáveis para as informações dos produtos e os hits e misses da cache
    result = []
    cache_hits = 0
    cache_misses = 0

    for item in cart_items:

        # Pega as informações de um item, e registra se foi um cache miss ou hit
        product_data, from_cache = fetch_product(item.product_id)
        if from_cache:
            cache_hits += 1
        else:
            cache_misses += 1

        # Se foi retornado um produto, salva as informações dele no array
        if product_data:
            result.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product_data.get('name'),
                "quantity": item.quantity,
                "price": product_data.get('price')
            })

        # Caso contrário apenas cria uma versão sem os dados para devolver
        else:
            result.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": "Produto não encontrado",
                "quantity": item.quantity,
                "price": None
            })

    # Salva no span os hits e misses da cache
    span.set_attribute("cache.hits", cache_hits)
    span.set_attribute("cache.misses", cache_misses)

    return jsonify(result)
