document.addEventListener('DOMContentLoaded', () => {
  const connectWalletBtn = document.getElementById('connectWallet');
  const walletInfo = document.getElementById('walletInfo');
  const accountAddress = document.getElementById('accountAddress');
  const accountBalance = document.getElementById('accountBalance');
  const depositForm = document.getElementById('depositForm');
  const depositAmount = document.getElementById('depositAmount');
  const depositButton = document.getElementById('depositButton');
  const statusMessage = document.getElementById('statusMessage');
  const minDepositInfo = document.getElementById('minDepositInfo');

  let currentAccount = null;
  let minDeposit = 0;

  // Initialize Web3
  const initWeb3 = async () => {
      if (typeof window.ethereum !== 'undefined') {
          window.web3 = new Web3(window.ethereum);
          return true;
      }
      showStatus('Please install MetaMask to use this feature', 'error');
      return false;
  };

  // Show status message
  const showStatus = (message, type) => {
      statusMessage.querySelector('div').textContent = message;
      statusMessage.querySelector('div').className = 
          `p-4 rounded-lg ${type === 'error' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`;
      statusMessage.classList.remove('hidden');
  };

  // Get minimum deposit amount
  const getMinDeposit = async () => {
      try {
          const response = await fetch('/deposit');
          const data = await response.json();
          minDeposit = data.minimum_deposit;
          minDepositInfo.textContent = `Minimum deposit: ${minDeposit} ONE`;
      } catch (error) {
          console.error('Error fetching minimum deposit:', error);
      }
  };

  // Update wallet info
  const updateWalletInfo = async () => {
      if (!currentAccount) return;

      const balance = await web3.eth.getBalance(currentAccount);
      const balanceInOne = web3.utils.fromWei(balance, 'ether');
      accountAddress.textContent = currentAccount;
      accountBalance.textContent = `${parseFloat(balanceInOne).toFixed(4)} ONE`;
  };

  // Connect wallet
  connectWalletBtn.addEventListener('click', async () => {
      if (!await initWeb3()) return;

      try {
          const accounts = await window.ethereum.request({ 
              method: 'eth_requestAccounts' 
          });
          currentAccount = accounts[0];
          
          // Show wallet info and deposit form
          walletInfo.classList.remove('hidden');
          depositForm.classList.remove('hidden');
          connectWalletBtn.classList.add('hidden');
          
          await updateWalletInfo();
          await getMinDeposit();

      } catch (error) {
          showStatus('Failed to connect wallet', 'error');
          console.error('Error connecting wallet:', error);
      }
  });

  // Handle deposit
  depositButton.addEventListener('click', async () => {
      if (!currentAccount) {
          showStatus('Please connect your wallet first', 'error');
          return;
      }

      const amount = parseFloat(depositAmount.value);
      if (!amount || amount < minDeposit) {
          showStatus(`Minimum deposit is ${minDeposit} ONE`, 'error');
          return;
      }

      try {
          // Get deposit address
          const response = await fetch('/deposit');
          const { deposit_address } = await response.json();

          // Create transaction
          const amountInWei = web3.utils.toWei(amount.toString(), 'ether');
          const tx = {
              from: currentAccount,
              to: deposit_address,
              value: amountInWei,
              gas: '100000'
          };

          // Send transaction
          depositButton.disabled = true;
          depositButton.textContent = 'Processing...';

          const txHash = await window.ethereum.request({
              method: 'eth_sendTransaction',
              params: [tx],
          });

          // Verify deposit
          await fetch('/deposit', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                  transaction_hash: txHash,
              }),
          });

          showStatus('Deposit successful!', 'success');
          depositAmount.value = '';
          await updateWalletInfo();

      } catch (error) {
          showStatus('Failed to process deposit', 'error');
          console.error('Error processing deposit:', error);
      } finally {
          depositButton.disabled = false;
          depositButton.textContent = 'Deposit';
      }
  });

  // Listen for account changes
  if (window.ethereum) {
      window.ethereum.on('accountsChanged', async (accounts) => {
          if (accounts.length === 0) {
              currentAccount = null;
              walletInfo.classList.add('hidden');
              depositForm.classList.add('hidden');
              connectWalletBtn.classList.remove('hidden');
          } else {
              currentAccount = accounts[0];
              await updateWalletInfo();
          }
      });
  }
});