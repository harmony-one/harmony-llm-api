# Harmony LLM API


## Smart Contracts

The contracts directory contains all blockchain-related code:
- Smart contract source code
- Test files
- Deployment scripts
- Hardhat configuration

Main contracts:
- `HarmonyLLMPayment.sol`: Handles prepaid balances and usage tracking

## Setup

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### Smart Contract Setup
```bash
cd contracts
npm install
npx hardhat compile
```

## Development

### Running the Backend
```bash
cd backend
python app.py
```

### Testing Smart Contracts
```bash
cd contracts
npx hardhat test
```

### Deploying Smart Contracts
```bash
cd contracts
npx hardhat run scripts/deploy.js --network <network-name>
```
