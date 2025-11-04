# Set2Tracks - Node.js/TypeScript Version

🎵 **DJ Set Tracklist Generator** - Node.js rewrite of the Python/Flask Set2Tracks application.

This is a complete Node.js/TypeScript transcription of the original Python Set2Tracks application, designed to identify and catalog tracks from DJ set videos using Shazam, Spotify, and Apple Music APIs.

---

## 🚀 Project Status

**⚠️ IN ACTIVE DEVELOPMENT**

This is a fresh migration from Python to Node.js. Here's what's been completed:

### ✅ Completed
- [x] Project structure and TypeScript setup
- [x] Express.js server with middleware (compression, CORS, sessions)
- [x] Prisma ORM with complete database schema (migrated from SQLAlchemy)
- [x] Configuration system with environment variables
- [x] Winston logging setup
- [x] Nunjucks template engine configuration
- [x] i18next internationalization setup
- [x] Redis integration for sessions and job queue
- [x] External API service stubs (Spotify, YouTube, Shazam)
- [x] Spotify service (fully implemented)
- [x] YouTube service with yt-dlp integration
- [x] Shazam service structure (needs audio recognition implementation)

### 🚧 TODO
- [ ] Passport.js authentication (local + Google OAuth)
- [ ] Route controllers (auth, sets, tracks, playlists, admin)
- [ ] Business logic migration (set processing, track matching)
- [ ] Bull job queue for background processing
- [ ] Template migration from Jinja2 to Nunjucks
- [ ] Tailwind CSS build integration
- [ ] Chrome extension updates (point to new backend)
- [ ] Testing suite
- [ ] Production deployment configuration

---

## 📋 Prerequisites

- **Node.js**: >= 18.0.0
- **npm**: >= 9.0.0
- **PostgreSQL**: >= 13.0
- **Redis**: >= 6.0
- **FFmpeg**: Required for audio processing
- **yt-dlp**: Required for YouTube video downloads

### Installing System Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg redis-server postgresql

# macOS (with Homebrew)
brew install ffmpeg redis postgresql

# Install yt-dlp
pip install yt-dlp
# or
brew install yt-dlp
```

---

## 🛠️ Installation

### 1. Clone and Install Dependencies

```bash
cd /home/user/set2tracks-node

# Install Node.js dependencies
npm install
```

### 2. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

**Required Environment Variables:**
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Session secret key (32+ characters)
- `SPOTIFY_CLIENT_ID` & `SPOTIFY_CLIENT_SECRET`: From Spotify Developer Dashboard
- `GOOGLE_CLIENT_ID` & `GOOGLE_CLIENT_SECRET`: For OAuth (optional)
- `MAIL_*`: SMTP configuration for emails
- `REDIS_HOST` & `REDIS_PORT`: Redis connection

See `.env.example` for all available options.

### 3. Set Up Database

```bash
# Generate Prisma Client
npm run prisma:generate

# Option A: Create new database and run migrations
npm run prisma:migrate

# Option B: Pull schema from existing Python database
npm run prisma:introspect
npm run prisma:generate
```

### 4. Start Redis

```bash
# Ubuntu/Debian
sudo systemctl start redis

# macOS
brew services start redis

# Or run manually
redis-server
```

### 5. Run the Application

```bash
# Development mode (with hot reload)
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

The server will start on `http://localhost:8080`

---

## 🏗️ Architecture

### Technology Stack

| Component | Technology |
|-----------|-----------|
| **Runtime** | Node.js 18+ |
| **Language** | TypeScript 5.3+ |
| **Web Framework** | Express.js 4.18 |
| **ORM** | Prisma 5.7 |
| **Database** | PostgreSQL |
| **Template Engine** | Nunjucks (Jinja2 for Node) |
| **Authentication** | Passport.js |
| **Session Store** | Redis via connect-redis |
| **Job Queue** | Bull (Redis-backed) |
| **CSS Framework** | Tailwind CSS 3.4 |
| **i18n** | i18next |
| **Logging** | Winston |
| **Audio Processing** | fluent-ffmpeg (wraps FFmpeg) |
| **Video Download** | youtube-dl-exec (wraps yt-dlp) |
| **Music Recognition** | Shazam API (needs implementation) |
| **Music APIs** | Spotify Web API, Apple Music |

### Directory Structure

```
set2tracks-node/
├── src/
│   ├── config/           # Configuration and environment setup
│   │   └── index.ts      # Centralized config loader
│   ├── models/           # Prisma models (auto-generated)
│   ├── controllers/      # Business logic (to be implemented)
│   ├── routes/           # Express route handlers (to be implemented)
│   ├── services/         # External API integrations
│   │   ├── spotify.service.ts    # ✅ Complete
│   │   ├── youtube.service.ts    # ✅ Complete
│   │   └── shazam.service.ts     # ⚠️ Needs audio recognition
│   ├── jobs/             # Bull job processors (to be implemented)
│   ├── middleware/       # Express middleware (to be implemented)
│   ├── utils/            # Helper utilities
│   │   └── logger.ts     # Winston logger setup
│   ├── views/            # Nunjucks templates (to be migrated)
│   ├── app.ts            # Express app configuration
│   └── index.ts          # Application entry point
├── prisma/
│   └── schema.prisma     # ✅ Complete database schema
├── public/               # Static assets
│   ├── css/
│   ├── js/
│   └── images/
├── locales/              # i18n translation files (to be copied)
├── logs/                 # Application logs
├── uploads/              # User uploads
├── temp/                 # Temporary files (audio segments)
├── package.json
├── tsconfig.json
└── .env.example
```

---

## 🗄️ Database Schema

The Prisma schema includes all models from the original Python application:

- **User Management**: `User`, `OAuth`, `Invite`
- **Music**: `Track`, `Genre`, `RelatedTrack`, `TrackGenre`
- **Channels**: `Channel`
- **Sets**: `Set`, `SetQueue`, `SetBrowsingHistory`, `SetSearch`
- **Relationships**: `TrackSet` (many-to-many)
- **Config**: `AppConfig`

All indexes, relationships, and constraints from the Python SQLAlchemy models have been preserved.

---

## 📚 API Services

### Spotify Service (`src/services/spotify.service.ts`)

✅ **Fully Implemented**

```typescript
import spotifyService from './services/spotify.service';

// Search for tracks
const tracks = await spotifyService.searchTrack('Artist - Track Name');

// Get track details
const track = await spotifyService.getTrack(trackId);

// Create playlist
const playlist = await spotifyService.createPlaylist(userId, 'My Playlist', 'Description');
```

**Features:**
- Automatic token refresh (Client Credentials flow)
- Search tracks, artists, albums
- Get track details and audio features
- Create and manage playlists
- Get recommendations
- User OAuth support

### YouTube Service (`src/services/youtube.service.ts`)

✅ **Fully Implemented**

```typescript
import youtubeService from './services/youtube.service';

// Get video info
const info = await youtubeService.getVideoInfo('videoId');

// Download audio
const audioPath = await youtubeService.downloadAudio('videoId');

// Split into segments
const segments = await youtubeService.splitAudioIntoSegments(audioPath, 10);

// Cleanup
await youtubeService.cleanupVideoFiles('videoId');
```

**Features:**
- Video metadata extraction (title, duration, chapters, views, likes)
- Audio download (uses yt-dlp)
- Audio segmentation (uses FFmpeg)
- Chapter extraction
- Proxy support

### Shazam Service (`src/services/shazam.service.ts`)

⚠️ **Needs Audio Recognition Implementation**

The structure is in place, but actual audio fingerprinting needs to be implemented.

**Options for implementation:**
1. **AcrCloud API** (recommended): Commercial service with free tier
2. **AudD.io API**: Alternative music recognition service
3. **Call Python shazamio**: Use `child_process` to execute Python script
4. **Node Shazam Library**: If one exists/emerges

Current placeholder methods:
```typescript
- recognizeTrack(audioFilePath): Promise<ShazamTrack | null>
- recognizeTracks(audioFilePaths): Promise<(ShazamTrack | null)[]>
- getTrackDetails(shazamTrackId): Promise<any>
- getTrackLabel(shazamTrackId): Promise<string | null>
- getRelatedTracks(shazamTrackId): Promise<ShazamTrack[]>
```

---

## 🔄 Migration Notes

### Key Differences from Python Version

1. **Async by Nature**: Node.js is natively asynchronous, making concurrent API calls more natural
2. **Type Safety**: TypeScript provides compile-time type checking
3. **Modern ORM**: Prisma offers better type safety and developer experience than SQLAlchemy
4. **Template Engine**: Nunjucks is a direct port of Jinja2, so templates can be migrated with minimal changes
5. **Job Queue**: Bull (Redis-backed) replaces custom Python cron scripts
6. **Session Store**: Redis-backed sessions instead of Flask's default

### What Stayed the Same

- Database schema (identical to Python version)
- API integrations (Spotify, YouTube, Shazam, Apple Music)
- Business logic concepts
- Chrome extension (just needs backend URL updated)
- Tailwind CSS build process

---

## 🔧 Development

### Available Scripts

```bash
# Development
npm run dev              # Start dev server with hot reload

# Building
npm run build            # Compile TypeScript to JavaScript
npm start                # Run production build

# Database
npm run prisma:generate  # Generate Prisma Client
npm run prisma:migrate   # Run database migrations
npm run prisma:studio    # Open Prisma Studio (GUI)

# CSS
npm run tailwind:build   # Build Tailwind CSS
npm run tailwind:watch   # Watch and rebuild CSS

# Background Jobs
npm run jobs:dev         # Start job worker in development
```

### Testing

```bash
# TODO: Add testing framework
npm test
```

---

## 🐛 Known Issues & Limitations

### Current Limitations

1. **Shazam Audio Recognition**: Not yet implemented. Options:
   - Use AcrCloud or AudD.io API
   - Call Python shazamio via subprocess
   - Find/create Node.js audio fingerprinting library

2. **Authentication**: Passport.js setup not complete

3. **Controllers**: Business logic needs to be migrated from Python

4. **Templates**: Jinja2 templates need conversion to Nunjucks

5. **Job Queue**: Bull jobs not yet defined

### Python Dependencies Still Needed

- **yt-dlp**: Node.js version has limitations, so we use the Python binary
- **Possible Shazam**: Might need to call Python shazamio if no Node alternative

---

## 🚀 Deployment

### Production Checklist

- [ ] Set `NODE_ENV=production`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure PostgreSQL with connection pooling
- [ ] Set up Redis persistence
- [ ] Configure reverse proxy (Nginx/Apache)
- [ ] Set up SSL certificates
- [ ] Configure logging to external service
- [ ] Set up monitoring (PM2, New Relic, DataDog)
- [ ] Configure automated backups
- [ ] Set resource limits for FFmpeg
- [ ] Implement rate limiting

### Deployment Options

1. **Traditional VPS** (DigitalOcean, Linode, AWS EC2)
2. **Platform-as-a-Service** (Heroku, Railway, Render)
3. **Containerized** (Docker + Kubernetes)
4. **Serverless** (Not recommended due to FFmpeg/long-running processes)

---

## 📄 License

Same as original Set2Tracks project (check parent repository)

---

## 🙏 Credits

- **Original Python Version**: [Set2Tracks](../set2tracks)
- **Node.js Migration**: Fresh transcription maintaining all functionality
- **Libraries**: Express, Prisma, Passport, Bull, Nunjucks, Spotify Web API Node, and many more

---

## 📞 Support

For issues specific to the Node.js version, please open an issue in this repository.

For general Set2Tracks questions, refer to the main project documentation.

---

## 🗺️ Roadmap

### Phase 1: Core Functionality (Current)
- [x] Project setup and configuration
- [x] Database schema migration
- [x] External API services
- [ ] Authentication system
- [ ] Core routes and controllers

### Phase 2: Set Processing
- [ ] YouTube video download pipeline
- [ ] Audio segmentation
- [ ] Shazam track recognition
- [ ] Spotify/Apple Music enrichment
- [ ] Job queue for async processing

### Phase 3: User Features
- [ ] Set browsing and search
- [ ] Track discovery
- [ ] Playlist creation
- [ ] User history
- [ ] Admin dashboard

### Phase 4: Polish
- [ ] Template migration complete
- [ ] Chrome extension integration
- [ ] Testing suite
- [ ] Performance optimization
- [ ] Production deployment

---

**🔥 Let's fucking go! Life is short!** 🚀

---

*Last Updated: November 2025*
