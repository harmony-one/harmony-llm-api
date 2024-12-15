# auth/middleware.py
from functools import wraps
from flask import g, request, jsonify, current_app as app
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
import jwt
import config as app_config

def require_jwt(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            jwt_identity = get_jwt_identity()
            if not jwt_identity:
                return jsonify({"msg": "Invalid JWT token"}), 401
            
            class UserContext:
                def __init__(self, id):
                    self.id = id
            
            g.auth_type = 'jwt'
            g.is_jwt_user = True
            g.user = UserContext(id=int(jwt_identity))
            
            try:
                return f(*args, **kwargs)
            except Exception as e:
                app.logger.error(f"Endpoint execution error: {str(e)}")
                raise
        
        except Exception as e:
            app.logger.error(f"JWT authentication error: {str(e)}")
            return jsonify({"msg": "JWT authentication required"}), 401
    
    return decorated

def require_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_successful = False
        token = request.headers.get('Authorization')
        
        try:
            if token:
                token = token.split(' ')[1]
                if token in app_config.config.API_KEYS:
                    auth_successful = True
                    
            if not auth_successful:
                token = request.cookies.get('session_token')
                if token and token in app_config.config.API_KEYS:
                    auth_successful = True
                    
            if not auth_successful:
                return jsonify({"msg": "Invalid API token"}), 401
                
            g.auth_type = 'token'
            g.is_jwt_user = False
            
            try:
                return f(*args, **kwargs)
            except Exception as e:
                app.logger.error(f"Endpoint execution error: {str(e)}")
                raise
                
        except Exception as e:
            app.logger.error(f"Token authentication error: {str(e)}")
            return jsonify({"msg": "Invalid API token"}), 401
            
    return decorated

def require_any_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Reset auth context
        g.auth_type = None
        g.user = None
        g.is_jwt_user = False
        
        auth_successful = False
        auth_header = request.headers.get('Authorization')

        # Try JWT first
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            
            class UserContext:
                def __init__(self, id):
                    self.id = id

            g.auth_type = 'jwt'
            g.is_jwt_user = True
            g.user = UserContext(id=int(user_id))
            auth_successful = True  
            app.logger.debug(f"JWT verification successful")
            return f(*args, **kwargs)
        except Exception as e:
            app.logger.debug(f"JWT verification failed, trying API token")
            
            # Try API token
            if auth_header:
                try:
                    token = auth_header.split(' ')[1]
                    if token in app_config.config.API_KEYS:
                        g.auth_type = 'token'
                        g.is_jwt_user = False
                        auth_successful = True
                        app.logger.debug(f"API token-based verification successful")
                        return f(*args, **kwargs)
                except Exception as e:
                    app.logger.error(f"API key verification error: {str(e)}")

        if not auth_successful:
            return {"message": "Authentication required"}, 401
        
        try:
            return f(*args, **kwargs)
        except Exception as e:
            app.logger.error(f"Endpoint execution error: {str(e)}")
            raise
            
    return decorated