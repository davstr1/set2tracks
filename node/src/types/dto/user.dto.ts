/**
 * User DTOs
 * Data Transfer Objects for users and authentication
 */

/**
 * Public user info (safe to expose)
 */
export interface UserDto {
  id: number;
  email: string;
  fname: string;
  type: string;
  lang: string;
  regDate: Date;
}

/**
 * User profile (for logged-in user)
 */
export interface UserProfileDto extends UserDto {
  connectMethod: string;
  createdAt: Date;
  updatedAt: Date;
}

/**
 * User list item (for admin)
 */
export interface UserListDto {
  id: number;
  email: string;
  fname: string;
  type: string;
  connectMethod: string;
  regDate: Date;
  createdAt: Date;
}

/**
 * Login request
 */
export interface LoginRequestDto {
  email: string;
  password: string;
  redirect?: string;
}

/**
 * Registration request
 */
export interface RegisterRequestDto {
  email: string;
  password: string;
  fname: string;
  inviteCode?: string;
}

/**
 * Password reset request
 */
export interface PasswordResetRequestDto {
  email: string;
}

/**
 * Password reset confirmation
 */
export interface PasswordResetConfirmDto {
  token: string;
  password: string;
  confirmPassword: string;
}

/**
 * Auth response
 */
export interface AuthResponseDto {
  user: UserDto;
  message?: string;
}

/**
 * Password reset response
 */
export interface PasswordResetResponseDto {
  message: string;
  resetToken?: string; // Only in development
}
