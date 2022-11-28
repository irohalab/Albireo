# -*- coding: utf-8 -*-
from flask import request, Blueprint

from service.auth import auth_user
from service.bangumi import bangumi_service
from service.watch import watch_service
from service.announce import announce_service
from flask_login import login_required, current_user
from domain.Favorites import Favorites
import json

from utils.exceptions import ClientError

home_api = Blueprint('home', __name__)


@home_api.route('/recent', methods=['GET'])
@login_required
def recent_update():
    days = int(request.args.get('days', 7))
    return bangumi_service.recent_update(days)


@home_api.route('/on_air', methods=['GET'])
@login_required
def on_air_bangumi():
    bangumi_type = request.args.get('type', 2)
    return bangumi_service.on_air_bangumi(current_user.id, bangumi_type)


@home_api.route('/my_bangumi', methods=['GET'])
@login_required
@auth_user(0)
def my_bangumi():
    status = int(request.args.get('status', Favorites.WATCHING))
    if status == 0:
        status = None
    return watch_service.my_favorites(current_user.id, status)


@home_api.route('/episode/<episode_id>', methods=['GET'])
@auth_user(0)
@login_required
def episode_detail(episode_id):
    return bangumi_service.episode_detail(episode_id, current_user.id)


@home_api.route('/bangumi', methods=['GET'])
@auth_user(0)
@login_required
def list_bangumi():
    page = int(request.args.get('page', 1))
    count = int(request.args.get('count', 10))
    sort_field = request.args.get('order_by', 'air_date')
    sort_order = request.args.get('sort', 'desc')
    name = request.args.get('name')
    bangumi_type = int(request.args.get('type', -1))
    return bangumi_service.list_bangumi(page=page,
                                        count=count,
                                        sort_field=sort_field,
                                        sort_order=sort_order,
                                        name=name,
                                        user_id=current_user.id,
                                        bangumi_type=bangumi_type)


@home_api.route('/bangumi/<bangumi_id>', methods=['GET'])
@auth_user(0)
@login_required
def bangumi_detail(bangumi_id):
    return bangumi_service.get_bangumi(bangumi_id, current_user.id)


@home_api.route('/announce', methods=['GET'])
@login_required
def get_available_announce():
    return announce_service.get_available_announce()


@home_api.route('/feedback', methods=['POST'])
@auth_user(0)
@login_required
def feed_back():
    data = json.loads(request.get_data(as_text=True))
    episode_id = data.get('episode_id', None)
    video_file_id = data.get('video_file_id', None)
    message = data.get('message', None)
    if not episode_id or not video_file_id:
        raise ClientError(ClientError, ClientError.INVALID_REQUEST)
    return bangumi_service.feed_back(episode_id, video_file_id, current_user, message)
