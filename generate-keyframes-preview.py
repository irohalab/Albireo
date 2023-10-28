import subprocess
from math import sqrt, ceil, floor

from utils.SessionManager import SessionManager

# Unused domain is necessary
from domain.Bangumi import Bangumi
from domain.Episode import Episode
from domain.InviteCode import InviteCode
from domain.TorrentFile import TorrentFile
from domain.User import User
from domain.base import Base
from domain.Feed import Feed
from domain.Favorites import Favorites
from domain.ServerSession import ServerSession
from domain.WatchProgress import WatchProgress
from domain.Task import Task
from domain.VideoFile import VideoFile
from domain.Image import Image
from domain.Announce import Announce
from domain.WebHook import WebHook
from domain.WebHookToken import WebHookToken

import yaml
import os

TILE_SIZE = 10
SCALE_HEIGHT = 120
FRAMES_INTERVAL = 5000
MAX_PIC_WIDTH = 16256

def query_video_files():
    fr = open('./config/config.yml', 'r')
    config = yaml.load(fr)
    download_location = config['download']['location']
    session = SessionManager.Session()
    video_file_list = session.query(VideoFile).filter(VideoFile.kf_image_path_list == None).all()
    for video_file in video_file_list:
        if video_file.status != VideoFile.STATUS_DOWNLOADED:
            continue
        video_path = download_location + '/' + str(video_file.bangumi_id) + '/' + video_file.file_path
        if os.path.exists(video_path):
            print('Found video_file: {0}'.format(video_path))
            generate_keyframes(video_file, video_path)
    session.commit()
    SessionManager.Session.remove()

def generate_keyframes(video_file, video_path):
    try:
        video_file.tile_size = TILE_SIZE
        video_file.frame_height = SCALE_HEIGHT
        video_file.frame_width = int(round(SCALE_HEIGHT * video_file.resolution_w/video_file.resolution_h))
        # if video_file.tile_size * video_file.frame_width > MAX_PIC_WIDTH:
        #     video_file.tile_size = int(floor(MAX_PIC_WIDTH/video_file.frame_width))
        image_dir_path = os.path.dirname(video_path)
        image_filename_base = 'keyframes-{0}'.format(os.path.basename(os.path.splitext(video_path)[0]))
        keyframe_image_path = image_dir_path + '/' + '{0}-%3d.jpg'.format(image_filename_base)
        subprocess.check_call(['ffmpeg','-y', '-i', video_path, '-vf',
             'select=isnan(prev_selected_t)+gte(t-prev_selected_t\\,2),scale={0}:{1},tile={2}x{2}'.format(
                 video_file.frame_width, video_file.frame_height, video_file.tile_size),
            '-an', '-vsync', '0', keyframe_image_path])

        filename_list = os.listdir(image_dir_path)
        video_file.kf_image_path_list = []
        for f in filename_list:
            filename = os.path.basename(f)
            if filename.endswith('.jpg') and filename.startswith(image_filename_base):
                video_file.kf_image_path_list.append(f)
        print('keyframe generated')
    except Exception as error:
        print(error)

query_video_files()
