# 🎵 Set2Tracks - Node.js Edition

**Automatically identify and catalog tracks from DJ set videos using Shazam music recognition**

A complete Node.js/TypeScript rewrite of the original Python/Flask Set2Tracks application. Upload a YouTube DJ set URL, and the app automatically downloads it, identifies every track using Shazam, enriches metadata with Spotify, and creates a beautiful tracklist.

---

## ⚡ Quick Start (5 Minutes)

```bash
# 1. Install dependencies
npm install

# 2. Set up environment
cp .env.example .env
nano .env  # Add your API keys (see below)

# 3. Set up database
npx prisma generate
npx prisma db push

# 4. Build Tailwind CSS
npm run tailwind:build

# 5. Start Redis (in separate terminal)
redis-server

# 6. Start the app
npm run dev

# 7. Start background worker (in separate terminal)
npm run jobs:dev

# 8. Open browser
open http://localhost:8080
```

**That's it!** You're ready to start identifying tracks from DJ sets! 🚀

---

## 🌟 Features

### ✅ **Fully Implemented**

- **🎵 Shazam Music Recognition** - Identifies tracks from audio with retry logic and rate limiting
- **🔐 Authentication** - Email/password + Google OAuth login
- **📹 YouTube Integration** - Downloads DJ set videos and extracts audio
- **✂️ Audio Segmentation** - Splits sets into segments for recognition
- **🎧 Spotify Integration** - Enriches tracks with metadata, artwork, and links
- **📧 Email Notifications** - Get notified when your set is processed
- **⚙️ Background Processing** - Bull job queue with Redis for async processing
- **🎨 Beautiful UI** - Tailwind CSS templates with responsive design
- **📊 Browse & Search** - Explore sets, tracks, and channels
- **👤 User Accounts** - Registration, login, password reset, profile
- **📱 Channel Discovery** - Find and follow YouTube DJ channels

### 🎯 **How It Works**

1. **Submit a YouTube URL** - Paste a link to a DJ set video
2. **Download & Segment** - App downloads audio and splits it into 10-second chunks
3. **Shazam Recognition** - Each segment is identified using Shazam API
4. **Spotify Enrichment** - Track metadata, artwork, and links added from Spotify
5. **Tracklist Created** - Beautiful page with full tracklist, timestamps, and links
6. **Email Notification** - Get notified when processing is complete

---

## 📋 Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| **Node.js** | >= 18.0 | Runtime environment |
| **npm** | >= 9.0 | Package manager |
| **PostgreSQL** | >= 13.0 | Primary database |
| **Redis** | >= 6.0 | Sessions & job queue |
| **FFmpeg** | Latest | Audio processing |
| **yt-dlp** | Latest | YouTube downloads |

### Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg redis-server postgresql nodejs npm
pip install yt-dlp
```

**macOS:**
```bash
brew install ffmpeg redis postgresql node
brew install yt-dlp
```

**Verify Installation:**
```bash
node --version    # Should be v18+
redis-cli ping    # Should return "PONG"
ffmpeg -version   # Should show version
yt-dlp --version  # Should show version
```

---

## 🔧 Configuration

### 1. Environment Variables

Copy `.env.example` to `.env` and fill in the required values:

```bash
cp .env.example .env
```

### 2. Required API Keys

#### **Spotify API** (Required for track metadata)
1. Go to https://developer.spotify.com/dashboard
2. Create an app
3. Copy Client ID and Client Secret to `.env`:
```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

#### **Google OAuth** (Optional - for social login)
1. Go to https://console.cloud.google.com/
2. Create OAuth 2.0 credentials
3. Add to `.env`:
```env
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_CALLBACK_URL=http://localhost:8080/auth/google/callback
```

#### **Email/SMTP** (Optional - for notifications)
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_DEFAULT_SENDER=your_email@gmail.com
```

### 3. Database Setup

**Option A: Create New Database**
```bash
# Create PostgreSQL database
createdb set2tracks

# Set DATABASE_URL in .env
DATABASE_URL="postgresql://username:password@localhost:5432/set2tracks"

# Generate Prisma client
npx prisma generate

# Push schema to database
npx prisma db push

# (Optional) Seed database
npm run prisma:seed
```

**Option B: Use Existing Python Database**
```bash
# Point to existing database in .env
DATABASE_URL="postgresql://username:password@localhost:5432/set2tracks"

# Introspect existing schema
npx prisma db pull

# Generate client
npx prisma generate
```

---

## 🚀 Running the Application

### Development Mode

You need **3 terminal windows**:

**Terminal 1: Redis**
```bash
redis-server
```

**Terminal 2: Web Server**
```bash
npm run dev
# Server starts on http://localhost:8080
```

**Terminal 3: Background Worker**
```bash
npm run jobs:dev
# Processes queued DJ sets
```

### Production Mode

```bash
# Build TypeScript
npm run build

# Build CSS
npm run tailwind:build

# Start Redis (if not running)
redis-server &

# Start web server
npm start &

# Start background worker
npm run jobs:prod &
```

### Using PM2 (Recommended for Production)

```bash
# Install PM2
npm install -g pm2

# Start all services
pm2 start npm --name "set2tracks-web" -- start
pm2 start npm --name "set2tracks-worker" -- run jobs:prod

# View logs
pm2 logs

# Stop all
pm2 stop all
```

---

## 📖 Usage Guide

### For Users

1. **Register an Account**
   - Visit http://localhost:8080/auth/register
   - Create account or use Google OAuth

2. **Submit a DJ Set**
   - Go to http://localhost:8080/set/queue
   - Paste YouTube URL (e.g., `https://www.youtube.com/watch?v=VIDEO_ID`)
   - Click "Process Set"
   - (Optional) Check "Send email when complete"

3. **View Your Set**
   - Processing takes 2-10 minutes depending on length
   - Check queue status at http://localhost:8080/admin/queue
   - When complete, view tracklist at http://localhost:8080/set/SET_ID

4. **Browse Content**
   - **All Sets**: http://localhost:8080/set
   - **All Tracks**: http://localhost:8080/track
   - **Channels**: http://localhost:8080/channel
   - **Search**: Use search bar in header

### For Admins

Access admin dashboard at http://localhost:8080/admin (requires admin account)

- View system statistics
- Manage users
- Monitor processing queue
- View application logs
- Configure settings

---

## 🗂️ Project Structure

```
set2tracks-node/
├── src/
│   ├── app.ts                 # Express app configuration
│   ├── index.ts               # Entry point
│   ├── config/                # Configuration loader
│   ├── controllers/           # Request handlers
│   │   ├── auth.controller.ts
│   │   ├── set.controller.ts
│   │   ├── track.controller.ts
│   │   ├── channel.controller.ts
│   │   └── admin.controller.ts
│   ├── routes/                # API routes
│   ├── services/              # Business logic
│   │   ├── recognition.service.ts  # Shazam integration
│   │   ├── spotify.service.ts      # Spotify API
│   │   ├── youtube.service.ts      # YouTube downloads
│   │   └── email.service.ts        # Email sending
│   ├── jobs/                  # Background jobs
│   │   ├── queue.ts           # Bull queue setup
│   │   ├── worker.ts          # Job worker
│   │   └── processors/        # Job handlers
│   ├── middleware/            # Express middleware
│   │   ├── auth.ts            # Auth guards
│   │   └── passport.ts        # Passport strategies
│   ├── views/                 # Nunjucks templates
│   │   ├── layout.njk         # Base layout
│   │   ├── auth/              # Login, register, etc.
│   │   ├── set/               # Set pages
│   │   ├── track/             # Track pages
│   │   └── channel/           # Channel pages
│   └── utils/                 # Utilities
│       ├── logger.ts          # Winston logger
│       └── password.ts        # Password hashing
├── prisma/
│   └── schema.prisma          # Database schema
├── public/                    # Static files
├── package.json               # Dependencies
├── tsconfig.json              # TypeScript config
└── tailwind.config.js         # Tailwind CSS config
```

---

## 🛠️ Available Scripts

### Development
```bash
npm run dev              # Start dev server with hot reload (port 8080)
npm run jobs:dev         # Start job worker in dev mode
```

### Building
```bash
npm run build            # Compile TypeScript to dist/
npm run tailwind:build   # Build Tailwind CSS
npm run tailwind:watch   # Watch and rebuild CSS
```

### Production
```bash
npm start                # Run compiled app (requires npm run build first)
npm run jobs:prod        # Run job worker in production
```

### Database
```bash
npm run prisma:generate  # Generate Prisma Client
npm run prisma:migrate   # Run migrations (dev)
npm run prisma:studio    # Open Prisma Studio GUI
npm run prisma:seed      # Seed database with initial data
npx prisma db push       # Push schema to database (quick)
npx prisma db pull       # Pull schema from database
```

---

## 🔍 API Endpoints

### Authentication
- `POST /auth/register` - Create account
- `POST /auth/login` - Login
- `GET /auth/logout` - Logout
- `GET /auth/google` - Google OAuth
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password/:token` - Reset password

### Sets
- `GET /set` - Browse all sets (HTML)
- `GET /set/:id` - View set detail with tracklist (HTML)
- `POST /set/queue` - Queue a YouTube video for processing
- `GET /set/search?q=query` - Search sets
- `GET /set/popular` - Popular sets
- `GET /set/recent` - Recent sets

### Tracks
- `GET /track` - Browse all tracks (HTML)
- `GET /track/:id` - View track detail (HTML)
- `GET /track/search?q=query` - Search tracks
- `GET /track/popular` - Popular tracks
- `GET /track/genre/:genre` - Tracks by genre

### Channels
- `GET /channel` - Browse YouTube channels (HTML)
- `GET /channel/:id` - View channel detail (HTML)
- `GET /channel/api/popular` - Popular channels (JSON)

### Admin (requires admin role)
- `GET /admin` - Admin dashboard
- `GET /admin/users` - Manage users
- `GET /admin/queue` - View processing queue
- `GET /admin/config` - Application configuration

---

## 🎯 Technology Stack

| Layer | Technology |
|-------|-----------|
| **Runtime** | Node.js 18+ |
| **Language** | TypeScript 5.x |
| **Web Framework** | Express.js 4.x |
| **Database** | PostgreSQL 13+ |
| **ORM** | Prisma 5.x |
| **Cache/Queue** | Redis 6+ |
| **Job Queue** | Bull 4.x |
| **Auth** | Passport.js (Local + OAuth) |
| **Templates** | Nunjucks |
| **CSS** | Tailwind CSS 3.x |
| **Music Recognition** | Shazam (node-shazam) |
| **Spotify API** | spotify-web-api-node |
| **YouTube** | yt-dlp + youtube-dl-exec |
| **Audio** | FFmpeg + fluent-ffmpeg |
| **Email** | Nodemailer |
| **Logging** | Winston |
| **i18n** | i18next |

---

## 🐛 Troubleshooting

### App Won't Start

**"Cannot find module '@prisma/client'"**
```bash
npx prisma generate
```

**"Redis connection failed"**
```bash
# Make sure Redis is running
redis-cli ping  # Should return PONG

# Start Redis
redis-server
```

**"Database connection failed"**
```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT 1"

# Verify DATABASE_URL in .env
# Make sure database exists
createdb set2tracks
```

### Processing Jobs Not Running

**Check worker is running:**
```bash
npm run jobs:dev  # In separate terminal
```

**Check Redis connection:**
```bash
redis-cli
> KEYS *  # Should show Bull queue keys
```

**Check logs:**
```bash
# Enable debug logging in .env
LOG_LEVEL=debug

# View logs
npm run dev  # Check console output
```

### Shazam Recognition Not Working

**"Cannot find module 'node-shazam'"**
```bash
npm install node-shazam
```

**Rate limiting:**
- Shazam has rate limits
- Adjust `RECOGNITION_MAX_CONCURRENT` in `.env`
- Add `RECOGNITION_RETRY_DELAY` for slower processing

### YouTube Downloads Failing

**"yt-dlp not found"**
```bash
# Install yt-dlp
pip install yt-dlp
# or
brew install yt-dlp

# Verify
yt-dlp --version
```

**Video not available:**
- Some videos are region-locked
- Try a different video
- Check video is embeddable

---

## 📊 Performance Tips

### Speed Up Processing

1. **Increase concurrency** (in `.env`):
```env
RECOGNITION_MAX_CONCURRENT=20  # Default: 10
```

2. **Use faster Redis** (Redis 7+):
```bash
brew install redis@7  # macOS
```

3. **Enable database connection pooling** (Prisma automatically does this)

4. **Run multiple workers**:
```bash
# Terminal 1
npm run jobs:prod

# Terminal 2
npm run jobs:prod  # Second worker!
```

### Reduce API Costs

1. **Cache Spotify results** - Tracks are cached in database
2. **Limit retries** - Adjust `RECOGNITION_MAX_RETRIES` in `.env`
3. **Skip failed segments** - Failed recognitions are logged but don't block

---

## 🔐 Security Checklist

Before deploying to production:

- [ ] Change `SECRET_KEY` to a random 32+ character string
- [ ] Use strong `SESSION_SECRET`
- [ ] Enable HTTPS (use nginx/Caddy as reverse proxy)
- [ ] Set `NODE_ENV=production`
- [ ] Use environment variables for all secrets (never commit `.env`)
- [ ] Enable rate limiting (add express-rate-limit)
- [ ] Set up firewall rules (only expose ports 80/443)
- [ ] Use PostgreSQL with strong password
- [ ] Enable Redis password (`requirepass` in redis.conf)
- [ ] Review CORS settings in `app.ts`
- [ ] Set up automated backups for PostgreSQL
- [ ] Monitor logs for suspicious activity

---

## 📚 Additional Resources

- **Prisma Docs**: https://www.prisma.io/docs
- **Express.js**: https://expressjs.com/
- **Shazam API**: https://github.com/shazam/shazam-api
- **Spotify Web API**: https://developer.spotify.com/documentation/web-api
- **Bull Queue**: https://optimalbits.github.io/bull/
- **Tailwind CSS**: https://tailwindcss.com/docs

---

## 🤝 Contributing

This is a personal project transcribed from Python to Node.js. If you find bugs or have suggestions:

1. Check existing issues
2. Create detailed bug reports with:
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Node version, etc.)
   - Logs/error messages

---

## 📄 License

[Same as original Set2Tracks project]

---

## 🙏 Credits

- Original Python/Flask version by [Original Author]
- Node.js/TypeScript transcription by Claude
- Music recognition powered by Shazam
- Metadata by Spotify Web API
- Built with ❤️ and TypeScript

---

## ⚡ TL;DR

```bash
npm install
cp .env.example .env  # Add your API keys
npx prisma generate && npx prisma db push
npm run tailwind:build
redis-server &
npm run dev &
npm run jobs:dev &
open http://localhost:8080
```

**You're live!** Submit a YouTube DJ set URL and watch the magic happen. 🎵✨
