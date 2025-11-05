/**
 * Set DTOs
 * Data Transfer Objects for DJ sets
 */

import { Timestamps } from './base.dto';

/**
 * Minimal channel info embedded in set
 */
export interface SetChannelDto {
  id: number;
  channelId: string;
  author: string | null;
  avatar: string | null;
}

/**
 * Track info embedded in set
 */
export interface SetTrackDto {
  id: number;
  pos: number;
  title: string;
  artistName: string | null;
  label: string | null;
  releaseDate: Date | null;
  keyTrackSpotify: string | null;
  genres?: GenreDto[];
}

/**
 * Genre info
 */
export interface GenreDto {
  id: number;
  name: string;
}

/**
 * Basic set info (for lists)
 */
export interface SetListDto {
  id: number;
  videoId: string;
  title: string;
  duration: number | null;
  publishDate: Date | null;
  thumbnail: string | null;
  viewCount: number | null;
  likeCount: number | null;
  nbTracks: number;
  channel: SetChannelDto | null;
}

/**
 * Full set details (for single set view)
 */
export interface SetDetailDto extends SetListDto {
  description: string | null;
  published: boolean;
  hidden: boolean;
  playableInEmbed: boolean;
  tracks: SetTrackDto[];
  createdAt: Date;
  updatedAt: Date;
}

/**
 * Set for queue/processing
 */
export interface SetQueueDto {
  id: number;
  videoId: string;
  status: string;
  duration: number | null;
  nbChapters: number;
  userPremium: boolean;
  errorMessage: string | null;
  createdAt: Date;
  updatedAt: Date;
}

/**
 * Set browsing history entry
 */
export interface SetHistoryDto {
  setId: number;
  datetime: Date;
  set: SetListDto;
}

/**
 * Queue submission result
 */
export interface QueueSubmissionResult {
  message: string;
  queueItem?: SetQueueDto;
  set?: SetListDto;
  alreadyExists: boolean;
}
