from flask import Blueprint, request, jsonify, session
from models import db, User
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# ===============================================================
# USER REGISTER
# ===============================================================
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json

    # Verifica o email e a senha passados pelo usuário para registro
    email = data.get('email')
    password = data.get('password')

    # Telemetria
    span = trace.get_current_span()


    # Se o email ou a senha não forem passados, retorna mensagem de erro
    if not email or not password:
        return jsonify({"error": "Email e senha são obrigatórios"}), 400

    # Telemetria do email e senha
    span.set_attribute("email", email)
    span.set_attribute("password", password)

    # Verifica se usuário já existe no banco de dados de registros
    if User.query.filter_by(username=data['email']).first():
        # Caso exista retorna mensagem de erro
        return jsonify({"error": "Usuário já existe"}), 400

    # Cria usuário no banco de dados e salva ele
    user = User(username=email, password=password)
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'Usuário Criado com sucesso'}), 201






# ===============================================================
# LOGIN
# ===============================================================
@auth_bp.route('/login', methods=['POST'])
def login():

    # Inicialização da telemetria
    span = trace.get_current_span()

    #Faz verificação de email e senha para ver se credenciais estão registradas e são válidas
    data = request.json
    user = User.query.filter_by(username=data['email'], password = data['password']).first()
    
    #Caso não estejam, retorna mensagem de erro
    if not user:
        return jsonify({'error': 'Credenciais inválidas'}), 401
    
    #Telemetria do usuário e email
    span.set_attribute("user.id", user.id)
    span.set_attribute("email", data['email'])

    #Cria sessão do usuário 
    session['user_id'] = user.id

    return jsonify({'message': 'Login realizado com sucesso'})






# ===============================================================
# LOGOUT
# ===============================================================
@auth_bp.route('/logout', methods=['POST'])
def logout():
    
    #Telemetria
    span = trace.get_current_span()
    span.set_attribute("user.id", session['user_id'])
    
    #Exclusão da sessão do usuário
    session.pop('user_id', None)
    
    return jsonify({'message':'Logout realizado com sucesso'})






# ===============================================================
# GET EMAIL
# ===============================================================
@auth_bp.route('/user', methods=['GET'])
def get_user():
    user_id = session.get('user_id')

    if not user_id:
        return jsonify(None)
    
    user = User.query.get(user_id)

    if not user: return jsonify(None)

    return jsonify({'email': user.username})
    