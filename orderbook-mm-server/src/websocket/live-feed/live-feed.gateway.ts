import {
  SubscribeMessage,
  WebSocketGateway,
  WebSocketServer,
  OnGatewayInit,
  OnGatewayConnection,
  OnGatewayDisconnect,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';

@WebSocketGateway({ namespace: '/ws/live-feed' })
export class LiveFeedGateway
  implements OnGatewayInit, OnGatewayConnection, OnGatewayDisconnect {
  @WebSocketServer() server: Server;

  afterInit(server: Server) {
    console.log('LiveFeedGateway Initialized');
    setInterval(() => this.sendLiveFeedUpdate(), 2000);
  }

  handleConnection(client: Socket, ...args: any[]) {
    console.log(`Client connected: ${client.id}`);
  }

  handleDisconnect(client: Socket) {
    console.log(`Client disconnected: ${client.id}`);
  }

  sendLiveFeedUpdate() {
    const mockLiveFeed = {
      symbol: 'BTC',
      currentPrice: 10000 + Math.random() * 10 - 5,
      oraclePrice: 10000,
      epochTimestamp: Date.now(),
    };
    this.server.emit('liveFeed', mockLiveFeed);
  }

  @SubscribeMessage('subscribe')
  handleSubscribe(client: Socket, payload: any): string {
    console.log(`Client ${client.id} subscribed to ${payload.asset}`);
    return `Subscribed to ${payload.asset}`;
  }
}
