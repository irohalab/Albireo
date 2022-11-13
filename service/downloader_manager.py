import logging

import requests
import yaml

from domain.Bangumi import Bangumi
from domain.Episode import Episode
from domain.VideoFile import VideoFile
from utils.SessionManager import SessionManager
from utils.db import row2dict
from utils.http import json_resp

logger = logging.getLogger(__name__)


class DownloadManagerService:
    def __init__(self):
        fr = open('./config/config.yml', 'r')
        config = yaml.load(fr)
        self.download_manager_url = config['download_manager_url']

    def proxy(self, req_data):
        req_method = req_data['method']
        req_url = self.download_manager_url + req_data['url']
        if req_method == 'GET':
            params = req_data.get('params')
            return requests.get(req_url, params=params).json()
        elif req_method == 'POST':
            body = req_data.get('body')
            return requests.post(req_url, json=body).json()
        elif req_method == 'PUT':
            body = req_data.get('body')
            return requests.put(req_url, json=body).json()
        elif req_method == 'DELETE':
            params = req_data.get('params')
            return requests.delete(req_url, params=params).json()

    def enhance_file_mapping(self, file_mapping):
        video_id_list = [entry['videoId'] for entry in file_mapping]
        session = SessionManager.Session()
        try:
            result = session.query(VideoFile, Episode).\
                join(Episode).\
                filter(VideoFile.id.in_(video_id_list)).\
                filter(Episode.id == VideoFile.episode_id).\
                all()
            for entry in file_mapping:
                for video_file, episode in result:
                    entry['episode'] = row2dict(episode, Episode)

            return json_resp({'data': file_mapping, 'total': len(file_mapping)})
        finally:
            SessionManager.Session.remove()

    def get_bangumi_from_ids(self, id_list):
        session = SessionManager.Session()
        try:
            result = session.query(Bangumi).\
                filter(Bangumi.id.in_(id_list)).\
                all()
            bangumi_dict_list = []
            for bgm in result:
                bangumi = row2dict(bgm, Bangumi)
                bangumi_dict_list.append(bangumi)
            return json_resp({'data': bangumi_dict_list, 'total': len(bangumi_dict_list)})
        finally:
            SessionManager.Session.remove()


download_manager_service = DownloadManagerService()
