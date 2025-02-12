// SPDX-License-Identifier: MIT 
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

contract HarmonyLLMPaymentSimple is Ownable, ReentrancyGuard, Pausable {
    // State variables
    uint256 public minDeposit;
    
    // Events
    event Deposit(address indexed user, uint256 amount);
    event BatchWithdraw(uint256 amount);
    event MinDepositUpdated(uint256 oldValue, uint256 newValue);
    
    constructor() Ownable(msg.sender) {
        minDeposit = 5 ether;
    }

    receive() external payable whenNotPaused {
        require(msg.value >= minDeposit, "Deposit below minimum");
        emit Deposit(msg.sender, msg.value);
    }

    function setMinDeposit(uint256 newMinDeposit) external onlyOwner {
        require(newMinDeposit > 0, "Min deposit must be greater than 0");
        uint256 oldValue = minDeposit;
        minDeposit = newMinDeposit;
        emit MinDepositUpdated(oldValue, newMinDeposit);
    }

    function batchWithdraw() external onlyOwner nonReentrant {
        uint256 amount = address(this).balance;
        require(amount > 0, "No funds to withdraw");
        
        (bool success, ) = owner().call{value: amount}("");
        require(success, "Transfer failed");
        
        emit BatchWithdraw(amount);
    }

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }

    function getContractBalance() external view returns (uint256) {
        return address(this).balance;
    }
}