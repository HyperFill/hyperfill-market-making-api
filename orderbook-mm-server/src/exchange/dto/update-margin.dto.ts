import {
  IsString,
  IsNotEmpty,
  IsNumber,
  IsBoolean,
} from 'class-validator';

export class UpdateMarginDto {
  @IsString()
  @IsNotEmpty()
  type: 'updateIsolatedMargin';

  @IsString()
  @IsNotEmpty()
  account: string;

  @IsString()
  @IsNotEmpty()
  asset: string;

  @IsNumber()
  collateral: number;

  @IsBoolean()
  isIncrement: boolean;

  @IsString()
  @IsNotEmpty()
  orderId: string;

  @IsString()
  @IsNotEmpty()
  signature: string;
}
