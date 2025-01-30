import os
from enum import Enum
from typing import Any, Dict
from config import config

class Network(Enum):
    LOCALHOST = 'localhost'
    TESTNET = 'testnet'
    MAINNET = 'mainnet'

# CHANGED: Added environment variable loading for web3 specific configs
class Web3Config:
    # RPC endpoints
    HARMONY_TESTNET_URL = os.getenv('HARMONY_TESTNET_URL', 'https://api.s0.b.hmny.io')
    HARMONY_MAINNET_URL = os.getenv('HARMONY_MAINNET_URL', 'https://api.harmony.one')
    HARMONY_LOCAL_URL = os.getenv('HARMONY_LOCAL_URL', 'http://127.0.0.1:8545')
    
    # Contract addresses
    HARMONY_LLM_PAYMENT_TESTNET = os.getenv('HARMONY_LLM_PAYMENT_TESTNET', '')
    HARMONY_LLM_PAYMENT_MAINNET = os.getenv('HARMONY_LLM_PAYMENT_MAINNET', '')
    HARMONY_LLM_PAYMENT_LOCAL = os.getenv('HARMONY_LLM_PAYMENT_LOCAL', '0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512')
    
    # Private keys (Consider using a more secure way to handle these)
    TESTNET_PRIVATE_KEY = os.getenv('TESTNET_PRIVATE_KEY', '')
    MAINNET_PRIVATE_KEY = os.getenv('MAINNET_PRIVATE_KEY', '')
    LOCAL_PRIVATE_KEY = os.getenv('LOCAL_PRIVATE_KEY', '')

# CHANGED: Using Web3Config for network configurations
NETWORKS: Dict[Network, Dict[str, Any]] = {
    Network.TESTNET: {
        'url': Web3Config.HARMONY_TESTNET_URL,
        'chain_id': 1666700000,
        'private_key': Web3Config.TESTNET_PRIVATE_KEY,
        'explorer_url': 'https://explorer.pops.one',
        'contracts': {
            'HarmonyLLMPaymentSimple': Web3Config.HARMONY_LLM_PAYMENT_TESTNET,
        }
    },
    Network.MAINNET: {
        'url': Web3Config.HARMONY_MAINNET_URL,
        'chain_id': 1666600000,
        'private_key': Web3Config.MAINNET_PRIVATE_KEY,
        'explorer_url': 'https://explorer.harmony.one',
        'contracts': {
            'HarmonyLLMPaymentSimple': Web3Config.HARMONY_LLM_PAYMENT_MAINNET,
        }
    },
    Network.LOCALHOST: {
        'url': Web3Config.HARMONY_LOCAL_URL,
        'chain_id': 1337,
        'private_key': Web3Config.LOCAL_PRIVATE_KEY,
        'explorer_url': '',
        'contracts': {
            'HarmonyLLMPaymentSimple': Web3Config.HARMONY_LLM_PAYMENT_LOCAL,
        }
    }
}

def get_network(network_env: str) -> Dict[str, Any]:
    """
    Get network configuration based on environment NETWORK value.
    
    Args:
        network_env: String value from environment variable NETWORK
        
    Returns:
        Dictionary containing network configuration
        
    Raises:
        ValueError: If network_env doesn't match any Network enum value
    """
    try:
        network = Network(network_env.lower())
        return NETWORKS[network]
    except ValueError:
        valid_networks = [n.value for n in Network]
        raise ValueError(
            f"Invalid network: {network_env}. Must be one of: {', '.join(valid_networks)}"
        )

def get_contract_address(contract_name: str) -> str:
    """
    Get contract address for current network.
    
    Args:
        contract_name: Name of the contract
        
    Returns:
        Contract address for the current network
        
    Raises:
        KeyError: If contract name doesn't exist in network config
    """
    try:
        return CURRENT_NETWORK['contracts'][contract_name]
    except KeyError:
        available_contracts = list(CURRENT_NETWORK['contracts'].keys())
        raise KeyError(
            f"Contract {contract_name} not found. Available contracts: {', '.join(available_contracts)}"
        )

def get_explorer_url(tx_hash: str = None) -> str:
    """
    Get explorer URL for current network.
    
    Args:
        tx_hash: Optional transaction hash to append to URL
        
    Returns:
        Explorer URL, optionally with transaction hash
    """
    base_url = CURRENT_NETWORK['explorer_url']
    if not base_url:
        return ''
    
    if tx_hash:
        return f"{base_url}/tx/{tx_hash}"
    return base_url

# Initialize current network configuration
CURRENT_NETWORK = get_network(config.NETWORK)

# Export commonly used values
CURRENT_RPC_URL = CURRENT_NETWORK['url']
CURRENT_CHAIN_ID = CURRENT_NETWORK['chain_id']
CURRENT_PRIVATE_KEY = CURRENT_NETWORK['private_key']