import {
  SubscribeMessage,
  WebSocketGateway,
  WebSocketServer,
  OnGatewayInit,
  OnGatewayConnection,
  OnGatewayDisconnect,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';

@WebSocketGateway({ namespace: '/ws/order-book' })
export class OrderBookGateway
  implements OnGatewayInit, OnGatewayConnection, OnGatewayDisconnect {
  @WebSocketServer() server: Server;

  afterInit(server: Server) {
    console.log('OrderBookGateway Initialized');
    setInterval(() => this.sendOrderBookUpdate(), 5000);
  }

  handleConnection(client: Socket, ...args: any[]) {
    console.log(`Client connected: ${client.id}`);
  }

  handleDisconnect(client: Socket) {
    console.log(`Client disconnected: ${client.id}`);
  }

  sendOrderBookUpdate() {
    const mockOrderBook = {
      bids: [
        { price: '10000', size: '10' },
        { price: '9999', size: '5' },
      ],
      asks: [
        { price: '10001', size: '8' },
        { price: '10002', size: '12' },
      ],
    };
    this.server.emit('orderBook', mockOrderBook);
  }

  @SubscribeMessage('subscribe')
  handleSubscribe(client: Socket, payload: any): string {
    // In a real app, you would join the client to a room for a specific asset
    console.log(`Client ${client.id} subscribed to ${payload.asset}`);
    return `Subscribed to ${payload.asset}`;
  }
}
