from flask import Flask, jsonify, request
from flask_httpauth import HTTPTokenAuth
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from flask_session import Session
from flask_cors import CORS
from apis import api
from models import db
from res import CustomError
from datetime import timedelta
import config as app_config
import os
import logging

auth = HTTPTokenAuth(scheme='Bearer')

app = Flask(__name__)

app.config    
API_KEYS = app_config.config.API_KEYS
app.config['JWT_SECRET_KEY'] = app_config.config.SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
jwt = JWTManager(app)

app.config['SECRET_KEY']=app_config.config.SECRET_KEY
app.config['SESSION_PERMANENT'] = True
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.update(SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_SECURE=True)

UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

sess = Session()
api.init_app(app)
sess.init_app(app)
db.init_app(app)

def verify_jwt_token():
    try:
        jwt_identity = get_jwt_identity()
        return bool(jwt_identity)
    except:
        return False
    

def verify_auth():
    # Check for JWT first
    if verify_jwt_token():
        return True
    
    # Fall back to API key check
    token = request.headers.get('Authorization')
    if token:
        token = token.split(' ')[1]
        if token in API_KEYS:
            return True
    
    # Check for session token in cookies
    token = request.cookies.get('session_token')
    if token and token in API_KEYS:
        return True
    
    return False


@auth.verify_token
def verify_token(token):
    token = request.headers.get('Authorization')
    if token:
        token = token.split(' ')[1]
    
    # for web client calls that uses HttpOnly cookies
    if not token:
        token = request.cookies.get('session_token')

    if token and token in API_KEYS:
        return True

    return False

app.app_context().push()
db.create_all()

CORS(app)
logging.info(f'****** APP Enviroment={app_config.config.ENV} *******')

@app.before_request
def auth_middleware():
    # Skip auth for specific endpoints
    if request.endpoint in ['auth_nonce_handler', 'auth_verify_handler', 'auth_refresh_handler']:
        return
    logging.debug('checking authentication')

    if not verify_auth():
        return jsonify({"msg": "Invalid or missing authentication"}), 401

    logging.debug('authentication successful')


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

if __name__ == '__main__':
    # from waitress import serve
    # serve(app, host="0.0.0.0", port=8080) # listen='0.0.0.0:8081') # port=8080, host="0.0.0.0",
    if app_config.config.ENV != 'development':
        from waitress import serve
        serve(app, host="0.0.0.0", port=8080) 
    else:
        app.run(debug=True)
