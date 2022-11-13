import json

from flask import Blueprint, request
from flask_login import login_required

from domain.User import User
from service.auth import auth_user
from service.downloader_manager import download_manager_service

download_manager_api = Blueprint('download_manager', __name__)


@download_manager_api.route('/proxy', methods=['POST'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def proxy():
    req_data = json.loads(request.get_data(True, as_text=True))
    return download_manager_service.proxy(req_data)


@download_manager_api.route('/file-mapping', methods=['POST'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def enhance_file_mapping():
    data = json.loads(request.get_data(True, as_text=True))
    return download_manager_service.enhance_file_mapping(data)


@download_manager_api.route('/bangumi', methods=['POST'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def get_bangumi_from_ids():
    data = json.loads(request.get_data(True, as_text=True))
    return download_manager_service.get_bangumi_from_ids(data['ids'])
