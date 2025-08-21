import {
  IsString,
  IsNotEmpty,
  IsNumber,
  IsBoolean,
} from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class UpdateMarginDto {
  @ApiProperty({ enum: ['updateIsolatedMargin'] })
  @IsString()
  @IsNotEmpty()
  type: 'updateIsolatedMargin';

  @ApiProperty({ example: '0x742d35Cc6634C0532925a3b844Bc454e4438f44e' })
  @IsString()
  @IsNotEmpty()
  account: string;

  @ApiProperty({ example: 'BTC' })
  @IsString()
  @IsNotEmpty()
  asset: string;

  @ApiProperty({ example: 1000 })
  @IsNumber()
  collateral: number;

  @ApiProperty()
  @IsBoolean()
  isIncrement: boolean;

  @ApiProperty({ example: 'some-unique-order-id' })
  @IsString()
  @IsNotEmpty()
  orderId: string;

  @ApiProperty({ example: '0x...' })
  @IsString()
  @IsNotEmpty()
  signature: string;
}
