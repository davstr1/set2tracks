/**
 * Shazam API Response Types
 * Based on node-shazam library responses
 */

export interface ShazamMetadataItem {
  title?: string;
  text?: string;
}

export interface ShazamSection {
  type?: string;
  metadata?: ShazamMetadataItem[];
  metapages?: Array<{
    image?: string;
    caption?: string;
  }>;
  tabname?: string;
  text?: string[];
}

export interface ShazamProvider {
  type: string;
  actions?: Array<{
    type?: string;
    uri?: string;
    name?: string;
  }>;
}

export interface ShazamHub {
  type?: string;
  image?: string;
  actions?: Array<{
    type?: string;
    uri?: string;
    name?: string;
  }>;
  options?: Array<{
    caption?: string;
    actions?: Array<{
      type?: string;
      uri?: string;
    }>;
  }>;
  providers?: ShazamProvider[];
  explicit?: boolean;
  displayname?: string;
}

export interface ShazamArtist {
  id?: string;
  adamid?: string;
}

export interface ShazamTrack {
  key?: string;
  title?: string;
  subtitle?: string;
  share?: {
    subject?: string;
    text?: string;
    href?: string;
    image?: string;
    twitter?: string;
    html?: string;
    avatar?: string;
    snapchat?: string;
  };
  images?: {
    background?: string;
    coverart?: string;
    coverarthq?: string;
    joecolor?: string;
  };
  hub?: ShazamHub;
  url?: string;
  artists?: ShazamArtist[];
  isrc?: string;
  genres?: {
    primary?: string;
  };
  sections?: ShazamSection[];
  type?: string;
  alias?: string;
  urlparams?: {
    [key: string]: string;
  };
  myshazam?: boolean;
  highlightsurls?: {
    artisthighlightsurl?: string;
    trackhighlighturl?: string;
  };
  relatedtracksurl?: string;
  albumadamid?: string;
}

export interface ShazamMatch {
  id?: string;
  offset?: number;
  timeskew?: number;
  frequencyskew?: number;
}

export interface ShazamResponse {
  track?: ShazamTrack;
  tagid?: string;
  matches?: ShazamMatch[];
  timestamp?: number;
  timezone?: string;
  location?: {
    accuracy?: number;
  };
}

export interface RecognitionResult {
  success: boolean;
  track?: {
    title: string;
    artist: string;
    album?: string;
    label?: string;
    releaseYear?: number;
    genre?: string;
    isrc?: string;
    spotifyId?: string;
    coverArt?: string;
  };
  error?: string;
  confidence?: number;
}
