import asyncio
from datetime import datetime
from typing import Callable, Dict, Any
import logging
from blockchain import web3_deposit

class DepositHelper:
    def __init__(self):
        """Initialize DepositHelper with Web3DepositService"""
        self.web3_service = web3_deposit
        self.last_block_checked = None

    async def start_monitoring(self, callback: Callable):
        """Start monitoring for deposit events"""
        self._monitoring = True
        logging.info("Starting deposit monitoring...")
        
        while self._monitoring:
            try:
                current_block = self.web3_service.w3.eth.block_number
                
                if self.last_block_checked is None:
                    # Start from current block on first run
                    self.last_block_checked = current_block
                    logging.info(f"Initial block set to {current_block}")
                    continue
                
                if current_block > self.last_block_checked:
                    logging.debug(f"Checking blocks {self.last_block_checked + 1} to {current_block}")
                    
                    # Get deposits between last checked block and current block
                    events = self.web3_service.get_past_deposits(
                        from_block=self.last_block_checked + 1,
                        to_block=current_block
                    )
                    
                    if events:
                        logging.info(f"Found {len(events)} new deposit events")
                        for event_data in events:
                            await self.handle_deposit_event(event_data, callback)
                    
                    self.last_block_checked = current_block
                    
            except Exception as e:
                logging.error(f"Error in deposit monitoring loop: {e}")
            
            await asyncio.sleep(12)  # Poll every 12 seconds (average block time)

    async def handle_deposit_event(self, deposit_data: Dict, callback: Callable):
        """Handle incoming deposit event"""
        try:
            logging.info(f"Processing deposit event: {deposit_data['transaction_hash']}")
            await callback(deposit_data)
            logging.info(f"Successfully processed deposit: {deposit_data['transaction_hash']}")
        except Exception as e:
            logging.error(f"Error handling deposit event {deposit_data.get('transaction_hash', 'unknown')}: {e}")
            # Don't raise the exception to keep the monitoring loop running

    def get_deposit_address(self) -> str:
        """Get contract address for deposits"""
        return self.web3_service.contract.address

    def get_minimum_deposit(self) -> float:
        """Get minimum deposit amount in ONE"""
        return float(self.web3_service.get_min_deposit())

    def verify_deposit(self, tx_hash: str) -> Dict:
        """Verify a deposit transaction"""
        return self.web3_service.verify_transaction(tx_hash)

    def create_deposit_transaction(self, from_address: str, amount: float) -> Dict:
        """Create a deposit transaction"""
        return self.web3_service.create_deposit_transaction(from_address, amount)

    def get_contract_balance(self) -> float:
        """Get current contract balance in ONE"""
        return float(self.web3_service.get_balance())

deposit_helper = DepositHelper()