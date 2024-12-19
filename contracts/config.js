// import * as dotenv from 'dotenv'
const dotenv = require('dotenv');


dotenv.config()

const config = {
  isHarmony: process.env.NETWORK === 'harmony' || process.env.NETWORK === 'mainnet',
  isLocal: process.env.NETWORK === 'localhost' || process.env.NETWORK === 'hardhat', // || process.env.NETWORK === 'local'
  metaMaskWallet: process.env.MEMATASK_WALLET_ADDRESS ?? '',
  network: process.env.NETWORK,
  chains: {
    mainnet: {
      privateKey: process.env.PRIVATE_KEY ?? '',
      networkUrl: 'https://api.harmony.one',
      chainId: 1666600000,
    },
    testnet: {
      privateKey: process.env.PRIVATE_KEY ?? '',
      networkUrl: 'https://api.s0.b.hmny.io',
      // networkUrl: 'https://api.s0.t.hmny.io',
      chainId: 1666700000,
    },
    hardhat: {
      privateKey: process.env.HARDHAT_PRIVATE_KEY ?? '', // This is a default private key for Hardhat's first account
      networkUrl: "http://127.0.0.1:8545",
      chainId: 1337,
    }, 
    localhost: {
      privateKey: process.env.HARDHAT_PRIVATE_KEY ?? '', // This is a default private key for Hardhat's first account
      networkUrl: "http://127.0.0.1:8545",
      chainId: 1337,
    }
  }
}

module.exports = {
  config
}