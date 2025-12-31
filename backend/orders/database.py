from flask_sqlalchemy import SQLAlchemy 
import os

from flask import Flask

db = SQLAlchemy()


def init_db(app: Flask):
    # Pega a URL do banco do environment (configurada no Deployment)
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/meubanco')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_size": 80,       # conexões fixas no pool
        "max_overflow": 40,    # extras além do pool
        "pool_timeout": 120,    # espera até liberar uma conexão
        "pool_recycle": 180   # recicla conexões a cada 30 min
        
    }

    db.init_app(app)

    # Cria as tabelas no PostgreSQL
    with app.app_context():
        db.create_all()