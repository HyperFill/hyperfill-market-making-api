import { IsBoolean, IsNumber, IsOptional } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class TriggerDto {
  @ApiProperty()
  @IsBoolean()
  isMarket: boolean;

  @ApiProperty({ required: false })
  @IsNumber()
  @IsOptional()
  slippage?: number;
}
