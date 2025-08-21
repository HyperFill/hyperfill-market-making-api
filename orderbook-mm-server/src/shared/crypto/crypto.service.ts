import { Injectable } from '@nestjs/common';
import { verifyMessage } from 'ethers';

@Injectable()
export class CryptoService {
  verifySignature(
    message: string,
    signature: string,
    address: string,
  ): boolean {
    try {
      const signerAddr = verifyMessage(message, signature);
      return signerAddr.toLowerCase() === address.toLowerCase();
    } catch (error) {
      return false;
    }
  }
}
