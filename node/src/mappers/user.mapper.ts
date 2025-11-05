/**
 * User Mappers
 * Functions to map database entities to User DTOs
 */

import { User } from '@prisma/client';
import { UserDto, UserProfileDto, UserListDto } from '../types/dto';

/**
 * Map user entity to safe DTO (public info only)
 * Excludes password and sensitive fields
 */
export function mapToUserDto(user: User): UserDto {
  return {
    id: user.id,
    email: user.email,
    fname: user.fname,
    type: user.type,
    lang: user.lang,
    regDate: user.regDate,
  };
}

/**
 * Map user entity to profile DTO (for logged-in user)
 */
export function mapToUserProfileDto(user: User): UserProfileDto {
  return {
    ...mapToUserDto(user),
    connectMethod: user.connectMethod,
    createdAt: user.createdAt,
    updatedAt: user.updatedAt,
  };
}

/**
 * Map user entity to list DTO (for admin views)
 */
export function mapToUserListDto(user: User): UserListDto {
  return {
    id: user.id,
    email: user.email,
    fname: user.fname,
    type: user.type,
    connectMethod: user.connectMethod,
    regDate: user.regDate,
    createdAt: user.createdAt,
  };
}
