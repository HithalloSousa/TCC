from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = 'secret'
    #QUAL BANCO DE DADOS QUE EU QUERO TRABALHAR(SQLITE EM ARQUIVO).
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"  
    #ESCONDER/IGNORAR O WARNING DO TRACK_MODIFICATIONS(CONSOLE).     
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False             

    db.init_app(app)
    login_manager.init_app(app)

    from app import routes
    routes.init_app(app)

    return app