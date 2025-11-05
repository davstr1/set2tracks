import { User } from '@prisma/client';

/**
 * Passport Authentication Types
 */

export interface PassportDoneCallback {
  (error: Error | null, user?: User | false, info?: { message: string }): void;
}

export interface PassportLocalCallback {
  (err: Error | null, user: User | false, info?: { message: string }): void;
}

export interface PassportGoogleCallback {
  (err: Error | null, user: User | false, info?: { message: string }): void;
}

export interface PassportSerializeCallback {
  (err: Error | null, id?: number): void;
}

export interface PassportDeserializeCallback {
  (err: Error | null, user?: User | false): void;
}
