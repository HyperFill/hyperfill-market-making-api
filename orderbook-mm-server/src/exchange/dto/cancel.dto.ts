import { IsString, IsNotEmpty } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class CancelDto {
  @ApiProperty({ example: '0x742d35Cc6634C0532925a3b844Bc454e4438f44e' })
  @IsString()
  @IsNotEmpty()
  account: string;

  @ApiProperty({ example: 'some-unique-order-id' })
  @IsString()
  @IsNotEmpty()
  orderId: string;

  @ApiProperty({ example: '0x...' })
  @IsString()
  @IsNotEmpty()
  signature: string;
}
