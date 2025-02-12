# api_tester.py
import json
import requests
from test_config import TestConfig
from token_manager import TokenManager

class DeepSeekTester:
    def __init__(self, base_url=TestConfig.ENDPOINT):
        self.base_url = base_url
        self.session = requests.Session()
        self.token_manager = TokenManager()

    def test_deepseek_api(self):
            """Test the DeepSeek API endpoint with streaming and non-streaming requests"""
            # tokens = self.token_manager.get_tokens()
            # if not tokens:
            #     print("No tokens available")
            #     return None

            # access_token = tokens['access_token']
            
            # print(f"Using token: {access_token[:30]}...")
            
            # if not access_token.startswith('Bearer '):
            #     access_token = f"Bearer {access_token}"
                
            # headers = {"Authorization": access_token}

            # Test both streaming and non-streaming requests
            test_cases = [
                {
                    "name": "Streaming request",
                    "payload": {
                        "model": "gpt-3.5-turbo", # "deepseek-chat",
                        "stream": "True",
                        "messages": [
                            {"role": "system", "content": "You are a helpful assistant"},
                            {"role": "user", "content": "Explain quantum computing in simple terms"}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 150
                    },
                    "stream": True
                },
                # {
                #     "name": "Non-streaming request",
                #     "payload": {
                #         "model": "deepseek-chat",
                #         "stream": "False",
                #         "messages": [
                #             {"role": "system", "content": "You are a helpful assistant"},
                #             {"role": "user", "content": "What is artificial intelligence?"}
                #         ],
                #         "temperature": 0.7,
                #         "max_tokens": 150
                #     },
                #     "stream": False
                # }
            ]

            results = []
            
            for test_case in test_cases:
                print(f"\nExecuting {test_case['name']}...")
                try:
                    response = self.session.post(
                        f"{self.base_url}/deepseek/completions",
                        # headers=headers,
                        json=test_case['payload'],
                        stream=test_case['stream']
                    )
                    
                    print(f"DeepSeek request status code: {response.status_code}")
                    
                    if response.status_code != 200:
                        print(f"Error response content: {response.text}")
                        results.append({
                            "test": test_case['name'],
                            "status": "failed",
                            "error": response.text
                        })
                        continue

                    if test_case['stream']:
                        print("\nStreaming response from DeepSeek:")
                        for line in response.iter_lines():
                            if line:
                                decoded_line = line.decode('utf-8')
                                if decoded_line.startswith('data: '):
                                    decoded_line = decoded_line[6:]
                                print(decoded_line)
                        results.append({
                            "test": test_case['name'],
                            "status": "completed"
                        })
                    else:
                        result = response.json()
                        print("\nDeepSeek API Response:")
                        print(json.dumps(result, indent=2))
                        results.append({
                            "test": test_case['name'],
                            "status": "completed",
                            "data": result
                        })

                except requests.exceptions.RequestException as e:
                    print(f"Request failed: {str(e)}")
                    results.append({
                        "test": test_case['name'],
                        "status": "error",
                        "error": str(e)
                    })
                except Exception as e:
                    print(f"Error processing response: {str(e)}")
                    results.append({
                        "test": test_case['name'],
                        "status": "error",
                        "error": str(e)
                    })

            return results