import setRepository from '../../repositories/set.repository';
import trackRepository from '../../repositories/track.repository';
import channelRepository from '../../repositories/channel.repository';
import userRepository from '../../repositories/user.repository';
import queueRepository from '../../repositories/queue.repository';
import prisma from '../../utils/database';

/**
 * Admin Service
 * Business logic for administrative operations
 */
export class AdminService {
  /**
   * Get dashboard statistics
   */
  async getDashboardStats() {
    const [
      totalSets,
      totalTracks,
      totalChannels,
      totalUsers,
      recentSets,
      queuedSets,
      recentUsers,
    ] = await Promise.all([
      setRepository.count(),
      trackRepository.count(),
      channelRepository.count(),
      userRepository.count(),
      setRepository.findRecentForAdmin(10),
      queueRepository.findRecent(10),
      userRepository.findRecentUsers(10),
    ]);

    return {
      stats: {
        totalSets,
        totalTracks,
        totalChannels,
        totalUsers,
      },
      recentSets,
      queuedSets,
      recentUsers,
    };
  }

  /**
   * Get users with pagination
   */
  async getUsers(page: number, limit: number) {
    const skip = (page - 1) * limit;

    const [users, total] = await Promise.all([
      userRepository.findUsersWithPagination({ skip, take: limit }),
      userRepository.count(),
    ]);

    return {
      users,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  /**
   * Get queue status
   */
  async getQueueStatus() {
    const [pendingQueue, processingQueue, failedQueue] = await Promise.all([
      queueRepository.findByStatus('pending'),
      queueRepository.findByStatus('processing'),
      queueRepository.findByStatus('failed'),
    ]);

    return {
      pendingQueue,
      processingQueue,
      failedQueue,
    };
  }

  /**
   * Get application configuration
   */
  async getConfig() {
    const appConfig = await prisma.appConfig.findMany({
      orderBy: { key: 'asc' },
    });

    return appConfig;
  }

  /**
   * Update configuration value
   */
  async updateConfig(key: string, value: string) {
    if (!key || value === undefined) {
      throw new Error('Key and value are required');
    }

    const config = await prisma.appConfig.upsert({
      where: { key },
      update: { value },
      create: { key, value },
    });

    return { success: true, config };
  }

  /**
   * Get system statistics (API)
   */
  async getSystemStats() {
    const [
      totalSets,
      publishedSets,
      totalTracks,
      totalChannels,
      totalUsers,
      queuePending,
      queueProcessing,
      queueFailed,
    ] = await Promise.all([
      setRepository.count(),
      setRepository.count({ hidden: false, published: true }),
      trackRepository.count(),
      channelRepository.count(),
      userRepository.count(),
      queueRepository.countByStatus('pending'),
      queueRepository.countByStatus('processing'),
      queueRepository.countByStatus('failed'),
    ]);

    return {
      sets: {
        total: totalSets,
        published: publishedSets,
      },
      tracks: totalTracks,
      channels: totalChannels,
      users: totalUsers,
      queue: {
        pending: queuePending,
        processing: queueProcessing,
        failed: queueFailed,
      },
    };
  }
}

export default new AdminService();
