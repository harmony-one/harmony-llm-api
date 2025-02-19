from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import create_access_token, create_refresh_token
from eth_account.messages import encode_defunct
from typing import Optional, Tuple
import logging
import uuid
from datetime import datetime, timedelta
from models.auth import SignInRequests, Users, Tokens
from models import db
from config import config
from blockchain import web3_auth
class AuthHelper:
    def __init__(self):
        self.config = config
        self.web3_auth = web3_auth
    
    async def get_user(self, address: str) -> Optional[Users]:
        """Get user by address."""
        return Users.query.filter_by(address=address.lower()).first()
    
    async def get_user_by_username(self, username: str) -> Optional[Users]:
        """Get user by username."""
        return Users.query.filter_by(username=username).first()

    async def create_user(self, address: str) -> Users:
        """Create a new user."""
        address = address.lower()
        username = Users.generate_username(address)
        
        if await self.get_user_by_username(username):
            username = address
            
        user = Users(
            address=address,
            username=username
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            return user
        except IntegrityError:
            db.session.rollback()
            raise ValueError("User already exists")
        
    def get_sign_in_request(self, address: str) -> Optional[SignInRequests]:
        """Get existing sign in request for address"""
        return SignInRequests.query.filter_by(
            address=address.lower()
        ).first()
    
    def create_sign_in_request(self, address: str) -> SignInRequests:
        """Create new sign in request with nonce"""
        SignInRequests.query.filter_by(address=address.lower()).delete()
        
        nonce = uuid.uuid4().int % 1000000  # Generate 6-digit nonce
        request = SignInRequests(
            address=address.lower(),
            nonce=nonce
        )
        db.session.add(request)
        db.session.commit()
        return request
    
    def verify_signature(self, address: str, signature: str, nonce: int) -> bool:
        return self.web3_auth.verify_signature(address, signature, nonce)

    def delete_sign_in_request(self, address: str):
        """Delete sign in request after use"""
        SignInRequests.query.filter_by(address=address.lower()).delete()
        db.session.commit()
    
    async def get_or_create_user(self, address: str) -> Users:
        """Get existing user or create new one"""
        user = await self.get_user(address)
        if user:
            return user
            
        try:
            user = await self.create_user(address)
            return user
        except Exception as e:
            db.session.rollback()
            raise e

    def validate_token_jti(self, jti: str, user_id: int) -> bool:
        """Validate that the JTI exists and belongs to the user"""
        token = Tokens.query.filter_by(
            jti=jti,
            user_id=user_id
        ).first()
        return token is not None
    
    def generate_tokens(self, user_id: int) -> Tuple[str, str]:
        """Generate access and refresh tokens"""
        jti = str(uuid.uuid4())
        
        # Store token record
        token = Tokens(user_id=user_id, jti=jti)
        db.session.add(token)
        db.session.commit()
        
        access_token = create_access_token(
            identity=str(user_id),
            additional_claims={
                'jti': jti,
                'type': 'access'
            },
            fresh=False
        )
        
        refresh_token = create_refresh_token(
            identity=str(user_id),
            additional_claims={
                'jti': jti,
                'type': 'refresh'
            }
        )
        
        return access_token, refresh_token
    
    def revoke_token(self, jti: str):
        """Revoke a token by deleting it"""
        Tokens.query.filter_by(jti=jti).delete()
        db.session.commit()