import { body, checkSchema } from 'express-validator';

/**
 * Authentication Validators
 *
 * Validation rules for auth endpoints
 */

export const registerValidator = [
  body('email')
    .isEmail()
    .withMessage('Invalid email address')
    .normalizeEmail()
    .trim(),

  body('password')
    .isString()
    .isLength({ min: 8, max: 128 })
    .withMessage('Password must be between 8 and 128 characters')
    .matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/)
    .withMessage('Password must contain at least one lowercase letter, one uppercase letter, and one number'),

  body('name')
    .optional()
    .isString()
    .trim()
    .isLength({ min: 1, max: 100 })
    .withMessage('Name must be between 1 and 100 characters'),

  body('inviteCode')
    .optional()
    .isString()
    .trim()
    .isLength({ min: 6, max: 50 })
    .withMessage('Invalid invite code'),
];

export const loginValidator = [
  body('email')
    .isEmail()
    .withMessage('Invalid email address')
    .normalizeEmail()
    .trim(),

  body('password')
    .isString()
    .notEmpty()
    .withMessage('Password is required'),
];

export const forgotPasswordValidator = [
  body('email')
    .isEmail()
    .withMessage('Invalid email address')
    .normalizeEmail()
    .trim(),
];

export const resetPasswordValidator = [
  body('token')
    .isString()
    .notEmpty()
    .withMessage('Reset token is required')
    .trim(),

  body('password')
    .isString()
    .isLength({ min: 8, max: 128 })
    .withMessage('Password must be between 8 and 128 characters')
    .matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/)
    .withMessage('Password must contain at least one lowercase letter, one uppercase letter, and one number'),
];

export const changePasswordValidator = [
  body('currentPassword')
    .isString()
    .notEmpty()
    .withMessage('Current password is required'),

  body('newPassword')
    .isString()
    .isLength({ min: 8, max: 128 })
    .withMessage('New password must be between 8 and 128 characters')
    .matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/)
    .withMessage('New password must contain at least one lowercase letter, one uppercase letter, and one number')
    .custom((value, { req }) => value !== req.body.currentPassword)
    .withMessage('New password must be different from current password'),
];

export default {
  registerValidator,
  loginValidator,
  forgotPasswordValidator,
  resetPasswordValidator,
  changePasswordValidator,
};
