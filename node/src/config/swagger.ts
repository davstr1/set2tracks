import swaggerJsdoc from 'swagger-jsdoc';
import path from 'path';

/**
 * Swagger/OpenAPI Configuration
 *
 * This file configures the API documentation using OpenAPI 3.0 specification.
 * Documentation is automatically generated from JSDoc comments in route files.
 *
 * Access the docs at: http://localhost:3000/api-docs
 */

const options: swaggerJsdoc.Options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Set2Tracks API',
      version: '1.0.0',
      description: `
        DJ Set Tracklist Generator API

        **Set2Tracks** automatically identifies tracks in DJ sets from YouTube videos using
        Shazam recognition and enriches them with Spotify metadata.

        ## Features
        - 🎵 Queue DJ sets for automatic track identification
        - 🔍 Search through processed sets and tracks
        - 📊 Browse popular sets and channels
        - 🎧 Get detailed track information with streaming links
        - 📈 Track user browsing history

        ## Authentication
        Most endpoints require session-based authentication. Use the \`/auth/login\` endpoint
        to authenticate and receive a session cookie.
      `,
      contact: {
        name: 'Set2Tracks Support',
        url: 'https://github.com/yourusername/set2tracks',
      },
      license: {
        name: 'MIT',
        url: 'https://opensource.org/licenses/MIT',
      },
    },
    servers: [
      {
        url: 'http://localhost:3000',
        description: 'Development server',
      },
      {
        url: 'https://api.set2tracks.com',
        description: 'Production server',
      },
    ],
    tags: [
      {
        name: 'Sets',
        description: 'DJ set operations - browse, search, queue for processing',
      },
      {
        name: 'Tracks',
        description: 'Track operations - browse, search, get details',
      },
      {
        name: 'Channels',
        description: 'YouTube channel operations',
      },
      {
        name: 'Auth',
        description: 'Authentication and user management',
      },
      {
        name: 'Admin',
        description: 'Administrative operations (admin only)',
      },
      {
        name: 'Health',
        description: 'Health check and monitoring endpoints',
      },
    ],
    components: {
      securitySchemes: {
        sessionAuth: {
          type: 'apiKey',
          in: 'cookie',
          name: 'sessionId',
          description: 'Session-based authentication. Login via `/auth/login` to receive session cookie.',
        },
      },
      schemas: {
        // Pagination
        PaginationMeta: {
          type: 'object',
          properties: {
            page: { type: 'integer', example: 1 },
            limit: { type: 'integer', example: 20 },
            total: { type: 'integer', example: 150 },
            totalPages: { type: 'integer', example: 8 },
          },
        },

        // Set DTOs
        SetListDto: {
          type: 'object',
          properties: {
            id: { type: 'integer', example: 1 },
            videoId: { type: 'string', example: 'dQw4w9WgXcQ' },
            title: { type: 'string', example: 'Best House Mix 2024' },
            duration: { type: 'integer', example: 3600, description: 'Duration in seconds' },
            publishDate: { type: 'string', format: 'date-time' },
            thumbnail: { type: 'string', example: 'https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg' },
            viewCount: { type: 'integer', example: 15000 },
            likeCount: { type: 'integer', example: 1200 },
            nbTracks: { type: 'integer', example: 25 },
            channel: { $ref: '#/components/schemas/ChannelDto' },
          },
        },

        SetDetailDto: {
          type: 'object',
          properties: {
            id: { type: 'integer', example: 1 },
            videoId: { type: 'string', example: 'dQw4w9WgXcQ' },
            title: { type: 'string', example: 'Best House Mix 2024' },
            duration: { type: 'integer', example: 3600 },
            publishDate: { type: 'string', format: 'date-time' },
            thumbnail: { type: 'string' },
            viewCount: { type: 'integer', example: 15000 },
            likeCount: { type: 'integer', example: 1200 },
            nbTracks: { type: 'integer', example: 25 },
            playableInEmbed: { type: 'boolean', example: true },
            channel: { $ref: '#/components/schemas/ChannelDto' },
            tracks: {
              type: 'array',
              items: { $ref: '#/components/schemas/SetTrackDto' },
            },
          },
        },

        SetTrackDto: {
          type: 'object',
          properties: {
            pos: { type: 'integer', example: 0 },
            startTime: { type: 'integer', nullable: true },
            endTime: { type: 'integer', nullable: true },
            track: { $ref: '#/components/schemas/TrackListDto' },
          },
        },

        // Track DTOs
        TrackListDto: {
          type: 'object',
          properties: {
            id: { type: 'integer', example: 1 },
            title: { type: 'string', example: 'Levels' },
            artistName: { type: 'string', example: 'Avicii' },
            album: { type: 'string', example: 'True', nullable: true },
            releaseYear: { type: 'integer', example: 2013, nullable: true },
            nbSets: { type: 'integer', example: 45 },
            coverArtUrl: { type: 'string', nullable: true },
            previewUrl: { type: 'string', nullable: true },
          },
        },

        TrackDetailDto: {
          type: 'object',
          properties: {
            id: { type: 'integer', example: 1 },
            title: { type: 'string', example: 'Levels' },
            artistName: { type: 'string', example: 'Avicii' },
            album: { type: 'string', nullable: true },
            label: { type: 'string', nullable: true },
            releaseYear: { type: 'integer', nullable: true },
            releaseDate: { type: 'string', format: 'date', nullable: true },
            nbSets: { type: 'integer', example: 45 },
            coverArtUrl: { type: 'string', nullable: true },
            previewUrl: { type: 'string', nullable: true },
            spotifyUrl: { type: 'string', nullable: true },
            appleMusicUrl: { type: 'string', nullable: true },
            sets: {
              type: 'array',
              items: { $ref: '#/components/schemas/SetListDto' },
            },
          },
        },

        // Channel DTOs
        ChannelDto: {
          type: 'object',
          properties: {
            id: { type: 'integer', example: 1 },
            channelId: { type: 'string', example: 'UCxxxxxxxxxxxxxxx' },
            author: { type: 'string', example: 'DJ Mix Channel' },
            channelUrl: { type: 'string', example: 'https://youtube.com/c/DJMixChannel' },
            nbSets: { type: 'integer', example: 120 },
          },
        },

        ChannelDetailDto: {
          type: 'object',
          properties: {
            id: { type: 'integer', example: 1 },
            channelId: { type: 'string' },
            author: { type: 'string' },
            channelUrl: { type: 'string' },
            channelThumbnail: { type: 'string', nullable: true },
            channelBanner: { type: 'string', nullable: true },
            nbSets: { type: 'integer', example: 120 },
            channelFollowerCount: { type: 'integer', nullable: true },
            sets: {
              type: 'array',
              items: { $ref: '#/components/schemas/SetListDto' },
            },
          },
        },

        // Queue DTOs
        QueueSubmissionResult: {
          type: 'object',
          properties: {
            message: { type: 'string', example: 'Set queued for processing' },
            queueItem: {
              type: 'object',
              nullable: true,
              properties: {
                id: { type: 'integer', example: 1 },
                videoId: { type: 'string', example: 'dQw4w9WgXcQ' },
                status: { type: 'string', example: 'pending', enum: ['pending', 'processing', 'done', 'failed'] },
                createdAt: { type: 'string', format: 'date-time' },
              },
            },
            set: { $ref: '#/components/schemas/SetListDto', nullable: true },
            alreadyExists: { type: 'boolean', example: false },
          },
        },

        // Error Response
        ErrorResponse: {
          type: 'object',
          properties: {
            error: { type: 'string', example: 'Resource not found' },
            message: { type: 'string', example: 'The requested set could not be found' },
            statusCode: { type: 'integer', example: 404 },
          },
        },
      },
      responses: {
        BadRequest: {
          description: 'Bad request - invalid input',
          content: {
            'application/json': {
              schema: { $ref: '#/components/schemas/ErrorResponse' },
            },
          },
        },
        Unauthorized: {
          description: 'Unauthorized - authentication required',
          content: {
            'application/json': {
              schema: { $ref: '#/components/schemas/ErrorResponse' },
            },
          },
        },
        NotFound: {
          description: 'Resource not found',
          content: {
            'application/json': {
              schema: { $ref: '#/components/schemas/ErrorResponse' },
            },
          },
        },
        TooManyRequests: {
          description: 'Too many requests - rate limit exceeded',
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  error: { type: 'string', example: 'Too many requests' },
                  retryAfter: { type: 'integer', example: 900, description: 'Seconds until rate limit resets' },
                },
              },
            },
          },
        },
        InternalServerError: {
          description: 'Internal server error',
          content: {
            'application/json': {
              schema: { $ref: '#/components/schemas/ErrorResponse' },
            },
          },
        },
      },
      parameters: {
        pageParam: {
          name: 'page',
          in: 'query',
          description: 'Page number for pagination',
          required: false,
          schema: {
            type: 'integer',
            minimum: 1,
            default: 1,
          },
        },
        limitParam: {
          name: 'limit',
          in: 'query',
          description: 'Number of items per page',
          required: false,
          schema: {
            type: 'integer',
            minimum: 1,
            maximum: 100,
            default: 20,
          },
        },
        searchQueryParam: {
          name: 'q',
          in: 'query',
          description: 'Search query',
          required: true,
          schema: {
            type: 'string',
            minLength: 1,
          },
        },
      },
    },
  },
  // Paths to files containing OpenAPI definitions (JSDoc comments)
  apis: [
    path.join(__dirname, '../routes/*.ts'),
    path.join(__dirname, '../controllers/*.ts'),
  ],
};

export const swaggerSpec = swaggerJsdoc(options);
