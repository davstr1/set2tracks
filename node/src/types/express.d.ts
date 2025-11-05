import { User as PrismaUser } from '@prisma/client';

/**
 * Express type augmentation
 * Extends Express types with custom properties
 */

declare global {
  namespace Express {
    interface User extends PrismaUser {}
  }
}

export {};
