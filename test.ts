import { CryptoService } from './src/shared/crypto/crypto.service';
import { Wallet } from 'ethers';

async function runTest() {
  const cryptoService = new CryptoService();
  const wallet = Wallet.createRandom();
  const message = 'test message';

  // Test valid signature
  const signature = await wallet.signMessage(message);
  const isValid = cryptoService.verifySignature(message, signature, wallet.address);
  console.assert(isValid, 'Test Case 1 Failed: Valid signature should return true');
  console.log('Test Case 1 Passed');


  // Test invalid signature
  const otherWallet = Wallet.createRandom();
  const isInvalid = cryptoService.verifySignature(message, signature, otherWallet.address);
  console.assert(!isInvalid, 'Test Case 2 Failed: Invalid signature should return false');
  console.log('Test Case 2 Passed');

  // Test malformed signature
  const isMalformed = cryptoService.verifySignature(message, 'invalid-signature', wallet.address);
  console.assert(!isMalformed, 'Test Case 3 Failed: Malformed signature should return false');
  console.log('Test Case 3 Passed');
}

runTest().catch(console.error);
