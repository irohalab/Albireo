import urlparse

from flask import jsonify, make_response
from datetime import date, datetime
import json
import uuid
import requests
import os
import errno
import logging
import traceback
import pickle
import yaml
import re

from requests import Request

from utils.sentry import sentry_wrapper

logger = logging.getLogger(__name__)

user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0'


epoch = datetime.utcfromtimestamp(0)


def encode_datetime(obj):
    if isinstance(obj, date):
        return obj.strftime('%Y-%m-%d')
    raise TypeError(repr(obj) + ' is not JSON serializable')


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return int((o - epoch).total_seconds() * 1000)
        elif isinstance(o, date):
            return o.strftime('%Y-%m-%d')
        elif isinstance(o, uuid.UUID):
            return str(o)
        else:
            return json.JSONEncoder.default(self, o)


def json_resp(obj, status=200):
    resp = make_response(json.dumps(obj, cls=DateTimeEncoder), status)
    resp.headers['Content-Type'] = 'application/json'
    return resp


def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except Exception as error:
        logger.warn(error)
        return False


def is_absolute_url(test_url):
    return bool(urlparse.urlparse(test_url).netloc)


class FileDownloader:

    def __init__(self):
        self.proxy = None
        config = yaml.load(open('./config/config.yml', 'r'))
        if 'bgm' in config:
            self.proxy = config['bgm'].get('proxy', None)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent
        })

    def download_file(self, url, file_path, force_https=False):
        if force_https and url.startswith('http://'):
            url = url.replace('http://', 'https://', 1)
        print(url)
        r = self.session.get(url, stream=True, proxies=self.proxy)

        if r.status_code > 399:
            r.raise_for_status()

        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)


class BangumiRequest:

    def __init__(self):
        self.proxy = None
        config = yaml.load(open('./config/config.yml', 'r'))
        if 'bgm' in config:
            self.proxy = config['bgm'].get('proxy', None)
        # persist request for accessing bangumi api
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'application/json;charset=utf-8'
        })

        session_storage_path = './.session'
        self.api_bgm_tv_session_path = session_storage_path + '/api_bgm_tv'

        try:
            if not os.path.exists(session_storage_path):
                os.makedirs(session_storage_path)
                logger.info('create session storage dir %s successfully' % session_storage_path)
        except OSError as exception:
            if exception.errno == errno.EACCES:
                raise exception
            else:
                logger.warn(exception)

    def __get_cookie_from_storage(self):
        try:
            with open(self.api_bgm_tv_session_path, 'r') as f:
                self.session.cookies = requests.utils.cookiejar_from_dict(pickle.load(f))
        except Exception as error:
            logger.warn(traceback.format_exc(error))

    def __save_cookie_to_storage(self):
        try:
            with open(self.api_bgm_tv_session_path, 'w') as f:
                pickle.dump(requests.utils.dict_from_cookiejar(self.session.cookies), f)
        except Exception as error:
            logger.warn(traceback.format_exc(error))

    def get(self, url):
        self.__get_cookie_from_storage()
        r = self.session.get(url, proxies=self.proxy)
        self.__save_cookie_to_storage()
        return r


class BangumiMoeRequest:

    def __init__(self):
        # persist request for accessing bangumi api
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'application/json;charset=utf-8'
        })

        session_storage_path = './.session'
        self.api_bgm_tv_session_path = session_storage_path + '/bangumi_moe'

        try:
            if not os.path.exists(session_storage_path):
                os.makedirs(session_storage_path)
                logger.info('create session storage dir %s successfully' % session_storage_path)
        except OSError as exception:
            if exception.errno == errno.EACCES:
                raise exception
            else:
                logger.warn(exception)

    def __get_cookie_from_storage(self):
        try:
            with open(self.api_bgm_tv_session_path, 'r') as f:
                self.session.cookies = requests.utils.cookiejar_from_dict(pickle.load(f))
        except Exception as error:
            logger.warn(traceback.format_exc(error))

    def __save_cookie_to_storage(self):
        try:
            with open(self.api_bgm_tv_session_path, 'w') as f:
                pickle.dump(requests.utils.dict_from_cookiejar(self.session.cookies), f)
        except Exception as error:
            logger.warn(traceback.format_exc(error))

    def post(self, url, payload):
        self.__get_cookie_from_storage()
        r = self.session.post(url=url, json=payload)
        self.__save_cookie_to_storage()
        return r

    def send(self, url, method, payload):
        self.__get_cookie_from_storage()
        req = Request(method, url)
        if payload is not None:
            req = Request(method=method, url=url, json=payload)
        prepped = self.session.prepare_request(req)
        r = self.session.send(prepped)
        self.__save_cookie_to_storage()
        return r


class RPCRequest:

    def __init__(self):
        config = yaml.load(open('./config/config.yml', 'r'))
        if 'rpc' in config:
            self.server_host = config['rpc']['server_host']
            self.server_port = config['rpc']['server_port']

    def send(self, method, method_args):
        try:
            requests.get('http://{0}:{1}/{2}'.format(self.server_host, self.server_port, method), params=method_args)
        except Exception as error:
            logger.error(error)
            sentry_wrapper.sentry_middleware.captureException()


bangumi_request = BangumiRequest()
bangumi_moe_request = BangumiMoeRequest()
rpc_request = RPCRequest()
