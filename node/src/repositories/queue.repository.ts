import { SetQueue, Prisma } from '@prisma/client';
import { BaseRepository } from './base.repository';

/**
 * Queue Repository
 * Handles all database operations for set processing queue
 */
export class QueueRepository extends BaseRepository<SetQueue> {
  constructor() {
    super('setQueue');
  }

  /**
   * Find queue item by video ID
   */
  async findByVideoId(videoId: string): Promise<SetQueue | null> {
    return this.prisma.setQueue.findUnique({
      where: { videoId },
    });
  }

  /**
   * Create queue item
   */
  async createQueueItem(data: {
    videoId: string;
    userId: number | null;
    userPremium: boolean;
    status: string;
    duration?: number;
    nbChapters?: number;
    videoInfoJson?: any;
    sendEmail?: boolean;
    playSound?: boolean;
  }): Promise<SetQueue> {
    return this.prisma.setQueue.create({
      data: {
        videoId: data.videoId,
        userId: data.userId,
        userPremium: data.userPremium,
        status: data.status,
        duration: data.duration,
        nbChapters: data.nbChapters,
        videoInfoJson: data.videoInfoJson,
        sendEmail: data.sendEmail || false,
        playSound: data.playSound || false,
      },
    });
  }

  /**
   * Update queue item status
   */
  async updateStatus(id: number, status: string, errorMessage?: string): Promise<SetQueue> {
    return this.prisma.setQueue.update({
      where: { id },
      data: {
        status,
        ...(errorMessage && { errorMessage }),
        updatedAt: new Date(),
      },
    });
  }

  /**
   * Find queue items by status
   */
  async findByStatus(status: string, limit = 50): Promise<SetQueue[]> {
    return this.prisma.setQueue.findMany({
      where: { status },
      orderBy: { createdAt: 'desc' },
      take: limit,
    });
  }

  /**
   * Count queue items by status
   */
  async countByStatus(status: string): Promise<number> {
    return this.prisma.setQueue.count({
      where: { status },
    });
  }

  /**
   * Find recent queue items
   */
  async findRecent(limit: number): Promise<SetQueue[]> {
    return this.prisma.setQueue.findMany({
      take: limit,
      orderBy: { createdAt: 'desc' },
    });
  }

  /**
   * Find queue items by user
   */
  async findByUserId(userId: number, limit = 20): Promise<SetQueue[]> {
    return this.prisma.setQueue.findMany({
      where: { userId },
      orderBy: { createdAt: 'desc' },
      take: limit,
    });
  }
}

export default new QueueRepository();
