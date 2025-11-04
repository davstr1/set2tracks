import passport from 'passport';
import { Strategy as LocalStrategy } from 'passport-local';
import { Strategy as GoogleStrategy } from 'passport-google-oauth20';
import { PrismaClient, User } from '@prisma/client';
import config from '../config';
import PasswordUtils from '../utils/password';
import logger from '../utils/logger';

const prisma = new PrismaClient();

/**
 * Serialize user for session
 */
passport.serializeUser((user: any, done) => {
  done(null, user.id);
});

/**
 * Deserialize user from session
 */
passport.deserializeUser(async (id: number, done) => {
  try {
    const user = await prisma.user.findUnique({ where: { id } });
    done(null, user);
  } catch (error) {
    logger.error('Error deserializing user:', error);
    done(error, null);
  }
});

/**
 * Local Strategy (Email + Password)
 */
passport.use(
  new LocalStrategy(
    {
      usernameField: 'email',
      passwordField: 'password',
    },
    async (email, password, done) => {
      try {
        // Find user by email
        const user = await prisma.user.findUnique({
          where: { email: email.toLowerCase() },
        });

        if (!user) {
          return done(null, false, { message: 'Invalid email or password' });
        }

        // Verify password
        const isValid = await PasswordUtils.compare(password, user.password);

        if (!isValid) {
          return done(null, false, { message: 'Invalid email or password' });
        }

        // Update last login
        await prisma.user.update({
          where: { id: user.id },
          data: { lastLogin: new Date() },
        });

        logger.info(`User logged in: ${user.email}`);
        return done(null, user);
      } catch (error) {
        logger.error('Error in local strategy:', error);
        return done(error);
      }
    }
  )
);

/**
 * Google OAuth Strategy
 */
if (config.oauth.google.clientId && config.oauth.google.clientSecret) {
  passport.use(
    new GoogleStrategy(
      {
        clientID: config.oauth.google.clientId,
        clientSecret: config.oauth.google.clientSecret,
        callbackURL: config.oauth.google.callbackUrl,
      },
      async (accessToken, refreshToken, profile, done) => {
        try {
          const email = profile.emails?.[0]?.value;

          if (!email) {
            return done(new Error('No email from Google'), undefined);
          }

          // Check if user exists
          let user = await prisma.user.findUnique({
            where: { email: email.toLowerCase() },
          });

          if (user) {
            // User exists, update last login
            user = await prisma.user.update({
              where: { id: user.id },
              data: { lastLogin: new Date() },
            });

            // Update or create OAuth record
            await prisma.oAuth.upsert({
              where: {
                provider_providerId: {
                  provider: 'google',
                  providerId: profile.id,
                },
              },
              update: {
                token: accessToken,
                tokenSecret: refreshToken,
              },
              create: {
                provider: 'google',
                providerId: profile.id,
                token: accessToken,
                tokenSecret: refreshToken,
                userId: user.id,
              },
            });

            logger.info(`User logged in via Google: ${user.email}`);
            return done(null, user);
          } else {
            // Create new user
            const name = profile.displayName || email.split('@')[0];

            user = await prisma.user.create({
              data: {
                email: email.toLowerCase(),
                fname: name,
                password: '', // No password for OAuth users
                type: 'User',
                connectMethod: 'Google',
                lastLogin: new Date(),
              },
            });

            // Create OAuth record
            await prisma.oAuth.create({
              data: {
                provider: 'google',
                providerId: profile.id,
                token: accessToken,
                tokenSecret: refreshToken,
                userId: user.id,
              },
            });

            logger.info(`New user created via Google: ${user.email}`);
            return done(null, user);
          }
        } catch (error) {
          logger.error('Error in Google OAuth strategy:', error);
          return done(error as Error, undefined);
        }
      }
    )
  );
}

export default passport;
