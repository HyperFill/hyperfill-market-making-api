import { Controller, Post, Body, BadRequestException } from '@nestjs/common';
import { ExchangeService } from './exchange.service';
import { CreateOrderDto } from './dto/create-order.dto';
import { CryptoService } from '../shared/crypto/crypto.service';
import { CancelOrderDto } from './dto/cancel-order.dto';
import { UpdateMarginDto } from './dto/update-margin.dto';
import { UpdateTpslDto } from './dto/update-tpsl.dto';

@Controller('exchange')
export class ExchangeController {
  constructor(
    private readonly exchangeService: ExchangeService,
    private readonly cryptoService: CryptoService,
  ) {}

  @Post()
  create(@Body() createOrderDto: CreateOrderDto) {
    for (const order of createOrderDto.orders) {
      const message = order.orderId;
      const signature = order.signature;
      const address = order.account;

      if (!this.cryptoService.verifySignature(message, signature, address)) {
        throw new BadRequestException('Invalid signature');
      }
    }
    return this.exchangeService.create(createOrderDto);
  }

  @Post('cancel')
  cancel(@Body() cancelOrderDto: CancelOrderDto) {
    for (const cancel of cancelOrderDto.cancels) {
      const message = cancel.orderId;
      const signature = cancel.signature;
      const address = cancel.account;

      if (!this.cryptoService.verifySignature(message, signature, address)) {
        throw new BadRequestException('Invalid signature');
      }
    }
    return this.exchangeService.cancel(cancelOrderDto);
  }

  @Post('update-margin')
  updateMargin(@Body() updateMarginDto: UpdateMarginDto) {
    const message = updateMarginDto.orderId;
    const signature = updateMarginDto.signature;
    const address = updateMarginDto.account;

    if (!this.cryptoService.verifySignature(message, signature, address)) {
      throw new BadRequestException('Invalid signature');
    }
    return this.exchangeService.updateMargin(updateMarginDto);
  }

  @Post('update-tpsl')
  updateTpsl(@Body() updateTpslDto: UpdateTpslDto) {
    const message = updateTpslDto.orderId;
    const signature = updateTpslDto.signature;
    const address = updateTpslDto.account;

    if (!this.cryptoService.verifySignature(message, signature, address)) {
      throw new BadRequestException('Invalid signature');
    }
    return this.exchangeService.updateTpsl(updateTpslDto);
  }
}
