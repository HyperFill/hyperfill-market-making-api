import { IsString, IsNotEmpty, IsArray, ValidateNested } from 'class-validator';
import { Type } from 'class-transformer';
import { CancelDto } from './cancel.dto';
import { ApiProperty } from '@nestjs/swagger';

export class CancelOrderDto {
  @ApiProperty({ enum: ['cancel'] })
  @IsString()
  @IsNotEmpty()
  type: 'cancel';

  @ApiProperty({ type: () => [CancelDto] })
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => CancelDto)
  cancels: CancelDto[];
}
