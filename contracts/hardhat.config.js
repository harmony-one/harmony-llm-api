require("@nomiclabs/hardhat-ethers");
require('dotenv').config({ path: './.env' }); 
const { config } = require("./config.js");

module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    hardhat: {
      chainId: config.chains.hardhat.chainId
    },
    localhost: {
      url: config.chains.localhost.networkUrl,
      chainId: config.chains.localhost.chainId
    },
    testnet: {
      url: config.chains.testnet.networkUrl,
      chainId: config.chains.testnet.chainId,
      accounts: [config.chains.testnet.privateKey]
    },
    mainnet: {
      url: config.chains.mainnet.networkUrl,
      chainId: config.chains.mainnet.chainId,
      accounts: [config.chains.mainnet.privateKey]
    }
  },
  paths: {
    sources: "./src",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts"
  }
};