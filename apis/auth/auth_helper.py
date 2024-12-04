from flask_jwt_extended import create_access_token, create_refresh_token
from eth_account.messages import encode_defunct
from web3 import Web3
from typing import Optional, Tuple
import logging
import uuid
from datetime import datetime, timedelta
from models.auth import SignInRequest, User, Token
from models import db
from config import config

class AuthHelper:
    def __init__(self):
        self.config = config
        self.w3 = Web3(Web3.HTTPProvider(config.WEB3_PROVIDER_URL))
    
    def get_sign_in_request(self, address: str) -> Optional[SignInRequest]:
        """Get existing sign in request for address"""
        return SignInRequest.query.filter_by(
            address=address.lower()
        ).first()
    
    def create_sign_in_request(self, address: str) -> SignInRequest:
        """Create new sign in request with nonce"""
        # Delete any existing requests
        SignInRequest.query.filter_by(address=address.lower()).delete()
        
        nonce = uuid.uuid4().int % 1000000  # Generate 6-digit nonce
        request = SignInRequest(
            address=address.lower(),
            nonce=nonce
        )
        db.session.add(request)
        db.session.commit()
        return request
    
    def verify_signature(self, address: str, signature: str, nonce: int) -> bool:
        """Verify wallet signature matches address"""
        try:
            message = f"I'm signing my one-time nonce: {nonce}"
            logging.debug(f"Verifying signature for message: {message}")
            encoded_message = encode_defunct(text=message)
            recovered_address = self.w3.eth.account.recover_message(
                encoded_message,
                signature=signature
            )
            logging.debug(f"Recovered address: {recovered_address}")
            logging.debug(f"Original address: {address}")
            return recovered_address.lower() == address.lower()
        except Exception as e:
            logging.error(f"Signature verification failed: {str(e)}", exc_info=True)
            return False
    
    def delete_sign_in_request(self, address: str):
        """Delete sign in request after use"""
        SignInRequest.query.filter_by(address=address.lower()).delete()
        db.session.commit()
    
    def get_or_create_user(self, address: str) -> User:
        """Get existing user or create new one"""
        user = User.query.filter_by(address=address.lower()).first()
        if not user:
            username = User.generate_username(address)
            # Check if username exists
            while User.query.filter_by(username=username).first():
                username = address.lower()
            
            user = User(address=address.lower(), username=username)
            db.session.add(user)
            db.session.commit()
        return user
    

    def validate_token_jti(self, jti: str, user_id: int) -> bool:
        """Validate that the JTI exists and belongs to the user"""
        token = Token.query.filter_by(
            jti=jti,
            user_id=user_id
        ).first()
        return token is not None
    
    def generate_tokens(self, user_id: int) -> Tuple[str, str]:
        """Generate access and refresh tokens"""
        jti = str(uuid.uuid4())
        
        # Store token record
        token = Token(user_id=user_id, jti=jti)
        db.session.add(token)
        db.session.commit()
        
        # Convert user_id to string for JWT identity
        payload = {
            'user_id': str(user_id),  # Convert to string
            'jti': jti
        }
        
        access_token = create_access_token(
            identity=str(user_id),  # Use string user_id as identity
            additional_claims={'jti': jti}  # Add jti as additional claim
        )
        
        refresh_token = create_refresh_token(
            identity=str(user_id),  # Use string user_id as identity
            additional_claims={'jti': jti}  # Add jti as additional claim
        )
        
        return access_token, refresh_token
    
    def revoke_token(self, jti: str):
        """Revoke a token by deleting it"""
        Token.query.filter_by(jti=jti).delete()
        db.session.commit()