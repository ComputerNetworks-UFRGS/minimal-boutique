from flask import Flask
from routes.products import products_bp
from database import init_db, db
from models import Product
from flask_cors import CORS
from telemetry import configure_telemetry
import json
import os


app = Flask(__name__)
app.secret_key = 'secret_key_products'

CORS(app, supports_credentials=True)

app.register_blueprint(products_bp)

init_db(app)

with app.app_context():
    print("Verificando e populando o banco de dados de produtos...")
    try:
        json_path = os.path.join(app.root_path, 'products.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            products_to_seed = json.load(f)

        for p_data in products_to_seed:
            product = Product.query.filter_by(name=p_data['name']).first()
            if product:
                # Product exists, check stock
                if product.stock <= 0:
                    print(f"Repondo estoque para o produto: {product.name}")
                    product.stock = p_data['stock']
                else:
                    # If you want to *add* to the existing stock instead of replacing it,
                    # you can change the line above to:
                    # product.stock += p_data['stock']
                    print(f"Produto {product.name} já tem estoque, adicionando mais.")
                    product.stock += p_data['stock'] # This will add to the stock.
            else:
                # Product does not exist, create new one
                print(f"Criando novo produto: {p_data['name']}")
                new_product = Product(**p_data)
                db.session.add(new_product)

        db.session.commit()
        print("Sincronização do banco de dados de produtos concluída.")

    except FileNotFoundError:
        print(f"ERRO CRÍTICO: O arquivo 'products.json' não foi encontrado no caminho esperado: {json_path}")
    except Exception as e:
        print(f"ERRO CRÍTICO ao carregar dados de produtos: {e}")
        db.session.rollback()


configure_telemetry(app, "products")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)