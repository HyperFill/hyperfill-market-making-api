import { IsBoolean, IsNumber, IsOptional } from 'class-validator';

export class TriggerDto {
  @IsBoolean()
  isMarket: boolean;

  @IsNumber()
  @IsOptional()
  slippage?: number;
}
