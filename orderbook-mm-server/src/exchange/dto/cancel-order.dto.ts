import { IsString, IsNotEmpty, IsArray, ValidateNested } from 'class-validator';
import { Type } from 'class-transformer';
import { CancelDto } from './cancel.dto';

export class CancelOrderDto {
  @IsString()
  @IsNotEmpty()
  type: 'cancel';

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => CancelDto)
  cancels: CancelDto[];
}
