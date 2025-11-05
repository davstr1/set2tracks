/**
 * Channel Mappers
 * Functions to map database entities to Channel DTOs
 */

import { Channel } from '@prisma/client';
import { ChannelListDto, ChannelDetailDto } from '../types/dto';
import { mapToSetListDto } from './set.mapper';

/**
 * Map channel entity to list DTO (minimal info)
 */
export function mapToChannelListDto(channel: Channel): ChannelListDto {
  return {
    id: channel.id,
    channelId: channel.channelId,
    author: channel.author,
    avatar: channel.avatar,
    channelUrl: channel.channelUrl,
    channelFollowerCount: channel.channelFollowerCount,
    nbSets: channel.nbSets,
    followable: channel.followable,
    hidden: channel.hidden,
  };
}

/**
 * Map channel entity with sets to detail DTO
 */
export function mapToChannelDetailDto(
  channel: Channel & {
    sets?: any[];
  }
): ChannelDetailDto {
  return {
    ...mapToChannelListDto(channel),
    sets: channel.sets ? channel.sets.map(mapToSetListDto) : [],
    createdAt: channel.createdAt,
    updatedAt: channel.updatedAt,
  };
}
