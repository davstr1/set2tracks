import { Request, Response, NextFunction } from 'express';
import { PrismaClient } from '@prisma/client';
import passport from 'passport';
import crypto from 'crypto';
import PasswordUtils from '../utils/password';
import logger from '../utils/logger';
import config from '../config';

const prisma = new PrismaClient();

/**
 * Auth Controller
 * Handles user registration, login, logout, password reset
 */
export class AuthController {
  /**
   * Show login page
   */
  async showLogin(req: Request, res: Response): Promise<void> {
    res.render('auth/login.njk', {
      title: 'Login',
      allowSite: config.signup.allowSite,
      allowGoogle: config.signup.allowGoogle,
      error: req.query.error,
      redirect: req.query.redirect || '/',
    });
  }

  /**
   * Show register page
   */
  async showRegister(req: Request, res: Response): Promise<void> {
    res.render('auth/register.njk', {
      title: 'Register',
      allowSite: config.signup.allowSite,
      allowGoogle: config.signup.allowGoogle,
      allowInvite: config.signup.allowInvite,
      error: req.query.error,
    });
  }

  /**
   * Handle login POST
   */
  async login(req: Request, res: Response, next: NextFunction): Promise<void> {
    passport.authenticate('local', (err: any, user: any, info: any) => {
      if (err) {
        logger.error('Login error:', err);
        return next(err);
      }

      if (!user) {
        return res.redirect('/auth/login?error=' + encodeURIComponent(info.message || 'Login failed'));
      }

      req.logIn(user, (err) => {
        if (err) {
          logger.error('Session login error:', err);
          return next(err);
        }

        const redirect = req.body.redirect || '/';
        return res.redirect(redirect);
      });
    })(req, res, next);
  }

  /**
   * Handle registration POST
   */
  async register(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { email, password, fname, inviteCode } = req.body;

      // Validate input
      if (!email || !password || !fname) {
        return res.redirect('/auth/register?error=' + encodeURIComponent('All fields are required'));
      }

      // Validate password
      const passwordValidation = PasswordUtils.validate(password);
      if (!passwordValidation.valid) {
        return res.redirect('/auth/register?error=' + encodeURIComponent(passwordValidation.message!));
      }

      // Check if site registration is allowed
      if (!config.signup.allowSite && !inviteCode) {
        return res.redirect('/auth/register?error=' + encodeURIComponent('Registration is invite-only'));
      }

      // Validate invite code if provided
      if (inviteCode) {
        const invite = await prisma.invite.findUnique({
          where: { inviteCode },
        });

        if (!invite) {
          return res.redirect('/auth/register?error=' + encodeURIComponent('Invalid invite code'));
        }

        if (invite.email.toLowerCase() !== email.toLowerCase()) {
          return res.redirect('/auth/register?error=' + encodeURIComponent('Email does not match invite'));
        }
      }

      // Check if email already exists
      const existingUser = await prisma.user.findUnique({
        where: { email: email.toLowerCase() },
      });

      if (existingUser) {
        return res.redirect('/auth/register?error=' + encodeURIComponent('Email already registered'));
      }

      // Hash password
      const hashedPassword = await PasswordUtils.hash(password);

      // Create user
      const user = await prisma.user.create({
        data: {
          email: email.toLowerCase(),
          fname,
          password: hashedPassword,
          type: 'User',
          connectMethod: 'Site',
          lang: req.acceptsLanguages(config.app.languages) || 'en',
        },
      });

      // Delete invite if used
      if (inviteCode) {
        await prisma.invite.delete({
          where: { inviteCode },
        });
      }

      logger.info(`New user registered: ${user.email}`);

      // Auto-login after registration
      req.logIn(user, (err) => {
        if (err) {
          logger.error('Auto-login error after registration:', err);
          return res.redirect('/auth/login');
        }
        return res.redirect('/');
      });
    } catch (error) {
      logger.error('Registration error:', error);
      next(error);
    }
  }

  /**
   * Handle logout
   */
  async logout(req: Request, res: Response, next: NextFunction): Promise<void> {
    req.logout((err) => {
      if (err) {
        logger.error('Logout error:', err);
        return next(err);
      }
      res.redirect('/');
    });
  }

  /**
   * Google OAuth callback
   */
  async googleCallback(req: Request, res: Response, next: NextFunction): Promise<void> {
    passport.authenticate('google', (err: any, user: any, info: any) => {
      if (err) {
        logger.error('Google OAuth error:', err);
        return res.redirect('/auth/login?error=' + encodeURIComponent('Google login failed'));
      }

      if (!user) {
        return res.redirect('/auth/login?error=' + encodeURIComponent('Google login failed'));
      }

      req.logIn(user, (err) => {
        if (err) {
          logger.error('Session login error after Google OAuth:', err);
          return res.redirect('/auth/login?error=' + encodeURIComponent('Login failed'));
        }
        return res.redirect('/');
      });
    })(req, res, next);
  }

  /**
   * Show password reset request page
   */
  async showForgotPassword(req: Request, res: Response): Promise<void> {
    res.render('auth/forgot-password.njk', {
      title: 'Reset Password',
    });
  }

  /**
   * Handle password reset request
   */
  async forgotPassword(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { email } = req.body;

      if (!email) {
        return res.redirect('/auth/forgot-password?error=' + encodeURIComponent('Email is required'));
      }

      const user = await prisma.user.findUnique({
        where: { email: email.toLowerCase() },
      });

      // Don't reveal if user exists
      if (!user) {
        return res.render('auth/forgot-password.njk', {
          title: 'Reset Password',
          message: 'If that email is registered, a reset link has been sent.',
        });
      }

      // Generate reset token
      const resetToken = crypto.randomBytes(32).toString('hex');
      const resetTokenExpiry = new Date(Date.now() + 3600000); // 1 hour

      // Store token in user's extraFields
      await prisma.user.update({
        where: { id: user.id },
        data: {
          extraFields: {
            ...((user.extraFields as any) || {}),
            resetToken,
            resetTokenExpiry: resetTokenExpiry.toISOString(),
          },
        },
      });

      // TODO: Send email with reset link
      // await emailService.sendPasswordReset(user.email, resetToken);

      logger.info(`Password reset requested for: ${user.email}`);

      res.render('auth/forgot-password.njk', {
        title: 'Reset Password',
        message: 'If that email is registered, a reset link has been sent.',
      });
    } catch (error) {
      logger.error('Forgot password error:', error);
      next(error);
    }
  }

  /**
   * Show password reset page
   */
  async showResetPassword(req: Request, res: Response): Promise<void> {
    const { token } = req.params;

    res.render('auth/reset-password.njk', {
      title: 'Reset Password',
      token,
    });
  }

  /**
   * Handle password reset
   */
  async resetPassword(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { token } = req.params;
      const { password, confirmPassword } = req.body;

      if (!password || !confirmPassword) {
        return res.redirect(`/auth/reset-password/${token}?error=` + encodeURIComponent('All fields are required'));
      }

      if (password !== confirmPassword) {
        return res.redirect(`/auth/reset-password/${token}?error=` + encodeURIComponent('Passwords do not match'));
      }

      // Validate password
      const passwordValidation = PasswordUtils.validate(password);
      if (!passwordValidation.valid) {
        return res.redirect(`/auth/reset-password/${token}?error=` + encodeURIComponent(passwordValidation.message!));
      }

      // Find user with this reset token
      const users = await prisma.user.findMany();
      const user = users.find((u) => {
        const extraFields = u.extraFields as any;
        if (!extraFields?.resetToken) return false;
        if (extraFields.resetToken !== token) return false;
        if (new Date(extraFields.resetTokenExpiry) < new Date()) return false;
        return true;
      });

      if (!user) {
        return res.redirect('/auth/forgot-password?error=' + encodeURIComponent('Invalid or expired reset token'));
      }

      // Hash new password
      const hashedPassword = await PasswordUtils.hash(password);

      // Update password and clear reset token
      await prisma.user.update({
        where: { id: user.id },
        data: {
          password: hashedPassword,
          extraFields: {
            ...((user.extraFields as any) || {}),
            resetToken: null,
            resetTokenExpiry: null,
          },
        },
      });

      logger.info(`Password reset successful for: ${user.email}`);

      res.redirect('/auth/login?message=' + encodeURIComponent('Password reset successful. Please login.'));
    } catch (error) {
      logger.error('Reset password error:', error);
      next(error);
    }
  }

  /**
   * Get current user info (API endpoint)
   */
  async getCurrentUser(req: Request, res: Response): Promise<void> {
    if (!req.user) {
      res.status(401).json({ error: 'Not authenticated' });
      return;
    }

    const user = req.user as any;

    res.json({
      id: user.id,
      email: user.email,
      fname: user.fname,
      type: user.type,
      lang: user.lang,
      regDate: user.regDate,
    });
  }
}

export default new AuthController();
