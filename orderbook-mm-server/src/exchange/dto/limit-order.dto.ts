import { IsString, IsNotEmpty } from 'class-validator';

export class LimitDto {
  @IsString()
  @IsNotEmpty()
  tif: string;

  @IsString()
  @IsNotEmpty()
  limitPrice: string;
}
