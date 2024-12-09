# auth/middleware.py
from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
import config as app_config
import logging

def require_jwt(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            jwt_identity = get_jwt_identity()
            if not jwt_identity:
                return jsonify({"msg": "Invalid JWT token"}), 401
            return f(*args, **kwargs)
        except:
            return jsonify({"msg": "JWT authentication required"}), 401
    return decorated

def require_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token:
            token = token.split(' ')[1]
            if token in app_config.config.API_KEYS:
                return f(*args, **kwargs)
        token = request.cookies.get('session_token')
        if token and token in app_config.config.API_KEYS:
            return f(*args, **kwargs)
        return jsonify({"msg": "Invalid API token"}), 401
    return decorated

def require_any_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        logging.info("Starting authentication check")
        
        if request.endpoint in ['auth_nonce_handler', 'auth_verify_handler', 'auth_refresh_handler']:
            return f(*args, **kwargs)

        # Try JWT first
        try:
            verify_jwt_in_request()
            logging.info("JWT verification successful")
            return f(*args, **kwargs)
        except Exception as e:
            logging.info(f"JWT verification failed: {str(e)}")
            pass

        # Try API token
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(' ')[1]
                if token in app_config.config.API_KEYS:
                    logging.info("API key verification successful")
                    return f(*args, **kwargs)
                logging.info("Invalid API key")
            except Exception as e:
                logging.info(f"API key verification error: {str(e)}")
                pass

        # Try session token
        session_token = request.cookies.get('session_token')
        if session_token and session_token in app_config.config.API_KEYS:
            logging.info("Session token verification successful")
            return f(*args, **kwargs)

        logging.info("All authentication methods failed")
        return {"message": "Authentication required"}, 401
    return decorated
