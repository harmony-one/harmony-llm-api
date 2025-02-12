from web3 import Web3
from eth_account import Account
from datetime import datetime
from ..web3_config import CURRENT_NETWORK, get_contract_address
from ..abis import HARMONY_LLM_PAYMENT_ABI
import logging
from decimal import Decimal

class Web3Deposit:
    def __init__(self, contract_address, contract_abi, rpc_url):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=contract_abi
        )
        
    def get_min_deposit(self):
        """Get the minimum deposit amount required"""
        try:
            min_deposit = self.contract.functions.minDeposit().call()
            return Web3.from_wei(min_deposit, 'ether')
        except Exception as e:
            logging.error(f"Error getting minimum deposit: {e}")
            raise

    def get_balance(self):
        """Get the current contract balance"""
        try:
            balance = self.contract.functions.getContractBalance().call()
            return Web3.from_wei(balance, 'ether')
        except Exception as e:
            logging.error(f"Error getting contract balance: {e}")
            raise

    def create_deposit_transaction(self, from_address, amount_in_ether):
        """Create a deposit transaction"""
        try:
            amount_in_wei = Web3.to_wei(amount_in_ether, 'ether')
            
            # Get minimum deposit
            min_deposit = self.contract.functions.minDeposit().call()
            if amount_in_wei < min_deposit:
                raise ValueError(f"Amount below minimum deposit of {Web3.from_wei(min_deposit, 'ether')} ETH")
            
            # Prepare transaction
            tx = {
                'from': from_address,
                'to': self.contract.address,
                'value': amount_in_wei,
                'gas': 100000,  # Estimated gas limit
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(from_address),
            }
            
            return tx
            
        except Exception as e:
            logging.error(f"Error creating deposit transaction: {e}")
            raise

    def verify_transaction(self, tx_hash):
        """Verify a deposit transaction"""
        try:
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] != 1:
                return {'success': False, 'error': 'Transaction failed'}
            
            logs = receipt['logs']
            for log in logs:
                # Try to decode the event
                try:
                    decoded_event = self.contract.events.Deposit().process_log(log)
                    return {
                        'success': True,
                        'user_address': decoded_event.args.user,
                        'amount': Web3.from_wei(decoded_event.args.amount, 'ether'),
                        'transaction_hash': tx_hash.hex() if isinstance(tx_hash, bytes) else tx_hash
                    }
                except Exception as e:
                    continue
            
            return {'success': False, 'error': 'No deposit event found'}
            
        except Exception as e:
            logging.error(f"Error verifying transaction: {e}")
            return {'success': False, 'error': str(e)}

    def get_past_deposits(self, from_block, to_block='latest'):
        """Get past deposit events"""
        try:
            if isinstance(from_block, int):
                from_block = hex(from_block)
            if isinstance(to_block, int):
                to_block = hex(to_block)
            
            # Get the event signature hash properly
            deposit_event = self.contract.events.Deposit
            
            # Get logs with proper filtering
            logs = self.w3.eth.get_logs({
                'address': self.contract.address,
                'fromBlock': from_block,
                'toBlock': to_block,
                'topics': [deposit_event.event_abi['signature']]
            })
            
            # Process logs into deposit events
            events = []
            for log in logs:
                try:
                    decoded_event = deposit_event().process_log(log)
                    events.append(self.parse_deposit_event(decoded_event))
                except Exception as e:
                    logging.error(f"Error processing log: {e}")
                    continue
            
            return events
            
        except Exception as e:
            logging.error(f"Error getting past deposits: {e}")
            return []

    def parse_deposit_event(self, event):
        """Parse deposit event data"""
        try:
            return {
                'user_address': event.args.user,
                'amount': float(Web3.from_wei(event.args.amount, 'ether')),
                'transaction_hash': event.transactionHash.hex(),
                'block_number': event.blockNumber,
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logging.error(f"Error parsing deposit event: {e}")
            raise

# Initialize the contract instance
harmony_llm_payment_contract = get_contract_address('HarmonyLLMPaymentSimple')
web3_deposit = Web3Deposit(
    contract_address=harmony_llm_payment_contract,
    contract_abi=HARMONY_LLM_PAYMENT_ABI,
    rpc_url=CURRENT_NETWORK.get('url')
)