import { IsString, IsNotEmpty, IsOptional } from 'class-validator';

export class UpdateTpslDto {
  @IsString()
  @IsNotEmpty()
  type: 'updateTpsl';

  @IsString()
  @IsNotEmpty()
  account: string;

  @IsString()
  @IsOptional()
  takeProfit?: string;

  @IsString()
  @IsOptional()
  stopLoss?: string;

  @IsString()
  @IsNotEmpty()
  orderId: string;

  @IsString()
  @IsNotEmpty()
  signature: string;

  @IsString()
  @IsNotEmpty()
  tpsl: 'tp' | 'sl';
}
