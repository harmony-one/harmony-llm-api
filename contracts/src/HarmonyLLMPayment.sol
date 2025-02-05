// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

contract HarmonyLLMPayment is Ownable, ReentrancyGuard, Pausable {
    // Constants
    uint256 public constant MIN_DEPOSIT = 5 ether; // 5 ONE
    
    // State variables
    mapping(address => uint256) public balances;
    mapping(address => bool) public authorizedOperators;
    
    // Events
    event Deposit(address indexed user, uint256 amount, uint256 newBalance);
    event BatchWithdraw(uint256 amount);
    event OperatorUpdated(address indexed operator, bool status);
    
    constructor() Ownable(msg.sender) {
        authorizedOperators[msg.sender] = true;
    }

    // Handle incoming deposits
    receive() external payable whenNotPaused {
        require(msg.value >= MIN_DEPOSIT, "Deposit below minimum 5 ONE");
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value, balances[msg.sender]);
    }

    // Owner withdraws accumulated funds periodically
    function batchWithdraw() external onlyOwner nonReentrant {
        uint256 amount = address(this).balance;
        require(amount > 0, "No funds to withdraw");
        
        (bool success, ) = owner().call{value: amount}("");
        require(success, "Transfer failed");
        
        emit BatchWithdraw(amount);
    }

    // Safety Controls
    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }

    // Operator Management
    function setOperator(address operator, bool status) external onlyOwner {
        authorizedOperators[operator] = status;
        emit OperatorUpdated(operator, status);
    }

    // View Functions
    function getContractBalance() external view returns (uint256) {
        return address(this).balance;
    }
}