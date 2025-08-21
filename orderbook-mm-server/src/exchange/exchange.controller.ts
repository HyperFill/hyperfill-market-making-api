import { Controller, Post, Body, BadRequestException } from '@nestjs/common';
import { ExchangeService } from './exchange.service';
import { CreateOrderDto } from './dto/create-order.dto';
import { CryptoService } from '../shared/crypto/crypto.service';
import { CancelOrderDto } from './dto/cancel-order.dto';
import { UpdateMarginDto } from './dto/update-margin.dto';
import { UpdateTpslDto } from './dto/update-tpsl.dto';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';

@ApiTags('exchange')
@Controller('exchange')
export class ExchangeController {
  constructor(
    private readonly exchangeService: ExchangeService,
    private readonly cryptoService: CryptoService,
  ) {}

  @Post()
  @ApiOperation({ summary: 'Place a new order' })
  @ApiResponse({
    status: 201,
    description: 'The order has been successfully created.',
  })
  @ApiResponse({ status: 400, description: 'Bad request.' })
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
  @ApiOperation({ summary: 'Cancel an existing order' })
  @ApiResponse({
    status: 201,
    description: 'The cancel request has been successfully received.',
  })
  @ApiResponse({ status: 400, description: 'Bad request.' })
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
  @ApiOperation({ summary: 'Update margin for a position' })
  @ApiResponse({
    status: 201,
    description: 'The margin update request has been successfully received.',
  })
  @ApiResponse({ status: 400, description: 'Bad request.' })
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
  @ApiOperation({ summary: 'Update take-profit or stop-loss for a position' })
  @ApiResponse({
    status: 201,
    description: 'The TP/SL update request has been successfully received.',
  })
  @ApiResponse({ status: 400, description: 'Bad request.' })
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
