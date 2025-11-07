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
import { authLimiter, registrationLimiter, passwordResetLimiter } from '../middleware/rateLimiter';

const router = Router();

/**
 * @swagger
 * tags:
 *   name: Auth
 *   description: Authentication and user management
 */

// Login (HTML page - not documented in OpenAPI)
router.get('/login', requireGuest, authController.showLogin.bind(authController));

/**
 * @swagger
 * /auth/login:
 *   post:
 *     tags: [Auth]
 *     summary: Authenticate user
 *     description: |
 *       Login with email and password. Returns a session cookie on success.
 *
 *       **Rate Limited:** 5 login attempts per 15 minutes per IP
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - email
 *               - password
 *             properties:
 *               email:
 *                 type: string
 *                 format: email
 *                 example: user@example.com
 *               password:
 *                 type: string
 *                 format: password
 *                 minLength: 8
 *                 example: SecurePassword123!
 *               rememberMe:
 *                 type: boolean
 *                 description: Extend session duration
 *                 default: false
 *     responses:
 *       200:
 *         description: Login successful
 *         headers:
 *           Set-Cookie:
 *             description: Session cookie
 *             schema:
 *               type: string
 *               example: sessionId=abc123; Path=/; HttpOnly; Secure; SameSite=Strict
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                   example: Login successful
 *                 user:
 *                   type: object
 *                   properties:
 *                     id:
 *                       type: integer
 *                     email:
 *                       type: string
 *                     fname:
 *                       type: string
 *                     type:
 *                       type: string
 *                       enum: [User, Admin]
 *       400:
 *         $ref: '#/components/responses/BadRequest'
 *       401:
 *         description: Invalid credentials
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/ErrorResponse'
 *       429:
 *         $ref: '#/components/responses/TooManyRequests'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.post('/login', requireGuest, authLimiter, validateRequest(loginValidator), authController.login.bind(authController));

// Register (HTML page - not documented in OpenAPI)
router.get('/register', requireGuest, authController.showRegister.bind(authController));

/**
 * @swagger
 * /auth/register:
 *   post:
 *     tags: [Auth]
 *     summary: Create new user account
 *     description: |
 *       Register a new user account. Invitation code may be required depending on server configuration.
 *
 *       **Rate Limited:** 3 registrations per hour per IP
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - email
 *               - password
 *               - fname
 *             properties:
 *               email:
 *                 type: string
 *                 format: email
 *                 example: newuser@example.com
 *               password:
 *                 type: string
 *                 format: password
 *                 minLength: 8
 *                 description: Must be at least 8 characters
 *                 example: SecurePassword123!
 *               fname:
 *                 type: string
 *                 minLength: 1
 *                 example: John
 *               inviteCode:
 *                 type: string
 *                 description: Invitation code (if required)
 *                 example: INVITE2024XYZ
 *               lang:
 *                 type: string
 *                 description: Preferred language (ISO 639-1 code)
 *                 default: en
 *                 example: en
 *     responses:
 *       201:
 *         description: Registration successful
 *         headers:
 *           Set-Cookie:
 *             description: Session cookie
 *             schema:
 *               type: string
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                   example: Registration successful
 *                 user:
 *                   type: object
 *                   properties:
 *                     id:
 *                       type: integer
 *                     email:
 *                       type: string
 *                     fname:
 *                       type: string
 *       400:
 *         description: Validation error or email already exists
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/ErrorResponse'
 *       429:
 *         $ref: '#/components/responses/TooManyRequests'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.post('/register', requireGuest, registrationLimiter, validateRequest(registerValidator), authController.register.bind(authController));

/**
 * @swagger
 * /auth/logout:
 *   post:
 *     tags: [Auth]
 *     summary: Logout user
 *     description: Destroy the current session and logout the authenticated user
 *     security:
 *       - sessionAuth: []
 *     responses:
 *       200:
 *         description: Logout successful
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                   example: Logout successful
 *       401:
 *         $ref: '#/components/responses/Unauthorized'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/logout', requireAuth, authController.logout.bind(authController));
router.post('/logout', requireAuth, authController.logout.bind(authController));

// Forgot password (HTML page - not documented in OpenAPI)
router.get('/forgot-password', requireGuest, authController.showForgotPassword.bind(authController));

/**
 * @swagger
 * /auth/forgot-password:
 *   post:
 *     tags: [Auth]
 *     summary: Request password reset
 *     description: |
 *       Send a password reset email to the specified address. Email will contain a reset link valid for 1 hour.
 *
 *       **Rate Limited:** 3 requests per hour per IP
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - email
 *             properties:
 *               email:
 *                 type: string
 *                 format: email
 *                 example: user@example.com
 *     responses:
 *       200:
 *         description: Password reset email sent (or email doesn't exist - same response for security)
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                   example: If an account exists with that email, a password reset link has been sent
 *       400:
 *         $ref: '#/components/responses/BadRequest'
 *       429:
 *         $ref: '#/components/responses/TooManyRequests'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.post('/forgot-password', requireGuest, passwordResetLimiter, validateRequest(forgotPasswordValidator), authController.forgotPassword.bind(authController));

// Reset password (HTML page - not documented in OpenAPI)
router.get('/reset-password/:token', requireGuest, authController.showResetPassword.bind(authController));

/**
 * @swagger
 * /auth/reset-password/{token}:
 *   post:
 *     tags: [Auth]
 *     summary: Reset password with token
 *     description: |
 *       Reset user password using the token received via email. Token is valid for 1 hour.
 *
 *       **Rate Limited:** 3 attempts per hour per IP
 *     parameters:
 *       - name: token
 *         in: path
 *         required: true
 *         description: Password reset token from email
 *         schema:
 *           type: string
 *           example: a1b2c3d4e5f6g7h8i9j0
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - password
 *             properties:
 *               password:
 *                 type: string
 *                 format: password
 *                 minLength: 8
 *                 description: New password (min 8 characters)
 *                 example: NewSecurePassword123!
 *     responses:
 *       200:
 *         description: Password reset successful
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                   example: Password reset successful. You can now login with your new password.
 *       400:
 *         description: Invalid or expired token
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/ErrorResponse'
 *       429:
 *         $ref: '#/components/responses/TooManyRequests'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.post('/reset-password/:token', requireGuest, passwordResetLimiter, validateRequest(resetPasswordValidator), authController.resetPassword.bind(authController));

/**
 * @swagger
 * /auth/google:
 *   get:
 *     tags: [Auth]
 *     summary: Initiate Google OAuth login
 *     description: Redirects to Google OAuth consent screen for authentication
 *     responses:
 *       302:
 *         description: Redirect to Google OAuth
 */
router.get(
  '/google',
  passport.authenticate('google', { scope: ['profile', 'email'] })
);

/**
 * @swagger
 * /auth/google/callback:
 *   get:
 *     tags: [Auth]
 *     summary: Google OAuth callback
 *     description: Callback URL for Google OAuth. Handled by passport middleware.
 *     parameters:
 *       - name: code
 *         in: query
 *         required: true
 *         description: Authorization code from Google
 *         schema:
 *           type: string
 *     responses:
 *       302:
 *         description: Redirect to application after successful authentication
 *       401:
 *         description: OAuth authentication failed
 */
router.get(
  '/google/callback',
  authController.googleCallback.bind(authController)
);

/**
 * @swagger
 * /auth/api/me:
 *   get:
 *     tags: [Auth]
 *     summary: Get current authenticated user
 *     description: Returns the currently authenticated user's profile information
 *     security:
 *       - sessionAuth: []
 *     responses:
 *       200:
 *         description: Current user retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 user:
 *                   type: object
 *                   properties:
 *                     id:
 *                       type: integer
 *                       example: 1
 *                     email:
 *                       type: string
 *                       example: user@example.com
 *                     fname:
 *                       type: string
 *                       example: John
 *                     type:
 *                       type: string
 *                       enum: [User, Admin]
 *                       example: User
 *                     connectMethod:
 *                       type: string
 *                       enum: [Site, Google]
 *                       example: Site
 *                     lang:
 *                       type: string
 *                       example: en
 *       401:
 *         $ref: '#/components/responses/Unauthorized'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/api/me', requireAuth, authController.getCurrentUser.bind(authController));

export default router;
