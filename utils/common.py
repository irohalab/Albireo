import re
from string import Template

import yaml
import os
import errno
from urlparse import urlparse
from datetime import datetime
import logging
from domain.Image import Image

from utils.db import row2dict

logger = logging.getLogger(__name__)


epoch = datetime.utcfromtimestamp(0)


class CommonUtils:

    def __init__(self):
        fr = open('./config/config.yml', 'r')
        config = yaml.load(fr)
        self.base_path = config['download']['location']
        self.image_domain = config['domain']['image']
        self.video_domain = config['domain']['video']
        self.s3_mode = False
        if 's3_public_config' in config:
            self.video_http_url_template = Template(config['s3_public_config']['video_http_url_template'])
            self.image_http_url_template = Template(config['s3_public_config']['image_http_url_template'])
            self.fallback_url_template = Template(config['s3_public_config']['fallback_url_template'])
            self.video_bucket = config['s3_public_config']['video_bucket']
            self.image_bucket = config['s3_public_config']['image_bucket']
            self.s3_mode = True

        try:
            if not os.path.exists(self.base_path):
                os.makedirs(self.base_path)
                print('create base dir {0} successfully'.format(self.base_path))
        except OSError as exception:
            if exception.errno == errno.EACCES:
                # permission denied
                raise exception
            else:
                print(exception)

    def generate_thumbnail_link(self, episode, bangumi):
        if episode.thumbnail_image is not None:
            thumbnail_url = u'/pic/{0}'.format(episode.thumbnail_image.file_path)
        else:
            thumbnail_url = '/pic/{0}/thumbnails/{1}.png'.format(str(bangumi.id), str(episode.episode_no))
        if self.image_domain is not None:
            thumbnail_url = self.image_domain + thumbnail_url
        return thumbnail_url

    def generate_video_link(self, bangumi_id, path):
        converted_path = self.convert_s3_to_http_url(path)
        if converted_path is not None:
            return converted_path
        video_link = '/video/{0}/{1}'.format(bangumi_id, path.encode('utf-8'))
        if self.video_domain is not None:
            video_link = self.video_domain + video_link
        return video_link

    def generate_keyframe_image_link(self, image_path_list):
        image_url_list = []
        for image_path in image_path_list:
            converted_path = self.convert_s3_to_http_url(image_path)
            if converted_path is not None:
                image_url_list.append(converted_path)
                continue
            image_url = '/pic/{0}'.format(image_path)
            if self.image_domain is not None:
                image_url = self.image_domain + image_url
            image_url_list.append(image_url)
        return image_url_list

    def convert_image_dict(self, image_dict):
        img_url = image_dict.get('url')
        if img_url is None:
            image_path = image_dict.get('file_path')
            if image_path is not None:
                converted_path = self.convert_s3_to_http_url(image_path)
                if converted_path is not None:
                    img_url = converted_path
                else:
                    img_url = u'/pic/{0}'.format(image_path)
        new_dict = {
            'url': img_url,
            'dominant_color': image_dict.get('dominant_color'),
            'width': image_dict.get('width'),
            'height': image_dict.get('height')
        }
        if self.image_domain is not None:
            new_dict['url'] = self.image_domain + new_dict['url']
        return new_dict

    def process_bangumi_dict(self, bangumi, bangumi_dict):
        if bangumi.cover_image is not None:
            bangumi_dict['cover_image'] = self.convert_image_dict(row2dict(bangumi.cover_image, Image))
        bangumi_dict.pop('cover_image_id', None)

    def process_episode_dict(self, episode, episode_dict):
        if episode.thumbnail_image is not None:
            episode_dict['thumbnail_image'] = self.convert_image_dict(row2dict(episode.thumbnail_image, Image))
        episode_dict.pop('thumbnail_image_id', None)

    def empty_to_none(self, dict, attr_name):
        return dict.get(attr_name, None) if dict.get(attr_name, None) else None

    def convert_s3_to_http_url(self, s3_path):
        if not self.s3_mode:
            return None
        search_result = re.search('^s3://([^/]+)/(.+)', s3_path, re.U | re.I)
        if search_result is None:
            return None
        bucket = search_result.group(1)
        key = search_result.group(2)
        if bucket == self.image_bucket:
            return self.image_http_url_template.safe_substitute(bucket=bucket, key=key)
        elif bucket == self.video_bucket:
            return self.video_http_url_template.safe_substitute(bucket=bucket, key=key)
        else:
            return self.fallback_url_template.safe_substitute(bucket=bucket, key=key)


utils = CommonUtils()
