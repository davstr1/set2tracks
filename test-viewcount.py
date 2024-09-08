



import json
from web.lib.youtube import youbube_video_info


inf = youbube_video_info('dQw4w9WgXcQ')

with open('vid_inf.json', 'w') as file:
    json.dump(inf, file, indent=4)