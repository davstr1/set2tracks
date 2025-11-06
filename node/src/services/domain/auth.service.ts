import userRepository from '../../repositories/user.repository';
import PasswordUtils from '../../utils/password';
import crypto from 'crypto';
import { ConflictError, UnauthorizedError, NotFoundError, ValidationError } from '../../types/errors';
import config from '../../config';
import { logAuth, logSecurity, logBusinessEvent } from '../../utils/structuredLogger';
import prisma from '../../utils/database';

/**
 * Auth Service
 * Business logic for authentication and user management
 */
export class AuthService {
  /**
   * Register a new user
   */
  async register(params: {
    email: string;
    password: string;
    fname: string;
    inviteCode?: string;
    acceptedLanguages?: string[];
  }) {
    const { email, password, fname, inviteCode, acceptedLanguages } = params;

    // Validate password
    const passwordValidation = PasswordUtils.validate(password);
    if (!passwordValidation.valid) {
      throw new ValidationError(passwordValidation.message || 'Invalid password');
    }

    // Check if site registration is allowed
    if (!config.signup.allowSite && !inviteCode) {
      throw new UnauthorizedError('Registration is invite-only');
    }

    // Validate invite code if provided
    if (inviteCode) {
      const invite = await userRepository.findInviteByCode(inviteCode);

      if (!invite) {
        throw new NotFoundError('Invite code');
      }

      if (invite.email.toLowerCase() !== email.toLowerCase()) {
        throw new ValidationError('Email does not match invite');
      }
    }

    // Check if email already exists
    const existingUser = await userRepository.findByEmail(email);

    if (existingUser) {
      throw new ConflictError('Email already registered');
    }

    // Hash password
    const hashedPassword = await PasswordUtils.hash(password);

    // Determine language
    const lang = acceptedLanguages && acceptedLanguages.length > 0
      ? acceptedLanguages[0]
      : 'en';

    // Use transaction to ensure atomic user creation and invite deletion
    const user = await prisma.$transaction(async (tx) => {
      // Create user
      const newUser = await tx.user.create({
        data: {
          email,
          fname,
          password: hashedPassword,
          type: 'User',
          connectMethod: 'Site',
          lang,
          regDate: new Date(),
          acceptedLanguages: acceptedLanguages ? acceptedLanguages.join(',') : 'en',
        },
      });

      // Delete invite if used (must succeed for transaction to commit)
      if (inviteCode) {
        await tx.invite.delete({
          where: { code: inviteCode },
        });
      }

      return newUser;
    });

    logAuth('user_registered', {
      userId: user.id,
      email: user.email,
      connectMethod: 'Site',
      usedInvite: !!inviteCode,
    });

    logBusinessEvent('user_registration', {
      userId: user.id,
      connectMethod: 'Site',
      lang,
    });

    return user;
  }

  /**
   * Verify user credentials (for Passport local strategy)
   */
  async verifyCredentials(email: string, password: string) {
    const user = await userRepository.findByEmail(email);

    if (!user) {
      logSecurity('login_failed_user_not_found', { email });
      throw new UnauthorizedError('Invalid email or password');
    }

    const isValid = await PasswordUtils.compare(password, user.password);

    if (!isValid) {
      logSecurity('login_failed_invalid_password', { userId: user.id, email });
      throw new UnauthorizedError('Invalid email or password');
    }

    logAuth('login_success', { userId: user.id, email, userType: user.type });

    return user;
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string) {
    const user = await userRepository.findByEmail(email);

    // Don't reveal if user exists for security
    if (!user) {
      return {
        message: 'If that email is registered, a reset link has been sent.',
      };
    }

    // Generate reset token
    const resetToken = crypto.randomBytes(32).toString('hex');
    const resetTokenExpiry = new Date(Date.now() + 3600000); // 1 hour

    // Store token in user's extraFields
    await userRepository.updateExtraFields(user.id, {
      resetToken,
      resetTokenExpiry: resetTokenExpiry.toISOString(),
    });

    // TODO: Send email with reset link
    // await emailService.sendPasswordReset(user.email, resetToken);

    logSecurity('password_reset_requested', {
      userId: user.id,
      email: user.email,
    });

    return {
      message: 'If that email is registered, a reset link has been sent.',
      // For development only - remove in production
      ...(process.env.NODE_ENV === 'development' && { resetToken }),
    };
  }

  /**
   * Reset password with token
   */
  async resetPassword(token: string, newPassword: string, confirmPassword: string) {
    // Validate passwords match
    if (newPassword !== confirmPassword) {
      throw new ValidationError('Passwords do not match');
    }

    // Validate password strength
    const passwordValidation = PasswordUtils.validate(newPassword);
    if (!passwordValidation.valid) {
      throw new ValidationError(passwordValidation.message || 'Invalid password');
    }

    // Find user with this reset token
    const user = await userRepository.findByResetToken(token);

    if (!user) {
      throw new UnauthorizedError('Invalid or expired reset token');
    }

    // Hash new password
    const hashedPassword = await PasswordUtils.hash(newPassword);

    // Update password and clear reset token
    await userRepository.updatePassword(user.id, hashedPassword);
    await userRepository.updateExtraFields(user.id, {
      resetToken: null,
      resetTokenExpiry: null,
    });

    logSecurity('password_reset_completed', {
      userId: user.id,
      email: user.email,
    });

    return {
      message: 'Password reset successful',
    };
  }

  /**
   * Get user by ID
   */
  async getUserById(id: number) {
    const user = await userRepository.findById(id);

    if (!user) {
      throw new NotFoundError('User', id);
    }

    return user;
  }

  /**
   * Get user by email
   */
  async getUserByEmail(email: string) {
    const user = await userRepository.findByEmail(email);

    if (!user) {
      throw new NotFoundError('User');
    }

    return user;
  }

  /**
   * Update user type (admin only)
   */
  async updateUserType(id: number, type: string) {
    if (!['Admin', 'User', 'Guest'].includes(type)) {
      throw new ValidationError('Invalid user type');
    }

    const user = await userRepository.updateUserType(id, type);

    logSecurity('user_type_changed', {
      userId: id,
      newType: type,
    });

    return { success: true, user };
  }
}

export default new AuthService();
