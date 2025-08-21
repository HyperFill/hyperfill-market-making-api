import { IsString, IsNotEmpty, IsArray, ValidateNested } from 'class-validator';
import { Type } from 'class-transformer';
import { OrderDto } from './order.dto';

export class CreateOrderDto {
  @IsString()
  @IsNotEmpty()
  type: 'order';

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => OrderDto)
  orders: OrderDto[];
}
