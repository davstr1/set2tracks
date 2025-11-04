import bcrypt from 'bcrypt';
import config from '../config';

/**
 * Password utilities for hashing and verification
 */

export class PasswordUtils {
  /**
   * Hash a password using bcrypt
   */
  static async hash(password: string): Promise<string> {
    const saltRounds = config.security.passwordSaltLength || 10;
    return bcrypt.hash(password, saltRounds);
  }

  /**
   * Compare a plain password with a hashed password
   */
  static async compare(password: string, hash: string): Promise<boolean> {
    return bcrypt.compare(password, hash);
  }

  /**
   * Validate password strength
   */
  static validate(password: string): { valid: boolean; message?: string } {
    if (!password || password.length < 8) {
      return { valid: false, message: 'Password must be at least 8 characters long' };
    }

    // Optional: Add more password requirements
    // if (!/[A-Z]/.test(password)) {
    //   return { valid: false, message: 'Password must contain at least one uppercase letter' };
    // }

    return { valid: true };
  }
}

export default PasswordUtils;
