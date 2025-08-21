import { Injectable } from '@nestjs/common';
import { OrderDto } from '../dto/order.dto';

@Injectable()
export class SettlementService {
  settleTrade(order: OrderDto) {
    console.log('--- MOCK ON-CHAIN SETTLEMENT ---');
    console.log(`Settling trade for orderId: ${order.orderId}`);
    console.log(`Account: ${order.account}`);
    console.log(`Token: ${order.indexToken}`);
    console.log(`Side: ${order.isBuy ? 'BUY' : 'SELL'}`);
    console.log(`Size: ${order.size}`);
    console.log('--- SETTLEMENT COMPLETE ---');
  }
}
