
import asyncio
from datetime import datetime
import logging
from typing import Callable, Dict, Optional
from web3.exceptions import TransactionNotFound
from web3.types import BlockData
from urllib3.exceptions import MaxRetryError, NewConnectionError


class DepositMonitor:
    def __init__(self):
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._connection_healthy = False
        self._last_error_time = None
        self.MAX_ERRORS_BEFORE_DISABLE = 3
        self.error_count = 0

    async def health_check(self):
        """Periodic health check of Web3 connection"""
        while self._monitoring:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.web3_service.w3.eth.block_number
                )
                if not self._connection_healthy:
                    logging.info("Web3 connection restored")
                    self._connection_healthy = True
            except Exception as e:
                if self._connection_healthy:
                    logging.warning(f"Web3 connection lost: {str(e)}")
                    self._connection_healthy = False
            
            await asyncio.sleep(30)

    async def check_web3_connection(self) -> bool:
        """Check if Web3 connection is available"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.web3_service.w3.eth.block_number
            )
            return True
        except (ConnectionRefusedError, MaxRetryError, NewConnectionError) as e:
            if not self._last_error_time or \
               (datetime.now() - self._last_error_time).total_seconds() > 300:  # Log every 5 minutes
                logging.warning(f"Web3 connection unavailable: {str(e)}")
                self._last_error_time = datetime.now()
            return False

    async def start(self, callback: Callable):
        """Start deposit monitoring"""
        if self._monitoring:
            logging.warning("Monitoring already running")
            return

        self._monitoring = True
        self._connection_healthy = False
        
        # Start health check task
        self._health_check_task = asyncio.create_task(self.health_check())
        
        # Start monitoring task
        self._monitor_task = asyncio.create_task(self._monitor_deposits(callback))
        
        logging.info("Deposit monitoring started")

    async def stop(self):
        """Stop deposit monitoring"""
        if not self._monitoring:
            return

        self._monitoring = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None

        logging.info("Deposit monitoring stopped")

    async def _monitor_deposits(self, callback: Callable):
        """Monitor deposits using event subscription"""
        error_count = 0
        max_errors = 3
        while self._monitoring:
            try:
                if not self._connection_healthy:
                    if error_count >= max_errors:
                        logging.warning("Too many connection errors, pausing monitoring")
                        await asyncio.sleep(60)  # Wait longer between retries
                        error_count = 0
                    else:
                        await asyncio.sleep(5)
                        error_count += 1
                    continue

                # Reset error count on successful connection
                error_count = 0

                # Try to get latest block
                try:
                    latest_block = await asyncio.get_event_loop().run_in_executor(
                        None, 
                        lambda: self.web3_service.w3.eth.block_number
                    )
                except Exception as e:
                    logging.error(f"Error getting latest block: {str(e)}")
                    self._connection_healthy = False
                    continue

                # Monitor for new deposits
                try:
                    deposits = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.web3_service.get_past_deposits(
                            from_block=latest_block - 10,  # Check last 10 blocks
                            to_block=latest_block
                        )
                    )
                    
                    for deposit in deposits:
                        await callback(deposit)
                        
                except Exception as e:
                    logging.error(f"Error processing deposits: {str(e)}")
                    
                await asyncio.sleep(12)  # Normal operation sleep

            except Exception as e:
                logging.error(f"Monitor error: {str(e)}")
                await asyncio.sleep(5)