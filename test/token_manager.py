# token_manager.py
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

class TokenManager:
    def __init__(self, cache_file=None):
        # Get the directory where token_manager.py is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # If no cache_file specified, create it in the current directory
        if cache_file is None:
            cache_file = os.path.join(current_dir, '.test_tokens.json')
        
        self.cache_file = cache_file
        print(f"Token cache file location: {self.cache_file}")
        self.tokens = self._load_tokens()

    def _load_tokens(self):
        try:
            if os.path.exists(self.cache_file):
                print(f"Loading tokens from: {self.cache_file}")
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    # Check if refresh token is still valid
                    if datetime.fromisoformat(data['refresh_expiry']) > datetime.now():
                        print("Found valid cached tokens")
                        return data
                    else:
                        print("Cached tokens have expired")
            else:
                print("No token cache file found")
        except Exception as e:
            print(f"Error loading tokens: {e}")
        return None

    def save_tokens(self, access_token, refresh_token):
        try:
            # Save tokens with expiry times
            data = {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'refresh_expiry': (datetime.now() + timedelta(days=1)).isoformat(),
                'created_at': datetime.now().isoformat()
            }
            
            print(f"Saving tokens to: {self.cache_file}")
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.tokens = data
            print("Tokens saved successfully")
            
            # Verify the file was created
            if os.path.exists(self.cache_file):
                print(f"Token cache file created successfully at: {self.cache_file}")
            else:
                print("Warning: Token file was not created!")
                
        except Exception as e:
            print(f"Error saving tokens: {e}")

    def get_tokens(self):
        if self.tokens:
            print(f"Returning cached token: {self.tokens['access_token'][:30]}...")
            print("\nToken details from cache:")
            print(f"Access token: {self.tokens['access_token'][:50]}...")
            print(f"Created at: {self.tokens['created_at']}")
            print(f"Refresh expiry: {self.tokens['refresh_expiry']}")
        if not self.tokens:
            print("No tokens available in memory")
        return self.tokens if self.tokens else None

    def clear_tokens(self):
        if os.path.exists(self.cache_file):
            print(f"Removing token cache file: {self.cache_file}")
            os.remove(self.cache_file)
            print("Token cache file removed")
        self.tokens = None