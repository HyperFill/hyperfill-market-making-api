import { IsString, IsNotEmpty } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class LimitDto {
  @ApiProperty({ example: 'Gtc' })
  @IsString()
  @IsNotEmpty()
  tif: string;

  @ApiProperty({ example: '10000.5' })
  @IsString()
  @IsNotEmpty()
  limitPrice: string;
}
