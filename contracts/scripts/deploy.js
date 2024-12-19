const { ethers } = require("hardhat");
const { config } = require("../config.js");

async function main() {
  try {
    console.log("Deploying HarmonyLLMPayment contract...");

    // Get the network configuration
    const network = process.env.NETWORK || "hardhat";
    const networkConfig = config.chains[network];

    if (!networkConfig) {
      throw new Error(`Network configuration not found for ${network}`);
    }

    // Get the contract factory
    const HarmonyLLMPayment = await ethers.getContractFactory("HarmonyLLMPayment");
    
    // Deploy the contract
    const harmonyLLMPayment = await HarmonyLLMPayment.deploy();
    await harmonyLLMPayment.deployed();

    console.log(`HarmonyLLMPayment deployed to: ${harmonyLLMPayment.address}`);
    console.log(`Network: ${network}`);
    console.log(`Chain ID: ${networkConfig.chainId}`);

    // Verify the contract on block explorer (if not local network)
    if (!config.isLocal) {
      console.log("Waiting for block confirmations...");
      await harmonyLLMPayment.deployTransaction.wait(5); // Wait for 5 block confirmations

      console.log("Verifying contract...");
      await hre.run("verify:verify", {
        address: harmonyLLMPayment.address,
        constructorArguments: [],
      });
    }

  } catch (error) {
    console.error("Error during deployment:", error);
    process.exit(1);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });