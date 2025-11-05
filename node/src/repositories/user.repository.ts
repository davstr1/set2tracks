import { User, Invite } from '@prisma/client';
import { BaseRepository } from './base.repository';

/**
 * User Repository
 * Handles all database operations for users and authentication
 */
export class UserRepository extends BaseRepository<User> {
  constructor() {
    super('user');
  }

  /**
   * Find user by email
   */
  async findByEmail(email: string): Promise<User | null> {
    return this.prisma.user.findUnique({
      where: { email: email.toLowerCase() },
    });
  }

  /**
   * Create user
   */
  async createUser(data: {
    email: string;
    fname: string;
    password: string;
    type?: string;
    connectMethod?: string;
    lang?: string;
  }): Promise<User> {
    return this.prisma.user.create({
      data: {
        email: data.email.toLowerCase(),
        fname: data.fname,
        password: data.password,
        type: data.type || 'User',
        connectMethod: data.connectMethod || 'Site',
        lang: data.lang || 'en',
      },
    });
  }

  /**
   * Update user password
   */
  async updatePassword(id: number, hashedPassword: string): Promise<User> {
    return this.prisma.user.update({
      where: { id },
      data: { password: hashedPassword },
    });
  }

  /**
   * Update user extra fields (for reset tokens, etc.)
   */
  async updateExtraFields(id: number, extraFields: Record<string, unknown>): Promise<User> {
    const user = await this.findById(id);
    if (!user) {
      throw new Error('User not found');
    }

    return this.prisma.user.update({
      where: { id },
      data: {
        extraFields: {
          ...((user.extraFields as Record<string, unknown>) || {}),
          ...extraFields,
        },
      },
    });
  }

  /**
   * Find user by reset token
   */
  async findByResetToken(token: string): Promise<User | null> {
    const users = await this.prisma.user.findMany();
    return users.find((u) => {
      const extraFields = u.extraFields as Record<string, unknown> | null;
      if (!extraFields?.resetToken) return false;
      if (extraFields.resetToken !== token) return false;
      if (extraFields.resetTokenExpiry && new Date(extraFields.resetTokenExpiry as string) < new Date()) {
        return false;
      }
      return true;
    }) || null;
  }

  /**
   * Update user type (admin/user/guest)
   */
  async updateUserType(id: number, type: string): Promise<User> {
    return this.prisma.user.update({
      where: { id },
      data: { type },
    });
  }

  /**
   * Find recent users
   */
  async findRecentUsers(limit: number): Promise<User[]> {
    return this.prisma.user.findMany({
      take: limit,
      orderBy: { createdAt: 'desc' },
    });
  }

  /**
   * Find users with pagination
   */
  async findUsersWithPagination(options: {
    skip: number;
    take: number;
  }): Promise<User[]> {
    return this.prisma.user.findMany({
      orderBy: { createdAt: 'desc' },
      skip: options.skip,
      take: options.take,
    });
  }

  // Invite operations

  /**
   * Find invite by code
   */
  async findInviteByCode(inviteCode: string): Promise<Invite | null> {
    return this.prisma.invite.findUnique({
      where: { inviteCode },
    });
  }

  /**
   * Delete invite
   */
  async deleteInvite(inviteCode: string): Promise<Invite> {
    return this.prisma.invite.delete({
      where: { inviteCode },
    });
  }

  // Browsing history

  /**
   * Record set browsing history
   */
  async recordSetBrowsingHistory(userId: number, setId: number): Promise<void> {
    await this.prisma.setBrowsingHistory.upsert({
      where: {
        setId_userId: {
          setId,
          userId,
        },
      },
      update: {
        datetime: new Date(),
      },
      create: {
        setId,
        userId,
        datetime: new Date(),
      },
    });
  }

  /**
   * Find user browsing history
   */
  async findBrowsingHistory(userId: number, limit: number): Promise<any[]> {
    return this.prisma.setBrowsingHistory.findMany({
      where: { userId },
      include: {
        set: {
          include: {
            channel: true,
          },
        },
      },
      orderBy: {
        datetime: 'desc',
      },
      take: limit,
    });
  }

  // Search history

  /**
   * Record search query
   */
  async recordSearchQuery(query: string, nbResults: number): Promise<void> {
    await this.prisma.setSearch.upsert({
      where: { query },
      update: {
        nbResults,
        updatedAt: new Date(),
      },
      create: {
        query,
        nbResults,
      },
    });
  }
}

export default new UserRepository();
