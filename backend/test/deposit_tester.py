import json
import requests
from blockchain import CURRENT_NETWORK
from test_config import TestConfig
from token_manager import TokenManager
from auth_tester import AuthTester
from web3 import Web3
from blockchain import get_contract_address, CURRENT_RPC_URL, HARMONY_LLM_PAYMENT_ABI

class DepositTester:
    def __init__(self, base_url=TestConfig.ENDPOINT):
        self.base_url = base_url
        self.session = requests.Session()
        self.token_manager = TokenManager()
        self.w3 = Web3(Web3.HTTPProvider(CURRENT_RPC_URL))
        
        # Initialize contract
        contract_address = get_contract_address('HarmonyLLMPaymentSimple')
        contract_abi = HARMONY_LLM_PAYMENT_ABI
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=contract_abi
        )

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

    def test_get_deposit_info(self, headers):
        """Test getting deposit address and info"""
        print("\nTesting GET /deposit endpoint...")
        try:
            response = self.session.get(
                f"{self.base_url}/deposit",
                headers=headers
            )
            
            print(f"Status code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error response: {response.text}")
                return {"error": response.text}
            
            result = response.json()
            print("\nDeposit Info Response:")
            print(json.dumps(result, indent=2))
            
            # CHANGED: Additional validations for new fields
            required_fields = ['deposit_address', 'minimum_deposit', 'current_balance']
            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                print(f"WARNING: Missing required fields: {missing_fields}")
            
            # Verify contract address matches
            if result['deposit_address'].lower() != self.contract.address.lower():
                print("WARNING: Returned deposit address doesn't match contract address!")
                
            # CHANGED: Verify minimum deposit matches contract
            try:
                contract_min_deposit = Web3.from_wei(
                    self.contract.functions.minDeposit().call(),
                    'ether'
                )
                if abs(float(result['minimum_deposit']) - float(contract_min_deposit)) > 0.0001:
                    print("WARNING: Returned minimum deposit doesn't match contract value!")
            except Exception as e:
                print(f"WARNING: Couldn't verify minimum deposit: {e}")
            
            return {"status": "completed", "data": result}
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
            return {"error": str(e)}

    def test_verify_deposit(self, tx_hash, headers):
        """Test verifying a deposit transaction"""
        print(f"\nTesting POST /deposit endpoint with tx_hash: {tx_hash}")
        try:
            response = self.session.post(
                f"{self.base_url}/deposit",
                headers=headers,
                json={"transaction_hash": tx_hash}
            )
            
            print(f"Status code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error response: {response.text}")
                return {"error": response.text}
            
            result = response.json()
            print("\nVerification Response:")
            print(json.dumps(result, indent=2))
            
            # CHANGED: Enhanced verification checks
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            if receipt['status'] != 1:
                print("WARNING: Transaction failed on-chain but API returned success!")
                
            # CHANGED: Verify Deposit event
            deposit_events = self.contract.events.Deposit().process_receipt(receipt)
            if not deposit_events:
                print("WARNING: No Deposit event found in transaction!")
            else:
                event = deposit_events[0]
                if float(result['amount']) != float(Web3.from_wei(event.args.amount, 'ether')):
                    print("WARNING: Returned amount doesn't match event amount!")
            
            return {"status": "completed", "data": result}
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
            return {"error": str(e)}

    def make_test_deposit(self, amount_in_one, private_key):
        """Helper function to make a test deposit transaction"""
        print(f"\nMaking test deposit of {amount_in_one} ONE...")
        try:
            # Convert ONE to Wei
            amount_in_wei = Web3.to_wei(amount_in_one, 'ether')
            
            # Get the account from private key
            account = self.w3.eth.account.from_key(private_key)
            
            # CHANGED: Check minimum deposit
            min_deposit = self.contract.functions.minDeposit().call()
            if amount_in_wei < min_deposit:
                raise ValueError(f"Amount below minimum deposit of {Web3.from_wei(min_deposit, 'ether')} ONE")
            
            chain_id = self.w3.eth.chain_id

            # Build the transaction
            tx = {
                'from': account.address,
                'to': self.contract.address,
                'value': amount_in_wei,
                'nonce': self.w3.eth.get_transaction_count(account.address),
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': chain_id
            }
            
            # Sign and send the transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key)
            
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            # Wait for transaction to be mined
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # CHANGED: Verify the deposit event
            deposit_events = self.contract.events.Deposit().process_receipt(receipt)
            if not deposit_events:
                raise Exception("Deposit transaction successful but no Deposit event found")
            
            print(f"Deposit transaction successful: {receipt['transactionHash'].hex()}")
            return receipt['transactionHash'].hex()
            
        except Exception as e:
            print(f"Error making deposit: {str(e)}")
            return None

    def run_deposit_tests(self, headers=None):
        """Run all deposit-related tests"""
        try:
            # Get authentication tokens
            access_token, refresh_token = self.ensure_valid_tokens()
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Test getting deposit info
            print("\nTesting deposit info retrieval...")
            deposit_info = self.test_get_deposit_info(headers)
            
            if headers:
                # CHANGED: Get minimum deposit from contract
                min_deposit = float(Web3.from_wei(
                    self.contract.functions.minDeposit().call(),
                    'ether'
                ))
                
                # Make a test deposit with minimum amount plus some extra for safety
                test_amount = min_deposit * 1.1  # 10% more than minimum
                print(f"\nMaking test deposit of {test_amount} ONE...")
                test_private_key = CURRENT_NETWORK.get('private_key')
                tx_hash = self.make_test_deposit(test_amount, test_private_key)
                
                if tx_hash:
                    # Verify the deposit
                    print("\nVerifying deposit...")
                    verification = self.test_verify_deposit(tx_hash, headers)
                    
                    return {
                        "deposit_info": deposit_info,
                        "test_deposit": {
                            "tx_hash": tx_hash,
                            "amount": test_amount
                        },
                        "verification": verification
                    }
            
            return {"deposit_info": deposit_info}
            
        except Exception as e:
            print(f"Error during deposit tests: {e}")
            self.token_manager.clear_tokens()
            return {"error": str(e)}
