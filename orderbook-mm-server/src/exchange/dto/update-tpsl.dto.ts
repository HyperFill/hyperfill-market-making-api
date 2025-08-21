import { IsString, IsNotEmpty, IsOptional } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class UpdateTpslDto {
  @ApiProperty({ enum: ['updateTpsl'] })
  @IsString()
  @IsNotEmpty()
  type: 'updateTpsl';

  @ApiProperty({ example: '0x742d35Cc6634C0532925a3b844Bc454e4438f44e' })
  @IsString()
  @IsNotEmpty()
  account: string;

  @ApiProperty({ example: '11000', required: false })
  @IsString()
  @IsOptional()
  takeProfit?: string;

  @ApiProperty({ example: '9000', required: false })
  @IsString()
  @IsOptional()
  stopLoss?: string;

  @ApiProperty({ example: 'some-unique-order-id' })
  @IsString()
  @IsNotEmpty()
  orderId: string;

  @ApiProperty({ example: '0x...' })
  @IsString()
  @IsNotEmpty()
  signature: string;

  @ApiProperty({ enum: ['tp', 'sl'] })
  @IsString()
  @IsNotEmpty()
  tpsl: 'tp' | 'sl';
}
