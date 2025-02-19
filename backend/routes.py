# routes.py
from flask import jsonify, render_template
from flask_httpauth import HTTPTokenAuth

auth = HTTPTokenAuth(scheme='Bearer')

def register_additional_routes(app):
    """
    Register additional routes beyond the core ones defined in create_app()
    This keeps route registration modular and organized
    """
    
    @app.route('/api/v1/balance')
    @auth.login_required
    def get_balance():
        # Example additional route
        return jsonify({"balance": 100}), 200

    @app.route('/api/v1/transactions')
    @auth.login_required
    def get_transactions():
        # Example additional route
        return jsonify({"transactions": []}), 200

    @app.route('/deposit-page')  # Using deposit-page to avoid conflict with /deposit API
    def deposit_page():
        return render_template('deposit.html')
