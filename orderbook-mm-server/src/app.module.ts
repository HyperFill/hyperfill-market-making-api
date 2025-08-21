import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { ExchangeModule } from './exchange/exchange.module';
import { WebsocketModule } from './websocket/websocket.module';
import { SharedModule } from './shared/shared.module';

@Module({
  imports: [ExchangeModule, WebsocketModule, SharedModule],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
