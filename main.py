# main.py
from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_httpauth import HTTPTokenAuth
from flask_jwt_extended import JWTManager, get_jwt_identity
from flask_session import Session
from flask_cors import CORS
from apis import api
from models import db
from res import CustomError
from datetime import timedelta
import config as app_config
import logging

auth = HTTPTokenAuth(scheme='Bearer')

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['JWT_SECRET_KEY'] = app_config.config.SECRET_KEY
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    app.config['SECRET_KEY'] = app_config.config.SECRET_KEY
    app.config['SESSION_PERMANENT'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = app_config.config.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config.update(SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_SECURE=True)
    app.config['UPLOAD_FOLDER'] = 'uploads/'

    # Initialize extensions
    db.init_app(app)
    api.init_app(app)
    Session().init_app(app)
    jwt = JWTManager(app)
    migrate = Migrate(app, db)
    CORS(app)


    @app.route('/')
    def index():
        return 'received!', 200

    @app.route('/health')
    def health():
        return "I'm healthy", 200

    @app.errorhandler(CustomError)
    def handle_custom_error(error):
        response = {
            "error": {
                "status_code": error.error_code,
                "message": error.message
            }
        }
        return jsonify(response), error.error_code

    # Register additional routes
    from routes import register_additional_routes
    register_additional_routes(app)

    return app

# Create the Flask application instance
app = create_app()

if __name__ == '__main__':
    if app_config.config.ENV != 'development':
        from waitress import serve
        serve(app, host="0.0.0.0", port=8080)
    else:
        app.run(debug=True)