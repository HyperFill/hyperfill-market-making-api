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

class OrderTypeDto {
  @IsString()
  @IsNotEmpty()
  type: 'limit' | 'trigger';

  @IsObject()
  @ValidateNested()
  @Type(() => LimitDto)
  limit?: LimitDto;

  @IsObject()
  @ValidateNested()
  @Type(() => TriggerDto)
  trigger?: TriggerDto;
}

export class OrderDto {
  @IsString()
  @IsNotEmpty()
  account: string;

  @IsString()
  @IsNotEmpty()
  indexToken: string;

  @IsBoolean()
  isBuy: boolean;

  @IsNumber()
  size: number;

  @IsNumber()
  leverage: number;

  @IsBoolean()
  reduceOnly: boolean;

  @IsString()
  @IsNotEmpty()
  orderId: string;

  @IsString()
  @IsNotEmpty()
  signature: string;

  @IsObject()
  @ValidateNested()
  @Type(() => OrderTypeDto)
  orderType: OrderTypeDto;
}
