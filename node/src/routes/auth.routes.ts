import { Router } from 'express';
import passport from 'passport';
import authController from '../controllers/auth.controller';
import { requireGuest, requireAuth } from '../middleware/auth';
import { validateRequest } from '../middleware/validation';
import {
  registerValidator,
  loginValidator,
  forgotPasswordValidator,
  resetPasswordValidator,
} from '../validators/auth.validator';

const router = Router();

/**
 * Auth Routes
 */

// Login
router.get('/login', requireGuest, authController.showLogin.bind(authController));
router.post('/login', requireGuest, validateRequest(loginValidator), authController.login.bind(authController));

// Register
router.get('/register', requireGuest, authController.showRegister.bind(authController));
router.post('/register', requireGuest, validateRequest(registerValidator), authController.register.bind(authController));

// Logout
router.get('/logout', requireAuth, authController.logout.bind(authController));
router.post('/logout', requireAuth, authController.logout.bind(authController));

// Password Reset
router.get('/forgot-password', requireGuest, authController.showForgotPassword.bind(authController));
router.post('/forgot-password', requireGuest, validateRequest(forgotPasswordValidator), authController.forgotPassword.bind(authController));
router.get('/reset-password/:token', requireGuest, authController.showResetPassword.bind(authController));
router.post('/reset-password/:token', requireGuest, validateRequest(resetPasswordValidator), authController.resetPassword.bind(authController));

// Google OAuth
router.get(
  '/google',
  passport.authenticate('google', { scope: ['profile', 'email'] })
);

router.get(
  '/google/callback',
  authController.googleCallback.bind(authController)
);

// API: Get current user
router.get('/api/me', requireAuth, authController.getCurrentUser.bind(authController));

export default router;
