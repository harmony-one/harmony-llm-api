from flask_restx import Namespace, Resource, fields 
from http import HTTPStatus
from .auth_helper import AuthHelper
from flask import request, jsonify, make_response, current_app as app
from res import EngMsg as msg
from flask_jwt_extended import get_jwt, jwt_required, get_jwt_identity
import logging

api = Namespace('auth', description=msg.API_NAMESPACE_LLMS_DESCRIPTION)

token_response = api.model('TokenResponse', {
    'access_token': fields.String(required=True, description='New JWT access token'),
    'refresh_token': fields.String(required=True, description='New JWT refresh token'),
    'token_type': fields.String(required=True, description='Token type', default='Bearer')
})

error_response = api.model('ErrorResponse', {
    'error': fields.String(required=True, description='Error message'),
    'error_code': fields.String(required=False, description='Error code for client handling')
})

auth_service = AuthHelper()

@api.route('/nonce')
class NonceHandler(Resource):
    
    def post(self):
        try:
            data = request.get_json()
            address = data.get('address')
              
            if not address:
                return jsonify({"error": "Address is required"}), 400
            app.logger.info(f'handling nonce request for address {address}')
            # Get or create sign in request
            sign_in = auth_service.get_sign_in_request(address)
            if not sign_in:
                sign_in = auth_service.create_sign_in_request(address)
                
            return jsonify({
                "nonce": sign_in.nonce,
                "address": sign_in.address
            })
              
        except Exception as e:
            logging.error(f"Error generating nonce: {str(e)}")
            return api.marshal({
                'error': "Failed to generate nonce",
                'error_code': 'NONCE_FAILED'
            }, error_response), HTTPStatus.INTERNAL_SERVER_ERROR

@api.route('/verify')
class VerifyHandler(Resource):
    def post(self):
        """Verify wallet signature and issue tokens"""
        try:
            data = request.get_json()
            logging.debug(f"Received verification data: {data}")
            
            address = data.get('address')
            signature = data.get('signature')
            
            if not address or not signature:
                return {'error': 'Address and signature required'}, 400
            
            app.logger.info(f'handling verify request for address {address}')
            logging.debug(f"Looking for sign in request for address: {address}")
            
            # Get sign in request
            sign_in = auth_service.get_sign_in_request(address)
            if not sign_in:
                return {'error': 'No sign in request found'}, 404
            
            logging.debug(f"Found sign in request with nonce: {sign_in.nonce}")
            
            # Verify signature
            if not auth_service.verify_signature(address, signature, sign_in.nonce):
                return {'error': 'Invalid signature'}, 401
            
            logging.debug("Signature verified successfully")
            # Get or create user
            user = auth_service.get_or_create_user(address)
            logging.debug(f"User retrieved/created: {user.id}")
            
            # Generate tokens
            access_token, refresh_token = auth_service.generate_tokens(user.id)
            logging.debug("Tokens generated successfully")
            
            # Delete used sign in request
            auth_service.delete_sign_in_request(address)
            
            response_data = {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'user': {
                    'id': str(user.id),  # Convert to string to ensure JSON serialization
                    'address': user.address,
                    'username': user.username
                }
            }
            
            logging.debug("Preparing response data")
            return response_data
            
        except Exception as e:
            logging.error(f"Authentication error: {str(e)}", exc_info=True)
            return api.marshal({
                'error': "Authentication failed",
                'error_code': 'VERIFY_FAILED'
            }, error_response), HTTPStatus.INTERNAL_SERVER_ERROR

@api.route('/refresh')
class RefreshHandler(Resource):
    @api.doc(security='refresh_token')
    @api.response(200, 'Successfully refreshed tokens', token_response)
    @api.response(401, 'Invalid or expired refresh token', error_response)
    @api.response(500, 'Internal server error', error_response)
    @jwt_required(refresh=True)
    def post(self):
        """Refresh access token using a valid refresh token"""
        try:
            # Get user_id from identity
            user_id = get_jwt_identity()
            # Get additional claims
            claims = get_jwt()
            jti = claims.get('jti')

            if not user_id or not jti:
                return {
                    'error': 'Invalid token claims', 
                    'error_code': 'INVALID_CLAIMS'
                }, 401
            app.logger.info(f'handling refresh request')
            # Validate JTI
            if not auth_service.validate_token_jti(jti, int(user_id)):
                return {
                    'error': 'Invalid or revoked token', 
                    'error_code': 'INVALID_TOKEN'
                }, 401

            # Revoke the old refresh token
            auth_service.revoke_token(jti)
            
            # Generate new tokens
            access_token, refresh_token = auth_service.generate_tokens(int(user_id))
            
            return api.marshal({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer'
            }, token_response), HTTPStatus.OK
        
        except Exception as e:
            logging.error(f"Token refresh error: {str(e)}")
            return api.marshal({
                'error': 'Failed to refresh token',
                'error_code': 'REFRESH_FAILED'
            }, error_response), HTTPStatus.INTERNAL_SERVER_ERROR

