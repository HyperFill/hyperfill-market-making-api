import { Module } from '@nestjs/common';
import { ExchangeController } from './exchange.controller';
import { ExchangeService } from './exchange.service';
import { SharedModule } from '../shared/shared.module';
import { SettlementService } from './settlement/settlement.service';

@Module({
  imports: [SharedModule],
  controllers: [ExchangeController],
  providers: [ExchangeService, SettlementService],
})
export class ExchangeModule {}
