import { Router } from 'express';
import channelController from '../controllers/channel.controller';

const router = Router();

// HTML Pages
router.get('/', channelController.getChannels.bind(channelController));
router.get('/:id', channelController.getChannelById.bind(channelController));

// API Endpoints
router.get('/api/channels', channelController.getChannelsApi.bind(channelController));
router.get('/api/channels/popular', channelController.getPopularChannels.bind(channelController));
router.get('/api/channels/search', channelController.searchChannels.bind(channelController));
router.get('/api/channels/:id', channelController.getChannelByIdApi.bind(channelController));
router.get('/api/channels/:id/sets', channelController.getChannelSets.bind(channelController));

export default router;
