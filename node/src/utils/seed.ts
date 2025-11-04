import { PrismaClient } from '@prisma/client';
import logger from './logger';

const prisma = new PrismaClient();

/**
 * Database Seed Script
 * Creates the "Unknown Track" placeholder (ID: 1)
 */
async function seed() {
  try {
    logger.info('Starting database seed...');

    // Check if Unknown Track already exists
    const unknownTrack = await prisma.track.findFirst({
      where: { id: 1 },
    });

    if (unknownTrack) {
      logger.info('Unknown Track already exists, skipping seed');
      return;
    }

    // Create Unknown Track
    await prisma.track.create({
      data: {
        id: 1,
        keyTrackShazam: -1,
        keyTrackSpotify: '-',
        keyTrackApple: '-',
        title: 'Unknown Track',
        artistName: 'Unknown Artist',
        nbSets: 0,
        relatedTracksChecked: false,
      },
    });

    logger.info('✅ Unknown Track created successfully (ID: 1)');
  } catch (error) {
    logger.error('Error seeding database:', error);
    throw error;
  } finally {
    await prisma.$disconnect();
  }
}

// Run seed if called directly
if (require.main === module) {
  seed()
    .then(() => {
      logger.info('Database seed completed!');
      process.exit(0);
    })
    .catch((error) => {
      logger.error('Database seed failed:', error);
      process.exit(1);
    });
}

export default seed;
