# for video related operations
import subprocess32 as subprocess
import logging
import os, errno

logger = logging.getLogger(__name__)


class VideoManager:

    def __init__(self):
        self.base_path = None

    def set_base_path(self, path):
        self.base_path = path

    def create_thumbnail(self, video_path, time, output_path):
        try:
            subprocess.check_call('ffmpeg -y -ss %s -i "%s" -vframes 1 "%s"' % (time, video_path, output_path), shell=True)
            return True
        except subprocess.CalledProcessError as error:
            logger.warn(error)
            return False


    def create_episode_thumbnail(self, episode, relative_path, time):
        bangumi_id = str(episode.bangumi_id)
        video_path = '{0}/{1}/{2}'.format(self.base_path, bangumi_id, relative_path.encode('utf-8'))
        thumbnail_folder = '{0}/{1}/thumbnails'.format(self.base_path, bangumi_id)
        output_path = '{0}/{1}.png'.format(thumbnail_folder, str(episode.episode_no))
        try:
            if not os.path.exists(thumbnail_folder):
                os.makedirs(thumbnail_folder)
                logger.info('create base dir %s successfully', thumbnail_folder)
        except OSError as exception:
            if exception.errno == errno.EACCES:
                # permission denied
                raise exception
            else:
                logger.error(exception)

        return self.create_thumbnail(video_path, time, output_path)


video_manager = VideoManager()
