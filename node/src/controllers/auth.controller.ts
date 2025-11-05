import { Request, Response, NextFunction } from 'express';
import { User } from '@prisma/client';
import passport from 'passport';
import authService from '../services/domain/auth.service';
import logger from '../utils/logger';
import config from '../config';
import { ConflictError, ValidationError, UnauthorizedError } from '../types/errors';

/**
 * Auth Controller
 * Handles HTTP requests for authentication
 * Thin controller - delegates business logic to AuthService
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
    passport.authenticate('local', (err: Error | null, user: User | false, info?: { message: string }) => {
      if (err) {
        logger.error('Login error:', err);
        return next(err);
      }

      if (!user) {
        return res.redirect('/auth/login?error=' + encodeURIComponent(info?.message || 'Login failed'));
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

      // Register user through service
      const acceptedLangs = req.acceptsLanguages(config.app.languages);
      const user = await authService.register({
        email,
        password,
        fname,
        inviteCode,
        acceptedLanguages: Array.isArray(acceptedLangs) ? acceptedLangs : [acceptedLangs || 'en'],
      });

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
      if (error instanceof ValidationError || error instanceof ConflictError || error instanceof UnauthorizedError) {
        return res.redirect('/auth/register?error=' + encodeURIComponent(error.message));
      }
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
    passport.authenticate('google', (err: Error | null, user: User | false, info?: { message: string }) => {
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

      const result = await authService.requestPasswordReset(email);

      logger.info(`Password reset requested for: ${email}`);

      res.render('auth/forgot-password.njk', {
        title: 'Reset Password',
        message: result.message,
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

      await authService.resetPassword(token, password, confirmPassword);

      logger.info('Password reset successful');

      res.redirect('/auth/login?message=' + encodeURIComponent('Password reset successful. Please login.'));
    } catch (error) {
      if (error instanceof ValidationError || error instanceof UnauthorizedError) {
        const { token } = req.params;
        if (error.message.includes('token')) {
          return res.redirect('/auth/forgot-password?error=' + encodeURIComponent(error.message));
        }
        return res.redirect(`/auth/reset-password/${token}?error=` + encodeURIComponent(error.message));
      }
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
