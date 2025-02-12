import asyncio
from datetime import datetime
from typing import Callable, Dict, Any
import logging
from blockchain import web3_deposit
from res import Web3ConnectionError
from web3.exceptions import TransactionNotFound, BlockNotFound, InvalidAddress
from web3.types import BlockData
from urllib3.exceptions import MaxRetryError, NewConnectionError
from .deposit_monitor import DepositMonitor

class DepositHelper:
    def __init__(self):
        """Initialize DepositHelper with Web3DepositService"""
        self.web3_service = web3_deposit
        self.monitor = DepositMonitor()

    async def start_monitoring(self, callback: Callable):
        """Start monitoring for deposit events"""
        await self.monitor.start(callback)


    async def stop_monitoring(self):
        """Stop monitoring for deposit events"""
        await self.monitor.stop()

    def get_deposit_address(self) -> str:
        """Get contract address for deposits"""
        return self.web3_service.contract.address

    def get_minimum_deposit(self) -> float:
        """Get minimum deposit amount in ONE"""
        return float(self.web3_service.get_min_deposit())

    def verify_deposit(self, tx_hash: str) -> Dict:
        """Verify a deposit transaction"""
        try:
            if not self.web3_service.w3.is_connected():
                raise Web3ConnectionError("Unable to connect to Ethereum node")
                
            result = self.web3_service.verify_transaction(tx_hash)
            if not result:
                raise ValueError("Invalid or unconfirmed transaction")
                
            return result
            
        except Web3ConnectionError as e:
            logging.error(f"Web3 connection error during verification: {str(e)}")
            raise
        except TransactionNotFound:
            logging.error(f"Transaction not found: {tx_hash}")
            return {'success': False, 'error': 'Transaction not found'}
        except Exception as e:
            logging.error(f"Error verifying deposit: {str(e)}")
            return {'success': False, 'error': str(e)}

    def create_deposit_transaction(self, from_address: str, amount: float) -> Dict:
        """Create a deposit transaction"""
        return self.web3_service.create_deposit_transaction(from_address, amount)

    def get_contract_balance(self) -> float:
        """Get current contract balance in ONE"""
        try:
            if not self.web3_service.w3.is_connected():
                raise Web3ConnectionError("Unable to connect to Ethereum node")
                
            return float(self.web3_service.get_balance())
        except (Web3ConnectionError, ConnectionRefusedError) as e:
            logging.error(f"Connection error getting balance: {str(e)}")
            raise Web3ConnectionError("Unable to fetch contract balance")
        except Exception as e:
            logging.error(f"Error getting contract balance: {str(e)}")
            raise

deposit_helper = DepositHelper()