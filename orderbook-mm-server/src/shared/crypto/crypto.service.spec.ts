import { Test, TestingModule } from '@nestjs/testing';
import { CryptoService } from './crypto.service';
import { Wallet } from 'ethers';

describe('CryptoService', () => {
  let service: CryptoService;
  let wallet: Wallet;
  let message: string;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [CryptoService],
    }).compile();

    service = module.get<CryptoService>(CryptoService);
    wallet = Wallet.createRandom();
    message = 'test message';
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  it('should return true for a valid signature', async () => {
    const signature = await wallet.signMessage(message);
    const isValid = service.verifySignature(message, signature, wallet.address);
    expect(isValid).toBe(true);
  });

  it('should return false for an invalid signature', async () => {
    const signature = await wallet.signMessage(message);
    const otherWallet = Wallet.createRandom();
    const isValid = service.verifySignature(
      message,
      signature,
      otherWallet.address,
    );
    expect(isValid).toBe(false);
  });

  it('should return false for a malformed signature', () => {
    const isValid = service.verifySignature(
      message,
      'invalid-signature',
      wallet.address,
    );
    expect(isValid).toBe(false);
  });
});
