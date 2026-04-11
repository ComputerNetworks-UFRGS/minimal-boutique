# backend/seed.py
import requests
import json

# URL do microsserviço de produtos
PRODUCTS_API_URL = "http://products:5001/products/"

# Lista de produtos para adicionar
products_to_seed = [
    {"name": "Tênis Esportivo", "price": 199.90, "description": "Tênis para corrida", "image_url": "https://upload.wikimedia.org/wikipedia/en/7/7b/Addison_Rae_-_Addison.png"},
    {"name": "Camiseta DryFit", "price": 89.90, "description": "Ideal para esportes", "image_url": "https://upload.wikimedia.org/wikipedia/en/7/7b/Addison_Rae_-_Addison.png"},
    {"name": "Relógio de Corrida", "price": 90.92, "description": "Ideal para esportes", "image_url": "https://upload.wikimedia.org/wikipedia/en/7/7b/Addison_Rae_-_Addison.png"},
    {"name": "Whey Protein 500g", "price": 25.12, "description": "Dieta e nutrição", "image_url": "https://upload.wikimedia.org/wikipedia/en/7/7b/Addison_Rae_-_Addison.png"}
]

def seed_products():
    headers = {'Content-Type': 'application/json'}
    

    for product in products_to_seed:
        try:
            response = requests.post(PRODUCTS_API_URL, data=json.dumps(product), headers=headers)
            
            # Verifica se a requisição foi bem-sucedida (código de status 201 Created)
            if response.status_code == 201:
                print(f"Produto '{product['name']}' adicionado com sucesso.")
            else:
                print(f"Erro ao adicionar o produto '{product['name']}'.")
                print(f"Status Code: {response.status_code}")
                print(f"Resposta: {response.text}")
        
        except requests.exceptions.ConnectionError as e:
            print(f"Erro de conexão: Não foi possível conectar à API de produtos em {PRODUCTS_API_URL}")
            print("Verifique se os contêineres Docker estão em execução.")
            print(f"Detalhes: {e}")
            break # Interrompe o script se não conseguir conectar

if __name__ == "__main__":
    seed_products()