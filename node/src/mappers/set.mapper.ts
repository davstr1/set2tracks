/**
 * Set Mappers
 * Functions to map database entities to Set DTOs
 */

import { Set, Channel, Track, Genre, SetQueue } from '@prisma/client';
import {
  SetListDto,
  SetDetailDto,
  SetChannelDto,
  SetTrackDto,
  SetQueueDto,
  GenreDto,
} from '../types/dto';

/**
 * Map channel entity to DTO
 */
export function mapToChannelDto(channel: Channel | null): SetChannelDto | null {
  if (!channel) return null;

  return {
    id: channel.id,
    channelId: channel.channelId,
    author: channel.author,
    avatar: channel.avatar,
  };
}

/**
 * Map genre entity to DTO
 */
export function mapToGenreDto(genre: Genre): GenreDto {
  return {
    id: genre.id,
    name: genre.name,
  };
}

/**
 * Map track with genres to DTO
 */
export function mapToSetTrackDto(trackSet: any): SetTrackDto {
  const track = trackSet.track;

  return {
    id: track.id,
    pos: trackSet.pos,
    title: track.title,
    artistName: track.artistName,
    label: track.label,
    releaseDate: track.releaseDate,
    keyTrackSpotify: track.keyTrackSpotify,
    ...(track.genres && {
      genres: track.genres.map(mapToGenreDto),
    }),
  };
}

/**
 * Map set entity to list DTO (minimal info)
 */
export function mapToSetListDto(
  set: Set & {
    channel?: Channel | null;
  }
): SetListDto {
  return {
    id: set.id,
    videoId: set.videoId,
    title: set.title,
    duration: set.duration,
    publishDate: set.publishDate,
    thumbnail: set.thumbnail,
    viewCount: set.viewCount,
    likeCount: set.likeCount,
    nbTracks: set.nbTracks,
    channel: mapToChannelDto(set.channel || null),
  };
}

/**
 * Map set entity with full details to detail DTO
 */
export function mapToSetDetailDto(
  set: Set & {
    channel?: Channel | null;
    trackSets?: any[];
  }
): SetDetailDto {
  return {
    ...mapToSetListDto(set),
    description: set.description,
    published: set.published,
    hidden: set.hidden,
    playableInEmbed: set.playableInEmbed,
    tracks: set.trackSets ? set.trackSets.map(mapToSetTrackDto) : [],
    createdAt: set.createdAt,
    updatedAt: set.updatedAt,
  };
}

/**
 * Map queue entity to DTO
 */
export function mapToSetQueueDto(queueItem: SetQueue): SetQueueDto {
  return {
    id: queueItem.id,
    videoId: queueItem.videoId,
    status: queueItem.status,
    duration: queueItem.duration,
    nbChapters: queueItem.nbChapters,
    userPremium: queueItem.userPremium,
    errorMessage: queueItem.errorMessage,
    createdAt: queueItem.createdAt,
    updatedAt: queueItem.updatedAt,
  };
}
