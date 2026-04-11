from flask import Blueprint, request, jsonify, session
from models import db, User
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json

    email = data.get('email')
    password = data.get('password')

    span = trace.get_current_span()

    if not email or not password:
        return jsonify({"error": "Email e senha são obrigatórios"}), 400
    span.set_attribute("email", email)
    span.set_attribute("password", password)

    if User.query.filter_by(username=data['email']).first():
        return jsonify({"error": "Usuário já existe"}), 400

    user = User(username=email, password=password)
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'Usuário Criado com sucesso'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():

    span = trace.get_current_span()
    data = request.json
    user = User.query.filter_by(username=data['email'], password = data['password']).first()
    
    if not user:
        return jsonify({'error': 'Credenciais inválidas'}), 401
    
    span.set_attribute("user.id", user.id)
    span.set_attribute("email", data['email'])
    session['user_id'] = user.id

    return jsonify({'message': 'Login realizado com sucesso'})

@auth_bp.route('/logout', methods=['POST'])
def logout():
    span = trace.get_current_span()
    span.set_attribute("user.id", session['user_id'])
    
    session.pop('user_id', None)
    
    return jsonify({'message':'Logout realizado com sucesso'})


@auth_bp.route('/user', methods=['GET'])
def get_user():
    user_id = session.get('user_id')

    if not user_id:
        return jsonify(None)
    
    user = User.query.get(user_id)

    if not user: return jsonify(None)

    return jsonify({'email': user.username})
    