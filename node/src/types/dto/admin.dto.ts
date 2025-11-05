/**
 * Admin DTOs
 * Data Transfer Objects for administrative operations
 */

import { SetListDto, SetQueueDto } from './set.dto';
import { UserListDto } from './user.dto';

/**
 * Dashboard statistics
 */
export interface DashboardStatsDto {
  totalSets: number;
  totalTracks: number;
  totalChannels: number;
  totalUsers: number;
}

/**
 * Dashboard data
 */
export interface DashboardDto {
  stats: DashboardStatsDto;
  recentSets: SetListDto[];
  queuedSets: SetQueueDto[];
  recentUsers: UserListDto[];
}

/**
 * Queue status
 */
export interface QueueStatusDto {
  pendingQueue: SetQueueDto[];
  processingQueue: SetQueueDto[];
  failedQueue: SetQueueDto[];
}

/**
 * System statistics (detailed)
 */
export interface SystemStatsDto {
  sets: {
    total: number;
    published: number;
  };
  tracks: number;
  channels: number;
  users: number;
  queue: {
    pending: number;
    processing: number;
    failed: number;
  };
}

/**
 * Application config entry
 */
export interface AppConfigDto {
  key: string;
  value: string;
  updatedAt?: Date;
}

/**
 * Config update request
 */
export interface ConfigUpdateDto {
  key: string;
  value: string;
}

/**
 * User type update request
 */
export interface UserTypeUpdateDto {
  type: 'Admin' | 'User' | 'Guest';
}

/**
 * Set visibility toggle request
 */
export interface SetVisibilityDto {
  hidden: boolean;
}
