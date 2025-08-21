import { Module } from '@nestjs/common';
import { OrderBookGateway } from './order-book/order-book.gateway';
import { LiveFeedGateway } from './live-feed/live-feed.gateway';

@Module({
  providers: [OrderBookGateway, LiveFeedGateway]
})
export class WebsocketModule {}
