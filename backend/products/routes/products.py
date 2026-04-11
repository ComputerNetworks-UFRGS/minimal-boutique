from flask import Blueprint, jsonify, request
from models import Product
from database import db
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


products_bp = Blueprint('products', __name__, url_prefix = '/products')
#Rotas de dados de produtos
@products_bp.route('/', methods=['GET'])
def list_products():
    span = trace.get_current_span()
    products = Product.query.filter(Product.stock>0).all()
    span.set_attribute("number.of.products", len(products))
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "price": p.price,
        "description": p.description,
        "image_url": p.image_url,
        "stock": p.stock
        } for p in products])

@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    span = trace.get_current_span()
    product = Product.query.get(product_id)
    if product is None:
        return jsonify({'error': 'Produto não encontrado'}), 404
    span.set_attribute("product.id", product.id)
    return jsonify({
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "description": product.description,
        "image_url": product.image_url,
        "stock": product.stock
    })

#Rotas para excluir e adicionar diretamente
@products_bp.route('/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    span = trace.get_current_span()
    product = Product.query.get(product_id)
    if product is None:
        return jsonify({'error': 'Producto não encontrado'}), 404
    span.set_attribute("product.id", product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message':'Producto removido com sucesso'}), 200

@products_bp.route('/', methods=['POST'])
def add_product():
    data = request.json
    product = Product(
        name=data['name'], 
        price=data['price'],
        description=data.get('description'),
        image_url=data.get('image_url'),
        stock=data.get('stock', 0)
        )
    db.session.add(product)
    db.session.commit()
    return jsonify({"id": product.id}), 201

#Rotas para reserva e liberação de produto

@products_bp.route('/<int:product_id>/reserve', methods=['POST'])
def reserve_stock(product_id):
    span = trace.get_current_span()
    span.set_attribute(" product.id", product_id)
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Produto não encontrado"}), 404
    
    quantity_to_reserve = request.json.get('quantity', 0)
    if quantity_to_reserve <= 0:
        return jsonify({"error":"Quantidade inválida"}), 400
    
    if product.stock >= quantity_to_reserve:
        product.stock -= quantity_to_reserve
        db.session.commit()
        return jsonify({"message": "Estoque reservado com sucesso", "new_stock": product.stock}), 200
    else:
        product.stock += 50000
        db.session.commit()
        # return jsonify({"error": "Estoque insuficiente"}), 409


@products_bp.route('/<int:product_id>/release', methods=['POST'])
def release_stock(product_id):
    span = trace.get_current_span()
    span.set_attribute("product.id", product_id)

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Produto não encontrado"}), 404
    
    quantity_to_release = request.json.get('quantity', 0)
    if quantity_to_release <= 0:
        return jsonify({"error": "Quantidade inválida"}), 400

    product.stock += quantity_to_release
    db.session.commit()
    return jsonify({"message": "Estoque liberado com sucesso", "new_stock": product.stock}), 200


@products_bp.route('/batch', methods=['POST'])
def get_products_batch():
    span=trace.get_current_span()

    data = request.get_json()
    if not data or 'ids' not in data:
        return jsonify({"error": "Corpo da requisição deve conter uma lista 'ids'"}), 400
    
    ids = data['ids']

    span.set_attribute("batch.request.size", len(ids))

    products = Product.query.filter(Product.id.in_(ids)).all()
    span.set_attribute("batch.response.size", len(products))

    return jsonify([
        {
            "id" : p.id,
            "name" : p.name,
            "price" : p.price,
            "description" : p.description,
            "image_url": p.image_url,
            "stock": p.stock
        }
        for p in products
    ])











# from flask import Blueprint, jsonify
# from database import get_db_connection


# products_bp = Blueprint('products', __name__, url_prefix='/products')

# @products_bp.route('/', methods=['GET'])
# def list_products():
#     conn = get_db_connection()
#     products = conn.execute('SELECT * FROM products').fetchall()
#     conn.close()
#     return jsonify([dict(row) for row in products])

