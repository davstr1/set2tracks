/**
 * Track Mappers
 * Functions to map database entities to Track DTOs
 */

import { Track, Genre } from '@prisma/client';
import { TrackListDto, TrackDetailDto, TrackSetDto } from '../types/dto';
import { mapToGenreDto } from './set.mapper';

/**
 * Map set info for track DTO
 */
export function mapToTrackSetDto(trackSet: any): TrackSetDto {
  const set = trackSet.set;

  return {
    id: set.id,
    videoId: set.videoId,
    title: set.title,
    publishDate: set.publishDate,
    thumbnail: set.thumbnail,
    channel: set.channel
      ? {
          id: set.channel.id,
          author: set.channel.author,
        }
      : null,
  };
}

/**
 * Map track entity to list DTO (minimal info)
 */
export function mapToTrackListDto(
  track: Track & {
    genres?: Genre[];
  }
): TrackListDto {
  return {
    id: track.id,
    title: track.title,
    artistName: track.artistName,
    label: track.label,
    album: track.album,
    releaseDate: track.releaseDate,
    keyTrackSpotify: track.keyTrackSpotify,
    nbSets: track.nbSets,
    ...(track.genres && {
      genres: track.genres.map(mapToGenreDto),
    }),
  };
}

/**
 * Map track entity with full details to detail DTO
 */
export function mapToTrackDetailDto(
  track: Track & {
    genres?: Genre[];
    trackSets?: any[];
  }
): TrackDetailDto {
  return {
    ...mapToTrackListDto(track),
    keyTrackShazam: track.keyTrackShazam,
    keyTrackDeezer: track.keyTrackDeezer,
    isrc: track.isrc,
    coverUrl: track.coverUrl,
    previewUrl: track.previewUrl,
    sets: track.trackSets
      ? track.trackSets.map((ts) => ({
          pos: ts.pos,
          set: mapToTrackSetDto(ts),
        }))
      : [],
    createdAt: track.createdAt,
    updatedAt: track.updatedAt,
  };
}
