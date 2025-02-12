# web3/auth.py
from eth_account.messages import encode_defunct
from web3 import Web3
from ..web3_config import CURRENT_NETWORK
import logging

class Web3Auth:
    def __init__(self, provider_url: str):
        self.w3 = Web3(Web3.HTTPProvider(provider_url))
    
    def verify_signature(self, address: str, signature: str, nonce: int) -> bool:
        """Verify wallet signature matches address"""
        try:
            message = f"I'm signing my one-time nonce: {nonce}"
            encoded_message = encode_defunct(text=message)
            recovered_address = self.w3.eth.account.recover_message(
                encoded_message,
                signature=signature
            )
            return recovered_address.lower() == address.lower()
        except Exception as e:
            logging.error(f"Signature verification failed: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def normalize_address(address: str) -> str:
        """Normalize Ethereum address to lowercase"""
        return address.lower()


web3_auth = Web3Auth(CURRENT_NETWORK.get('url'))