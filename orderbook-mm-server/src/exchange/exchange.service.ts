import { Injectable } from '@nestjs/common';
import { CreateOrderDto } from './dto/create-order.dto';
import { CancelOrderDto } from './dto/cancel-order.dto';
import { UpdateMarginDto } from './dto/update-margin.dto';
import { UpdateTpslDto } from './dto/update-tpsl.dto';
import { SettlementService } from './settlement/settlement.service';

@Injectable()
export class ExchangeService {
  constructor(private readonly settlementService: SettlementService) {}

  create(createOrderDto: CreateOrderDto) {
    console.log('New order received:', createOrderDto);
    for (const order of createOrderDto.orders) {
      // In a real application, you would match orders here.
      // For now, we will just send them directly to settlement.
      this.settlementService.settleTrade(order);
    }
    return { status: 'success', message: 'Order received and sent for settlement' };
  }

  cancel(cancelOrderDto: CancelOrderDto) {
    console.log('Cancel order request received:', cancelOrderDto);
    return { status: 'success', message: 'Cancel request received' };
  }

  updateMargin(updateMarginDto: UpdateMarginDto) {
    console.log('Update margin request received:', updateMarginDto);
    return { status: 'success', message: 'Update margin request received' };
  }

  updateTpsl(updateTpslDto: UpdateTpslDto) {
    console.log('Update TP/SL request received:', updateTpslDto);
    return { status: 'success', message: 'Update TP/SL request received' };
  }
}
