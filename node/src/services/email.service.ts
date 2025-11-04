import nodemailer, { Transporter } from 'nodemailer';
import config from '../config';
import logger from '../utils/logger';

/**
 * Email Service
 * Handles sending emails for password resets, notifications, etc.
 */
class EmailService {
  private transporter: Transporter;

  constructor() {
    this.transporter = nodemailer.createTransport({
      host: config.mail.server,
      port: config.mail.port,
      secure: config.mail.port === 465, // true for 465, false for other ports
      auth: {
        user: config.mail.username,
        pass: config.mail.password,
      },
      tls: {
        rejectUnauthorized: false, // Allow self-signed certificates
      },
    });

    // Verify connection
    this.verifyConnection();
  }

  /**
   * Verify email connection
   */
  private async verifyConnection() {
    try {
      await this.transporter.verify();
      logger.info('Email service connected successfully');
    } catch (error) {
      logger.error('Email service connection failed:', error);
    }
  }

  /**
   * Send password reset email
   */
  async sendPasswordReset(email: string, resetToken: string): Promise<void> {
    try {
      const resetUrl = `${config.app.baseUrl}/auth/reset-password/${resetToken}`;

      const mailOptions = {
        from: config.mail.defaultSender,
        to: email,
        subject: 'Set2Tracks - Password Reset Request',
        html: `
          <!DOCTYPE html>
          <html>
          <head>
            <meta charset="utf-8">
            <style>
              body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
              .container { max-width: 600px; margin: 0 auto; padding: 20px; }
              .button {
                display: inline-block;
                padding: 12px 24px;
                background-color: #4F46E5;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
              }
              .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }
            </style>
          </head>
          <body>
            <div class="container">
              <h2>Password Reset Request</h2>
              <p>You requested to reset your password for your Set2Tracks account.</p>
              <p>Click the button below to reset your password:</p>
              <a href="${resetUrl}" class="button">Reset Password</a>
              <p>Or copy and paste this link into your browser:</p>
              <p><a href="${resetUrl}">${resetUrl}</a></p>
              <p>This link will expire in 1 hour.</p>
              <p>If you didn't request this, please ignore this email.</p>
              <div class="footer">
                <p>Set2Tracks - DJ Set Tracklist Generator</p>
              </div>
            </div>
          </body>
          </html>
        `,
        text: `
Password Reset Request

You requested to reset your password for your Set2Tracks account.

Click this link to reset your password:
${resetUrl}

This link will expire in 1 hour.

If you didn't request this, please ignore this email.

---
Set2Tracks - DJ Set Tracklist Generator
        `,
      };

      await this.transporter.sendMail(mailOptions);
      logger.info(`Password reset email sent to: ${email}`);
    } catch (error) {
      logger.error(`Error sending password reset email to ${email}:`, error);
      throw error;
    }
  }

  /**
   * Send set processing notification
   */
  async sendSetProcessed(email: string, setTitle: string, setId: number): Promise<void> {
    try {
      const setUrl = `${config.app.baseUrl}/set/${setId}`;

      const mailOptions = {
        from: config.mail.defaultSender,
        to: email,
        subject: `Set2Tracks - Your set is ready: ${setTitle}`,
        html: `
          <!DOCTYPE html>
          <html>
          <head>
            <meta charset="utf-8">
            <style>
              body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
              .container { max-width: 600px; margin: 0 auto; padding: 20px; }
              .button {
                display: inline-block;
                padding: 12px 24px;
                background-color: #10B981;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
              }
              .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }
            </style>
          </head>
          <body>
            <div class="container">
              <h2>🎵 Your Set is Ready!</h2>
              <p>Great news! We've finished processing your DJ set:</p>
              <h3>${setTitle}</h3>
              <p>Click below to view the tracklist:</p>
              <a href="${setUrl}" class="button">View Tracklist</a>
              <p>Or visit: <a href="${setUrl}">${setUrl}</a></p>
              <div class="footer">
                <p>Set2Tracks - DJ Set Tracklist Generator</p>
              </div>
            </div>
          </body>
          </html>
        `,
        text: `
🎵 Your Set is Ready!

Great news! We've finished processing your DJ set:

${setTitle}

View the tracklist here:
${setUrl}

---
Set2Tracks - DJ Set Tracklist Generator
        `,
      };

      await this.transporter.sendMail(mailOptions);
      logger.info(`Set processed notification sent to: ${email}`);
    } catch (error) {
      logger.error(`Error sending set processed email to ${email}:`, error);
      throw error;
    }
  }

  /**
   * Send welcome email
   */
  async sendWelcome(email: string, name: string): Promise<void> {
    try {
      const mailOptions = {
        from: config.mail.defaultSender,
        to: email,
        subject: 'Welcome to Set2Tracks! 🎵',
        html: `
          <!DOCTYPE html>
          <html>
          <head>
            <meta charset="utf-8">
            <style>
              body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
              .container { max-width: 600px; margin: 0 auto; padding: 20px; }
              .button {
                display: inline-block;
                padding: 12px 24px;
                background-color: #4F46E5;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
              }
              .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }
            </style>
          </head>
          <body>
            <div class="container">
              <h2>Welcome to Set2Tracks, ${name}! 🎵</h2>
              <p>Thanks for joining Set2Tracks, the ultimate DJ set tracklist generator!</p>
              <p>Here's what you can do:</p>
              <ul>
                <li>🎵 Submit any DJ set from YouTube and get a complete tracklist</li>
                <li>🔍 Browse thousands of tracks and discover new music</li>
                <li>📝 Create Spotify playlists from your favorite sets</li>
                <li>🎧 Follow channels and get notified when new sets are uploaded</li>
              </ul>
              <a href="${config.app.baseUrl}" class="button">Get Started</a>
              <div class="footer">
                <p>Set2Tracks - DJ Set Tracklist Generator</p>
              </div>
            </div>
          </body>
          </html>
        `,
        text: `
Welcome to Set2Tracks, ${name}! 🎵

Thanks for joining Set2Tracks, the ultimate DJ set tracklist generator!

Here's what you can do:
- Submit any DJ set from YouTube and get a complete tracklist
- Browse thousands of tracks and discover new music
- Create Spotify playlists from your favorite sets
- Follow channels and get notified when new sets are uploaded

Get started: ${config.app.baseUrl}

---
Set2Tracks - DJ Set Tracklist Generator
        `,
      };

      await this.transporter.sendMail(mailOptions);
      logger.info(`Welcome email sent to: ${email}`);
    } catch (error) {
      logger.error(`Error sending welcome email to ${email}:`, error);
      // Don't throw - welcome email is not critical
    }
  }

  /**
   * Send invite email
   */
  async sendInvite(email: string, inviteCode: string): Promise<void> {
    try {
      const inviteUrl = `${config.app.baseUrl}/auth/register?invite=${inviteCode}`;

      const mailOptions = {
        from: config.mail.defaultSender,
        to: email,
        subject: "You're invited to Set2Tracks! 🎵",
        html: `
          <!DOCTYPE html>
          <html>
          <head>
            <meta charset="utf-8">
            <style>
              body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
              .container { max-width: 600px; margin: 0 auto; padding: 20px; }
              .button {
                display: inline-block;
                padding: 12px 24px;
                background-color: #10B981;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
              }
              .code {
                background: #f3f4f6;
                padding: 10px 15px;
                border-radius: 5px;
                font-family: monospace;
                font-size: 18px;
              }
              .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }
            </style>
          </head>
          <body>
            <div class="container">
              <h2>You've been invited to Set2Tracks! 🎵</h2>
              <p>Someone has invited you to join Set2Tracks, the DJ set tracklist generator!</p>
              <p>Your invite code:</p>
              <div class="code">${inviteCode}</div>
              <a href="${inviteUrl}" class="button">Accept Invitation</a>
              <p>Or visit: <a href="${inviteUrl}">${inviteUrl}</a></p>
              <div class="footer">
                <p>Set2Tracks - DJ Set Tracklist Generator</p>
              </div>
            </div>
          </body>
          </html>
        `,
        text: `
You've been invited to Set2Tracks! 🎵

Someone has invited you to join Set2Tracks, the DJ set tracklist generator!

Your invite code: ${inviteCode}

Accept your invitation:
${inviteUrl}

---
Set2Tracks - DJ Set Tracklist Generator
        `,
      };

      await this.transporter.sendMail(mailOptions);
      logger.info(`Invite email sent to: ${email}`);
    } catch (error) {
      logger.error(`Error sending invite email to ${email}:`, error);
      throw error;
    }
  }
}

export default new EmailService();
