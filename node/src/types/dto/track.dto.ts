/**
 * Track DTOs
 * Data Transfer Objects for tracks
 */

import { GenreDto } from './set.dto';

/**
 * Minimal set info embedded in track
 */
export interface TrackSetDto {
  id: number;
  videoId: string;
  title: string;
  publishDate: Date | null;
  thumbnail: string | null;
  channel: {
    id: number;
    author: string | null;
  } | null;
}

/**
 * Basic track info (for lists)
 */
export interface TrackListDto {
  id: number;
  title: string;
  artistName: string | null;
  label: string | null;
  album: string | null;
  releaseDate: Date | null;
  keyTrackSpotify: string | null;
  nbSets: number;
  genres?: GenreDto[];
}

/**
 * Full track details (for single track view)
 */
export interface TrackDetailDto extends TrackListDto {
  keyTrackShazam: string | null;
  keyTrackDeezer: string | null;
  isrc: string | null;
  coverUrl: string | null;
  previewUrl: string | null;
  sets: Array<{
    pos: number;
    set: TrackSetDto;
  }>;
  createdAt: Date;
  updatedAt: Date;
}

/**
 * Track with related tracks
 */
export interface TrackWithRelatedDto {
  track: TrackListDto;
  relatedTracks: Array<{
    id: number;
    title: string;
    artistName: string | null;
    insertionOrder: number;
  }>;
}

/**
 * Track search/filter result
 */
export interface TrackSearchDto {
  track: TrackListDto;
  relevance?: number;
}
