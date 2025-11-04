# 🚀 Quick Start Guide

Get Set2Tracks Node.js up and running in 5 minutes!

## Prerequisites Check

```bash
# Check Node.js version (need >= 18)
node --version

# Check npm version (need >= 9)
npm --version

# Check PostgreSQL
psql --version

# Check Redis
redis-cli --version

# Check FFmpeg
ffmpeg -version

# Check yt-dlp
yt-dlp --version
```

If any are missing, install them first (see README.md).

## 1. Install Dependencies

```bash
cd /home/user/set2tracks-node
npm install
```

## 2. Set Up Database

### Option A: Create New Database

```bash
# Create PostgreSQL database
createdb set2tracks

# Or using psql
psql -c "CREATE DATABASE set2tracks;"
```

### Option B: Use Existing Python Database

If you already have the Python version's database, you can use the same one!

## 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your settings
nano .env
```

**Minimum required settings:**

```bash
# Database
DATABASE_URL="postgresql://username:password@localhost:5432/set2tracks"

# Application
SECRET_KEY="your-super-secret-key-min-32-characters-long"
SESSION_SECRET="another-secret-key-for-sessions"

# Redis
REDIS_HOST="localhost"
REDIS_PORT=6379

# Spotify (get from https://developer.spotify.com/)
SPOTIFY_CLIENT_ID="your-spotify-client-id"
SPOTIFY_CLIENT_SECRET="your-spotify-client-secret"

# Database Tables (usually these defaults are fine)
DB_TABLE_USERS="users"
DB_TABLE_INVITES="invites"
```

## 4. Generate Database Schema

### If using NEW database:

```bash
# Generate Prisma Client
npm run prisma:generate

# Run migrations (creates all tables)
npm run prisma:migrate
```

### If using EXISTING Python database:

```bash
# Pull schema from existing database
npm run prisma:introspect

# Generate Prisma Client
npm run prisma:generate
```

## 5. Start Services

### Start Redis (if not running)

```bash
# Ubuntu/Debian
sudo systemctl start redis

# macOS
brew services start redis

# Or manually
redis-server
```

### Start the App

```bash
# Development mode (hot reload)
npm run dev
```

You should see:

```
🚀 Set2Tracks Node.js server is running!
📍 Environment: dev
🌐 Server: http://localhost:8080
💾 Database: localhost:5432/set2tracks
🔴 Redis: localhost:6379

✨ Ready to process DJ sets!
```

## 6. Test It Out

```bash
# Check health endpoint
curl http://localhost:8080/health

# Expected response:
# {"status":"ok","timestamp":"2024-11-04T17:30:00.000Z"}
```

Open your browser: http://localhost:8080

---

## Common Issues

### Port 8080 already in use

```bash
# Change PORT in .env
PORT=3000
```

### Can't connect to Redis

```bash
# Check if Redis is running
redis-cli ping

# Should respond: PONG

# If not, start it:
redis-server
```

### Can't connect to PostgreSQL

```bash
# Check if PostgreSQL is running
pg_isready

# Start if needed:
sudo systemctl start postgresql   # Linux
brew services start postgresql     # macOS
```

### Prisma errors

```bash
# Clear and regenerate
rm -rf node_modules/.prisma
npm run prisma:generate
```

### "Missing environment variable" errors

Make sure your `.env` file is in the root directory (`/home/user/set2tracks-node/.env`)

---

## Next Steps

Now that it's running:

1. **Explore the API**: Check out `src/services/` for external API integrations
2. **Review the Schema**: Run `npm run prisma:studio` to see the database
3. **Add Routes**: Create controllers in `src/controllers/` and routes in `src/routes/`
4. **Implement Jobs**: Set up Bull jobs in `src/jobs/` for background processing
5. **Migrate Templates**: Copy templates from Python version and convert to Nunjucks

---

## Development Workflow

```bash
# Terminal 1: Run the server
npm run dev

# Terminal 2: Watch Tailwind CSS (when ready)
npm run tailwind:watch

# Terminal 3: Run Prisma Studio (optional)
npm run prisma:studio

# Terminal 4: Run job workers (when implemented)
npm run jobs:dev
```

---

## Testing API Services

### Test Spotify Service

Create `test-spotify.ts`:

```typescript
import spotifyService from './src/services/spotify.service';

async function test() {
  const tracks = await spotifyService.searchTrack('Daft Punk');
  console.log(tracks);
}

test();
```

Run: `ts-node test-spotify.ts`

### Test YouTube Service

```typescript
import youtubeService from './src/services/youtube.service';

async function test() {
  const info = await youtubeService.getVideoInfo('dQw4w9WgXcQ');
  console.log(info);
}

test();
```

---

## Building for Production

```bash
# Build TypeScript
npm run build

# Set production environment
export NODE_ENV=production

# Start production server
npm start
```

---

## Need Help?

- Check the full [README.md](./README.md)
- Review the original Python code at `/home/user/set2tracks`
- Check logs in `./logs/`

---

**You're all set! Happy coding! 🎵**
