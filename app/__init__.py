from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)

    # 설정
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///school.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')

    # 확장 초기화
    db.init_app(app)
    jwt.init_app(app)

    # 라우트 등록
    from app.routes import main
    app.register_blueprint(main)

    # DB 테이블 생성
    with app.app_context():
        from app import models
        db.create_all()

    return app