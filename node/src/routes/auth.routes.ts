import { Router } from 'express';
import passport from 'passport';
import authController from '../controllers/auth.controller';
import { requireGuest, requireAuth } from '../middleware/auth';

const router = Router();

/**
 * Auth Routes
 */

// Login
router.get('/login', requireGuest, authController.showLogin.bind(authController));
router.post('/login', requireGuest, authController.login.bind(authController));

// Register
router.get('/register', requireGuest, authController.showRegister.bind(authController));
router.post('/register', requireGuest, authController.register.bind(authController));

// Logout
router.get('/logout', requireAuth, authController.logout.bind(authController));
router.post('/logout', requireAuth, authController.logout.bind(authController));

// Password Reset
router.get('/forgot-password', requireGuest, authController.showForgotPassword.bind(authController));
router.post('/forgot-password', requireGuest, authController.forgotPassword.bind(authController));
router.get('/reset-password/:token', requireGuest, authController.showResetPassword.bind(authController));
router.post('/reset-password/:token', requireGuest, authController.resetPassword.bind(authController));

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
