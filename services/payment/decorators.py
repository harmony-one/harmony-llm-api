from functools import wraps
from flask import g, request, current_app as app
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from .llm_manager import llm_models_manager
from models import Users

def check_balance(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            g.is_jwt_user = True

            user = Users.query.get(int(user_id))
            if not user:
                app.logger.error(f"User not found with ID: {user_id}")
                return {"msg": "User not found"}, 404

            balance = user.get_balance()
            endpoint = request.endpoint
            request_data = request.get_json() if request.is_json else request.form.to_dict()
            
            try:
                estimated_cost = llm_models_manager.estimate_request_cost(endpoint, request_data)
                if balance < estimated_cost:
                    return {
                        "msg": "Insufficient balance",
                        "current_balance": float(balance),
                        "estimated_cost": float(estimated_cost),
                        "additional_funds_needed": float(estimated_cost - balance)
                    }, 402
                    
                g.user = user
                g.balance = balance
                g.estimated_cost = estimated_cost
                
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    app.logger.error(f"Endpoint execution error: {str(e)}")
                    raise
                    
            except Exception as e:
                app.logger.error(f"Error estimating cost: {str(e)}")
                raise
                
        except Exception as e:
            g.is_jwt_user = False
            g.estimated_cost = 0
            
            try:
                return f(*args, **kwargs)
            except Exception as e:
                app.logger.error(f"Endpoint execution error: {str(e)}")
                raise
            
    return decorated