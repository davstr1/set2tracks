import { Router } from 'express';
import channelController from '../controllers/channel.controller';
import { validateRequest } from '../middleware/validation';
import {
  getChannelByIdValidator,
  browseChannelValidator,
} from '../validators/channel.validator';

const router = Router();

// HTML Pages
router.get('/', validateRequest(browseChannelValidator), channelController.getChannels.bind(channelController));
router.get('/:id', validateRequest(getChannelByIdValidator), channelController.getChannelById.bind(channelController));

// API Endpoints
router.get('/api/channels', validateRequest(browseChannelValidator), channelController.getChannelsApi.bind(channelController));
router.get('/api/channels/popular', validateRequest(browseChannelValidator), channelController.getPopularChannels.bind(channelController));
router.get('/api/channels/search', validateRequest(browseChannelValidator), channelController.searchChannels.bind(channelController));
router.get('/api/channels/:id', validateRequest(getChannelByIdValidator), channelController.getChannelByIdApi.bind(channelController));
router.get('/api/channels/:id/sets', validateRequest(getChannelByIdValidator), channelController.getChannelSets.bind(channelController));

export default router;
