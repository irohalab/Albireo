from flask import Blueprint, request

from domain.Announce import Announce
from service.announce import announce_service
from flask_login import login_required
from service.auth import auth_user
from domain.User import User
import json

announce_api = Blueprint('announce', __name__)


@announce_api.route('', methods=['GET'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def list_all():
    position = int(request.args.get('position', Announce.POSITION_BANNER))
    offset = int(request.args.get('offset', 0))
    count = int(request.args.get('count', 10))
    content = request.args.get('content')  # for query bangumi id
    return announce_service.get_all_announce(position, offset, count, content)


@announce_api.route('', methods=['POST'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def add_announce():
    announce_dict = json.loads(request.get_data(as_text=True))
    return announce_service.add_announce(announce_dict)


@announce_api.route('/<announce_id>', methods=['DELETE'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def delete_announce(announce_id):
    return announce_service.delete_announce(announce_id)


@announce_api.route('/<announce_id>', methods=['PUT'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def update_announce(announce_id):
    announce_dict = json.loads(request.get_data(as_text=True))
    return announce_service.update_announce(announce_id, announce_dict)
