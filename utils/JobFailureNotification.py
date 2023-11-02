import os

import yaml
import logging

from twisted.internet import threads
from twisted.internet.defer import inlineCallbacks

from domain.Bangumi import Bangumi
from domain.Episode import Episode
from domain.VideoFile import VideoFile
from domain.User import User
from sqlalchemy import exc
from sqlalchemy.orm import joinedload
from sender import Mail, Message
from jinja2 import Environment, FileSystemLoader
from utils.SessionManager import SessionManager
from utils.db import row2dict

logger = logging.getLogger(__name__)

isDebug = os.getenv('DEBUG', False)

if isDebug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)


class JobFailureNotification:

    def __init__(self):
        fr = open('./config/config.yml', 'r')
        config = yaml.load(fr)
        self.mail_config = config['mail']
        self.mail = Mail(self.mail_config['mail_server'],
                         port=self.mail_config['mail_port'],
                         username=self.mail_config['mail_username'],
                         password=self.mail_config['mail_password'],
                         use_tls=self.mail_config['mail_use_tls'],
                         use_ssl=self.mail_config['mail_use_ssl'])

        self.mail.fromaddr = ('Video Job Manager', self.mail_config['mail_default_sender'])
        # root path of site
        self.root_path = '{0}://{1}'.format(config['site']['protocol'], config['site']['host'])
        # mail template
        # tfr = open('./templates/download-status-alert.html', 'r')
        env = Environment(
            loader=FileSystemLoader('./templates')
        )
        self.mail_template = env.get_template('job-failure-notification.html')

    @inlineCallbacks
    def send_notification(self, job):
        yield threads.deferToThread(self.__send_notification, job)

    def __send_notification(self, job):
        session = SessionManager.Session()
        try:
            video_file = session.query(VideoFile).\
                options(joinedload(VideoFile.episode)).\
                options(joinedload(VideoFile.bangumi).joinedload(Bangumi.maintained_by)).\
                filter(VideoFile.id==job.get('video_id')).\
                one()

            if video_file is None:
                logger.warn('cannot find the video_file record of video_id: {0}'.format(job.get('video_id')))
                return
            if video_file.bangumi.maintained_by is None:
                logger.warn('No maintainer for this bangumi')
                return

            maintainer = row2dict(video_file.bangumi.maintained_by, User)
            bangumi_dict = row2dict(video_file.bangumi, Bangumi)
            bangumi_dict['url'] = '{0}/admin/bangumi/{1}'.format(self.root_path, bangumi_dict['id'])
            episode_dict = row2dict(video_file.episode, Episode)
            job['url'] = '{0}/admin/video-manager/{1}'.format(self.root_path, job.get('id'))
            msg = Message('A Video Job Failed', fromaddr=('Video Job Manager', self.mail_config['mail_default_sender']))
            msg.html = self.mail_template.render(maintainer=maintainer, bangumi_dict=bangumi_dict, episode_dict=episode_dict, job_dict=job)
            msg.to = maintainer['email']
            self.mail.send(msg)
        except Exception as error:
            logger.error(error)
        finally:
            SessionManager.Session.remove()


job_failure_notification = JobFailureNotification()
