import {
  IsString,
  IsNotEmpty,
  IsBoolean,
  IsNumber,
  IsObject,
  ValidateNested,
} from 'class-validator';
import { Type } from 'class-transformer';
import { LimitDto } from './limit-order.dto';
import { TriggerDto } from './trigger-order.dto';
import { ApiProperty } from '@nestjs/swagger';

class OrderTypeDto {
  @ApiProperty({ enum: ['limit', 'trigger'] })
  @IsString()
  @IsNotEmpty()
  type: 'limit' | 'trigger';

  @ApiProperty({ type: () => LimitDto, required: false })
  @IsObject()
  @ValidateNested()
  @Type(() => LimitDto)
  limit?: LimitDto;

  @ApiProperty({ type: () => TriggerDto, required: false })
  @IsObject()
  @ValidateNested()
  @Type(() => TriggerDto)
  trigger?: TriggerDto;
}

export class OrderDto {
  @ApiProperty({ example: '0x742d35Cc6634C0532925a3b844Bc454e4438f44e' })
  @IsString()
  @IsNotEmpty()
  account: string;

  @ApiProperty({ example: 'BTC' })
  @IsString()
  @IsNotEmpty()
  indexToken: string;

  @ApiProperty()
  @IsBoolean()
  isBuy: boolean;

  @ApiProperty({ example: 1.5 })
  @IsNumber()
  size: number;

  @ApiProperty({ example: 10 })
  @IsNumber()
  leverage: number;

  @ApiProperty()
  @IsBoolean()
  reduceOnly: boolean;

  @ApiProperty({ example: 'some-unique-order-id' })
  @IsString()
  @IsNotEmpty()
  orderId: string;

  @ApiProperty({ example: '0x...' })
  @IsString()
  @IsNotEmpty()
  signature: string;

  @ApiProperty()
  @IsObject()
  @ValidateNested()
  @Type(() => OrderTypeDto)
  orderType: OrderTypeDto;
}
