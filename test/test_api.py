import sys
import os
import requests
import json
from eth_account import Account
from eth_account.messages import encode_defunct
from sqlalchemy import create_engine

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as app_config


ENDPOINT = 'http://127.0.0.1:5000' #'https://harmony-llm-api-dev.fly.dev' # 'http://127.0.0.1:5000'):
DATABASE_URL = app_config.config.DATABASE_URL

class APITester:
    def __init__(self, base_url=ENDPOINT):
        self.base_url = base_url
        self.session = requests.Session()
        
        # Create a test account if you don't have a real wallet
        self.account = Account.create()
        print(f"Test wallet address: {self.account.address}")

        if DATABASE_URL:
            try:
                self.engine = create_engine(DATABASE_URL)
                print("Database connection established")
            except Exception as e:
                print(f"Failed to connect to database: {str(e)}")
                self.engine = None
        else:
            print("DATABASE_URL not set")
            self.engine = None
            
    

    def check_user_in_database(self, address):
        """Query the database to check if user exists"""
        if not self.engine:
            print("Database connection not available")
            return None
            
        try:
            with self.engine.connect() as connection:
                result = connection.execute(
                    f"SELECT * FROM users WHERE address = '{address.lower()}'"
                ).fetchone()
                
                if result:
                    print("\nUser found in database:")
                    print(f"ID: {result[0]}")
                    print(f"Address: {result[1]}")
                    print(f"Username: {result[2]}")
                    return result
                else:
                    print("\nUser not found in database")
                    return None
        except Exception as e:
            print(f"Database query failed: {str(e)}")
            return None
        
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
    
    
    def generate_image(self, access_token, prompt, size="1024x1024", num_images=1, quality="standard", style="vivid"):
        print(f"Using access token: {access_token[:10]}...") # Add this debug line
        headers = {"Authorization": f"Bearer {access_token}"}
        print(f"Headers: {headers}") # Add this debug line
        
        response = self.session.post(
            f"{self.base_url}/openai/generate-image",
            headers=headers,
            json={
                "prompt": prompt,
                "size": size,
                "n": num_images,
                "quality": quality,
                "style": style
            }
        )
        print("\nDALL-E Response:", json.dumps(response.json(), indent=2))
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
            
             # Check database for user
            print("\nChecking database for user...")
            user_result = self.check_user_in_database(self.account.address)
            print("user result", user_result)
            
            # Store tokens
            access_token = auth_result['access_token']
            refresh_token = auth_result['refresh_token']
            
            # Wait for user input to test refresh
            input("\nPress Enter to test token refresh...")
            
             # Test DALL-E image generation
            print("\nTesting DALL-E image generation...")
            dalle_result = self.generate_image(access_token, "kid playing with a ball")
            print("DALL-E result:", dalle_result)

            # Refresh tokens
            refresh_result = self.refresh_tokens(refresh_token)
            
            print('result', refresh_result)
            print("\nTest completed successfully!")
            
        except Exception as e:
            print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    tester = APITester()
    tester.run_full_test()