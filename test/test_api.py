import requests
import json
from eth_account import Account
from eth_account.messages import encode_defunct
import os

class APITester:
    def __init__(self, base_url='http://127.0.0.1:5000'):
        self.base_url = base_url
        self.session = requests.Session()
        
        # Create a test account if you don't have a real wallet
        self.account = Account.create()
        print(f"Test wallet address: {self.account.address}")
    
    def get_nonce(self):
        print('fco::: getNonce', self.account.address)
        response = self.session.post(
            f"{self.base_url}/auth/nonce",
            json={"address": self.account.address}
        )
        print("\nNonce Response:", json.dumps(response.json(), indent=2))
        return response.json()['nonce']
    
    def sign_and_verify(self, nonce):
        # Create the message
        message = f"I'm signing my one-time nonce: {nonce}"
        print(f"\nSigning message: {message}")
        
        # Create the signable message
        message_encoded = encode_defunct(text=message)
        
        # Sign the message
        signed_message = Account.sign_message(
            message_encoded,
            private_key=self.account.key
        )
        
        print(f"Generated signature: {signed_message.signature.hex()}")
        
        # Verify signature
        response = self.session.post(
            f"{self.base_url}/auth/verify",
            json={
                "address": self.account.address,
                "signature": signed_message.signature.hex()
            }
        )
        print("\nVerify Response:", response.text)  # Print raw response text
        try:
            return response.json()
        except Exception as e:
            print(f"Error parsing response: {str(e)}")
            return None
    
    def refresh_tokens(self, refresh_token):
        response = self.session.post(
            f"{self.base_url}/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        print("\nRefresh Response:", json.dumps(response.json(), indent=2))
        return response.json()
    
    def run_full_test(self):
        try:
            print("Starting API test flow...")
            
            # Get nonce
            nonce = self.get_nonce()
            
            # Sign and verify
            auth_result = self.sign_and_verify(nonce)
            if 'access_token' not in auth_result:
                print("Authentication failed!")
                return
            
            # Store tokens
            access_token = auth_result['access_token']
            refresh_token = auth_result['refresh_token']
            
            # Wait for user input to test refresh
            input("\nPress Enter to test token refresh...")
            
            # Refresh tokens
            refresh_result = self.refresh_tokens(refresh_token)
            
            print('result', refresh_result)
            print("\nTest completed successfully!")
            
        except Exception as e:
            print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    tester = APITester()
    tester.run_full_test()