/**
 * YouTube / yt-dlp Response Types
 */

export interface YtDlpChapter {
  title: string;
  start_time: number;
  end_time: number;
}

export interface YtDlpThumbnail {
  url: string;
  preference?: number;
  id?: string;
  height?: number;
  width?: number;
  resolution?: string;
}

export interface YtDlpFormat {
  format_id: string;
  url: string;
  ext: string;
  format_note?: string;
  acodec?: string;
  vcodec?: string;
  width?: number;
  height?: number;
  fps?: number;
  abr?: number;
  vbr?: number;
  filesize?: number;
  quality?: number;
}

export interface YtDlpPayload {
  id: string;
  title: string;
  description?: string;
  duration?: number;
  upload_date?: string;
  uploader?: string;
  uploader_id?: string;
  uploader_url?: string;
  channel?: string;
  channel_id?: string;
  channel_url?: string;
  channel_follower_count?: number;
  thumbnail?: string;
  thumbnails?: YtDlpThumbnail[];
  view_count?: number;
  like_count?: number;
  dislike_count?: number;
  average_rating?: number;
  age_limit?: number;
  webpage_url?: string;
  categories?: string[];
  tags?: string[];
  playable_in_embed?: boolean;
  live_status?: string;
  availability?: string;
  formats?: YtDlpFormat[];
  chapters?: YtDlpChapter[];
  requested_formats?: YtDlpFormat[];
  format?: string;
  format_id?: string;
  ext?: string;
  protocol?: string;
  language?: string;
  subtitles?: {
    [key: string]: Array<{
      ext: string;
      url: string;
      name?: string;
    }>;
  };
  automatic_captions?: {
    [key: string]: Array<{
      ext: string;
      url: string;
    }>;
  };
}

export interface VideoInfo {
  videoId: string;
  title: string;
  description: string;
  duration: number;
  uploadedAt: Date;
  channelId: string;
  channelName: string;
  thumbnail: string;
  viewCount: number;
  likeCount: number;
  isEmbeddable: boolean;
  chapters?: Array<{
    title: string;
    startTime: number;
    endTime: number;
    durationSeconds: number;
  }>;
}

export interface ChannelInfo {
  channelId: string;
  name: string;
  url: string;
  subscribers: number;
}

export interface PlaylistVideo {
  videoId: string;
  title: string;
  duration?: number;
  thumbnail?: string;
  uploadDate?: string;
}

export interface PlaylistInfo {
  playlistId: string;
  title: string;
  description?: string;
  videos: PlaylistVideo[];
}
