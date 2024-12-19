# api_tester.py
import json
import requests
from test_config import TestConfig
from token_manager import TokenManager
from auth_tester import AuthTester


class APITester:
    def __init__(self, base_url=TestConfig.ENDPOINT):
        self.base_url = base_url
        self.session = requests.Session()
        self.token_manager = TokenManager()
        
    def ensure_valid_tokens(self):
        """Get valid tokens, either from cache or by authenticating"""
        tokens = self.token_manager.get_tokens()
        
        if not tokens:
            print("No valid tokens found in cache, authenticating...")
            auth_tester = AuthTester(self.base_url)
            auth_result = auth_tester.run_auth_test()
            if auth_result:
                self.token_manager.save_tokens(
                    auth_result['access_token'],
                    auth_result['refresh_token']
                )
                tokens = self.token_manager.get_tokens()
            else:
                raise Exception("Authentication failed")
                
        return tokens['access_token'], tokens['refresh_token']

    
    def test_gemini_api(self):
        tokens = self.token_manager.get_tokens()
        if not tokens:
            print("No tokens available")
            return None

        access_token = tokens['access_token']
        
        print(f"Using token: {access_token[:30]}...")
        
        if not access_token.startswith('Bearer '):
            access_token = f"Bearer {access_token}"
            
        headers = {"Authorization": access_token}
    
        try:
            response = self.session.post(
                f"{self.base_url}/vertex/completions/gemini",
                headers=headers,
                json={
                    "model": "gemini-1.5-pro-latest",
                    "stream": True,
                    "max_tokens": 100,
                    "system": "Short answers",
                    "messages": [
                        {
                            "parts": {"text": "Hello, how can I help you today?"},
                            "role": "model"
                        },
                        {
                            "parts": {"text": "Can you explain quantum computing in simple terms?"},
                            "role": "user"
                        }
                    ],
                },
                stream=True
            )
            
            # Add status code check
            print(f"Gemini request status code: {response.status_code}")
            if response.status_code != 200:
                print(f"Error response content: {response.text}")
                
            response.raise_for_status()
            
            print("\nStreaming response from Gemini:")
            for line in response.iter_lines():
                if line:
                    # Decode the line from bytes to string
                    decoded_line = line.decode('utf-8')
                    
                    # Skip SSE prefix if present
                    if decoded_line.startswith('data: '):
                        decoded_line = decoded_line[6:]
                    
                    try:
                        # Parse the JSON chunk
                        chunk = json.loads(decoded_line)
                        print(json.dumps(chunk, indent=2))
                    except json.JSONDecodeError:
                        print(f"Could not parse line: {decoded_line}")
                        continue
            
            return {"status": "completed"}
        
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
            return {"error": str(e)}
        except Exception as e:
            print(f"Error processing stream: {str(e)}")
            return {"error": str(e)}

    def test_dalle_api(self, headers):
        print("Testing DALL-E image generation...")
        try:
            response = self.session.post(
                f"{self.base_url}/openai/generate-image",
                headers=headers,
                json={
                    "prompt": "A cute robot painting a landscape",
                    "size": "1024x1024",
                    "n": 1,
                    "model": "dall-e-3"
                }
            )
            
            print(f"DALL-E request status code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error response content: {response.json()}")
                return {"error": response.text}
                
            response.raise_for_status()
            
            result = response.json()
            print("\nDALL-E API Response:")
            print(json.dumps(result, indent=2))
            
            if 'images' in result:
                print(f"\nGenerated {len(result['images'])} images:")
                for i, image_url in enumerate(result['images'], 1):
                    print(f"Image {i}: {image_url}")
                    
            return {"status": "completed", "data": result}
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
            return {"error": str(e)}
        except Exception as e:
            print(f"Error processing response: {str(e)}")
            return {"error": str(e)}

    def run_api_tests(self):
        """Run API tests with automatic token handling"""
        try:
            access_token, refresh_token = self.ensure_valid_tokens()
            
            # Set up headers with token
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Run your API tests here
            # print("\nTesting Gemini API...")
            # self.test_gemini_api()
            
            print("\nTesting DALL-E API...")
            self.test_dalle_api(headers)
            
        except Exception as e:
            print(f"Error during API tests: {e}")
            # Optionally clear tokens if they might be invalid
            self.token_manager.clear_tokens()

