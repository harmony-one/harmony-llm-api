import os
import sys
import json
import requests
from eth_account import Account
from eth_account.messages import encode_defunct
from datetime import datetime, timedelta
from test_config import TestConfig

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as app_config


class AuthTester:
    def __init__(self, base_url=TestConfig.ENDPOINT):
        self.base_url = base_url
        self.session = requests.Session()
        self.account = Account.create()
        print(f"Test wallet address: {self.account.address}")

    def get_nonce(self):
        response = self.session.post(
            f"{self.base_url}/auth/nonce",
            json={"address": self.account.address}
        )
        return response.json()['nonce']
    
    def sign_and_verify(self, nonce):
        message = f"I'm signing my one-time nonce: {nonce}"
        message_encoded = encode_defunct(text=message)
        signed_message = Account.sign_message(
            message_encoded,
            private_key=self.account.key
        )
        
        response = self.session.post(
            f"{self.base_url}/auth/verify-token",
            json={
                "address": self.account.address,
                "signature": signed_message.signature.hex()
            }
        )
        return response.json()

    def refresh_token(self, refresh_token):
        response = self.session.post(
            f"{self.base_url}/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        return response.json()

    def run_auth_test(self):
        try:
            print("\n=== Running Authentication Tests ===")
            
            print("\nTesting nonce generation...")
            nonce = self.get_nonce()
            print(f"Nonce received: {nonce}")
            
            print("\nTesting sign and verify...")
            auth_result = self.sign_and_verify(nonce)
            print(f"Received access token: {auth_result['access_token'][:30]}...")
            if 'access_token' not in auth_result:
                raise Exception("Authentication failed!")
            print("Authentication successful!")
            
            print("\nTesting token refresh...")
            refresh_result = self.refresh_token(auth_result['refresh_token'])
            print("Token refresh successful!")
            
            return auth_result
            
        except Exception as e:
            print(f"Authentication test failed: {str(e)}")
            return None