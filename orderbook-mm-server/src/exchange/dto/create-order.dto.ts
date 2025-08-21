import { IsString, IsNotEmpty, IsArray, ValidateNested } from 'class-validator';
import { Type } from 'class-transformer';
import { OrderDto } from './order.dto';
import { ApiProperty } from '@nestjs/swagger';

export class CreateOrderDto {
  @ApiProperty({ enum: ['order'] })
  @IsString()
  @IsNotEmpty()
  type: 'order';

  @ApiProperty({ type: () => [OrderDto] })
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => OrderDto)
  orders: OrderDto[];
}
