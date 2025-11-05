/**
 * Domain Service Layer Exports
 * Centralized export for all domain service classes
 */
export { SetService } from './set.service';
export { TrackService } from './track.service';
export { ChannelService } from './channel.service';
export { AuthService } from './auth.service';
export { AdminService } from './admin.service';

// Export default instances
import setService from './set.service';
import trackService from './track.service';
import channelService from './channel.service';
import authService from './auth.service';
import adminService from './admin.service';

export default {
  set: setService,
  track: trackService,
  channel: channelService,
  auth: authService,
  admin: adminService,
};
