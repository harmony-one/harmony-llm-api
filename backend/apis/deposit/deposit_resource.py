# apis/payment/deposit_resource.py
import asyncio
import threading
from flask_restx import Resource, Namespace, fields
from flask import request, current_app as app
from web3 import Web3
from models import db
from .deposit_helper import deposit_helper
from ..auth import require_jwt
from models import Transactions
from datetime import datetime
from config import config
# const contractAbi = require('./abi/HarmonyLLMPayment.json');

api = Namespace('deposit', description='Deposit operations')

deposit_verify_model = api.model('DepositVerify', {
    'transaction_hash': fields.String(required=True, description='Transaction hash to verify')
})

deposit_info_model = api.model('DepositInfo', {
    'deposit_address': fields.String(description='Contract address for deposits'),
    'minimum_deposit': fields.Float(description='Minimum deposit amount in ONE'),
    'current_balance': fields.Float(description='Current contract balance in ONE'),
    'instructions': fields.String(description='Deposit instructions')
})

async def run_deposit_monitoring():
    async def deposit_callback(deposit_data):
        try:
            # Use application context
            with app.app_context():
                # Check if transaction already exists
                existing_tx = Transactions.query.filter_by(
                    tx_hash=deposit_data['transaction_hash']
                ).first()
                
                if existing_tx:
                    app.logger.info(f"Transaction {deposit_data['transaction_hash']} already processed")
                    return

                # Record deposit in database
                transaction = Transactions(
                    user_address=deposit_data['user_address'],
                    type='DEPOSIT',
                    amount=deposit_data['amount'],
                    tx_hash=deposit_data['transaction_hash'],
                    status='COMPLETED',
                    created_at=deposit_data['timestamp']
                )
                db.session.add(transaction)
                db.session.commit()
                app.logger.info(f"Processed deposit: {deposit_data['transaction_hash']}")
        except Exception as e:
            app.logger.error(f"Error in deposit callback: {e}")
            db.session.rollback()

    await deposit_helper.start_monitoring(deposit_callback)

def start_background_monitoring():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(run_deposit_monitoring())
    except Exception as e:
        app.logger.error(f"Error in monitoring thread: {e}")
    finally:
        loop.close()

# CHANGED: Initialize monitoring when the application starts
def init_deposit_monitoring(app):
    with app.app_context():
        thread = threading.Thread(target=start_background_monitoring)
        thread.daemon = True
        thread.start()
        app.logger.info("Deposit monitoring started")

def cleanup_deposit_monitoring():
    if deposit_helper:
        deposit_helper.stop_monitoring()
    
    global _monitor_thread
    if _monitor_thread and _monitor_thread.is_alive():
        _monitor_thread.join(timeout=5)
        _monitor_thread = None

@api.route('')
class DepositResource(Resource):
    @require_jwt
    @api.marshal_with(deposit_info_model)
    def get(self):
        try:
            min_deposit = deposit_helper.get_minimum_deposit()
            current_balance = deposit_helper.get_contract_balance()
            
            return {
                'deposit_address': deposit_helper.get_deposit_address(),
                'minimum_deposit': min_deposit,
                'current_balance': current_balance,
                'instructions': f'Send at least {min_deposit} ONE tokens to this address. Include gas fees!'
            }
        except Exception as e:
            app.logger.error(f"Error getting deposit info: {e}")
            api.abort(500, f"Error getting deposit information: {str(e)}")

    @require_jwt
    @api.expect(deposit_verify_model)
    def post(self):
        """Verify a deposit transaction"""
        try:
            tx_hash = request.json.get('transaction_hash')
            if not tx_hash:
                return {'error': 'Transaction hash required'}, 400

            # CHANGED: Added validation for transaction hash format
            if not Web3.is_hex(tx_hash) or len(tx_hash) != 66:  # '0x' + 64 hex chars
                return {'error': 'Invalid transaction hash format'}, 400

            result = deposit_helper.verify_deposit(tx_hash)
            
            if result['success']:
                # Record in database
                transaction = Transactions(
                    user_id=request.user_id,  # From JWT
                    user_address=result['user_address'],  # CHANGED: Added user_address
                    type='DEPOSIT',
                    amount=float(result['amount']),
                    tx_hash=tx_hash,
                    status='COMPLETED',
                    created_at=datetime.utcnow()
                )
                db.session.add(transaction)
                db.session.commit()
                
                return {
                    'status': 'success',
                    'amount': float(result['amount']),
                    'user_address': result['user_address']
                }
            
            return {'error': result['error']}, 400
            
        except Exception as e:
            app.logger.error(f"Error processing deposit verification: {e}")
            return {'error': f"Error processing deposit: {str(e)}"}, 500

# Start deposit monitoring when app starts
# @api.on_startup
# async def start_deposit_monitoring():
#     async def deposit_callback(deposit_data):
#         # Record deposit in database
#         transaction = Transactions(
#             user_address=deposit_data['user_address'],
#             type='DEPOSIT',
#             amount=deposit_data['amount'],
#             tx_hash=deposit_data['transaction_hash'],
#             status='COMPLETED',
#             created_at=deposit_data['timestamp']
#         )
#         db.session.add(transaction)
#         db.session.commit()

#     await deposit_helper.start_monitoring(deposit_callback)