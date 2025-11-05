/**
 * Channel DTOs
 * Data Transfer Objects for YouTube channels
 */

import { SetListDto } from './set.dto';

/**
 * Basic channel info (for lists)
 */
export interface ChannelListDto {
  id: number;
  channelId: string;
  author: string | null;
  avatar: string | null;
  channelUrl: string | null;
  channelFollowerCount: number | null;
  nbSets: number;
  followable: boolean;
  hidden: boolean;
}

/**
 * Full channel details (for single channel view)
 */
export interface ChannelDetailDto extends ChannelListDto {
  sets: SetListDto[];
  createdAt: Date;
  updatedAt: Date;
}

/**
 * Channel with paginated sets
 */
export interface ChannelWithSetsDto {
  channel: ChannelListDto;
  sets: SetListDto[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

/**
 * Channel statistics
 */
export interface ChannelStatsDto {
  channelId: string;
  author: string | null;
  totalSets: number;
  totalTracks: number;
  followers: number | null;
  avgViewCount: number;
  avgLikeCount: number;
}
