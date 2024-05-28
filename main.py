from flask import Flask, jsonify, request
from flask_httpauth import HTTPTokenAuth
from flask_session import Session
from flask_cors import CORS
from apis import api
from models import db
from res import CustomError
import config as app_config
import os
import logging

API_KEYS = app_config.config.API_KEYS
app = Flask(__name__)
auth = HTTPTokenAuth(scheme='Bearer')
    
# my_key_manager.fetch_api_key_loader(lambda: API_KEYS)
# print(my_key_manager.fetch_api_key_loader( .create_api_key_loader())

#  .init_app() . fetch_api_key_loader()

app.config['SECRET_KEY']=app_config.config.SECRET_KEY
app.config['SESSION_PERMANENT'] = True
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:'
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# if app_config.config.ENV == 'development':
#     app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:'
# else:
#     path = app_config.config.CHROMA_SERVER_PATH 
#     os.makedirs(os.path.dirname(path), exist_ok=True)
#     # f = open(os.path.join(app_config.config.CHROMA_SERVER_PATH, "app.db"), 'w')
#     app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///" +os.path.join(app_config.config.CHROMA_SERVER_PATH, "app.db") # chroma.sqlite3
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.update(SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_SECURE=True)

sess = Session()
api.init_app(app)
sess.init_app(app)
db.init_app(app)


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
@auth.login_required
def can_activate():
    logging.debug('checking api key')

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


# python main.py