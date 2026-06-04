# -*- coding: utf-8 -*-
from flask import request, Blueprint

from utils.exceptions import ClientError
from utils.http import json_resp
import json
from service.user import UserCredential
from flask_login import login_user, logout_user, login_required, fresh_login_required, current_user

user_api = Blueprint('user', __name__)


@user_api.route('/login', methods=['POST'])
def login():
    """
    login a user
    :return: response
    """
    content = request.get_data(True, as_text=True)
    login_data = json.loads(content)
    if ('name' in login_data) and ('password' in login_data):
        name = login_data['name']
        password = login_data['password']
        remember = login_data['remember'] if 'remember' in login_data else False
        credential = UserCredential.login_user(name, password)
        login_user(credential, remember=remember)
        return json_resp({'msg': 'OK'})
    else:
        raise ClientError(ClientError.INVALID_REQUEST)


@user_api.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    logout a user
    :return: response
    """
    logout_user()
    return json_resp({'msg': 'ok'})


@user_api.route('/register', methods=['POST'])
def register():
    """
    register a new user using invite code, note that a newly registered user is not administrator, you need to
    use an admin user to promote it
    :return: response
    """
    content = request.get_data(True, as_text=True)
    register_data = json.loads(content)
    if ('name' in register_data) and ('password' in register_data) and ('password_repeat' in register_data) and ('invite_code' in register_data) and ('email' in register_data):
        name = register_data['name']
        password = register_data['password']
        password_repeat = register_data['password_repeat']
        email = register_data['email']
        invite_code = register_data['invite_code']
        if password != password_repeat:
            raise ClientError(ClientError.PASSWORD_MISMATCH)
        if UserCredential.register_user(name=name, password=password, email=email, invite_code=invite_code):
            # login automatically
            credential = UserCredential.login_user(name, password)
            login_user(credential, remember=False)
            # send email
            credential.send_confirm_email()
            return json_resp({'message': 'ok'}, 201)
    else:
        raise ClientError(ClientError.INVALID_REQUEST)


@user_api.route('/update-pass', methods=['POST'])
@login_required
def update_pass():
    """
    update a user password, the original password is needed
    :return: response
    """
    content = request.get_data(True, as_text=True)
    user_data = json.loads(content)
    if ('new_password' in user_data) and ('new_password_repeat' in user_data) and ('password' in user_data):
        if user_data['new_password'] != user_data['new_password_repeat']:
            raise ClientError('password not match')
        current_user.update_password(user_data['password'], user_data['new_password'])

        return logout()
    else:
        raise ClientError(ClientError.INVALID_REQUEST)


@user_api.route('/reset-pass', methods=['POST'])
def reset_pass():
    """
    reset password using token
    """
    data = json.loads(request.get_data(True, as_text=True))
    if ('new_pass' in data) and ('new_pass_repeat' in data) and ('token' in data):
        new_pass = data['new_pass']
        new_pass_repeat = data['new_pass_repeat']
        if new_pass != new_pass_repeat:
            raise ClientError(ClientError.PASSWORD_MISMATCH)
        return UserCredential.update_password_with_token(new_pass, token=data['token'])
    else:
        raise ClientError(ClientError.INVALID_REQUEST)


@user_api.route('/request-reset-pass', methods=['POST'])
def request_reset_pass():
    data = json.loads(request.get_data(True, as_text=True))
    if 'email' in data:
        UserCredential.send_pass_reset_email(data['email'])
        return json_resp({'message': 'ok'})
    else:
        raise ClientError(ClientError.INVALID_REQUEST)


@user_api.route('/info', methods=['GET'])
@login_required
def get_user_info():
    """
    get current user name and level
    :return: response
    """
    user_info = {
        'name': current_user.name,
        'level': current_user.level,
        # 'email': current_user.email,
        'email_confirmed': current_user.email_confirmed
    }
    return json_resp({'data': user_info})


@user_api.route('/email/confirm', methods=['POST'])
@login_required
def get_confirm_email():
    data = json.loads(request.get_data(as_text=True))
    token = data.get('token')
    if token is None:
        raise ClientError('Invalid Token')
    return current_user.confirm_token(token)


@user_api.route('/email', methods=['POST'])
@login_required
def update_email():
    data = json.loads(request.get_data(as_text=True))
    email = data.get('email')
    # password = data.get('password')
    if email is None:
        raise ClientError(ClientError.INVALID_EMAIL)
    # if password is None:
    #     raise ClientError('Invalid password')
    return current_user.update_email(email)


@user_api.route('/email/resend', methods=['POST'])
@login_required
def send_confirm_mail():
    if current_user.email is None:
        raise ClientError(ClientError.INVALID_EMAIL)
    current_user.send_confirm_email()
    return json_resp({"message": "ok"})


@user_api.route('/migration-token', methods=['POST'])
@login_required
def generate_migration_token():
    if current_user.email is None:
        raise ClientError(ClientError.INVALID_EMAIL)
    return current_user.generate_migration_token()
