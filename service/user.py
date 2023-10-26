from flask_login import UserMixin
from sqlalchemy.exc import IntegrityError, DataError
from sqlalchemy.orm.exc import NoResultFound

from domain.InviteCode import InviteCode
from utils.SessionManager import SessionManager
from domain.User import User
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer

from utils.exceptions import ClientError, ServerError
from utils.http import json_resp, rpc_request
from flask_mail import Message
from flask import render_template
from smtplib import SMTPAuthenticationError

import logging
import re

logger = logging.getLogger(__name__)

PASSWORD_DIGEST_LENGTH = 8


class UserCredential(UserMixin):

    def __init__(self, user):
        self.id = user.id
        self.name = user.name
        self.password = user.password
        self.level = user.level
        self.email = user.email
        self.email_confirmed = user.email_confirmed
        self.register_time = user.register_time
        self.update_time = user.update_time

    @staticmethod
    def get_pass_hash(password):
        return generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

    def update_password(self, old_pass, new_pass):
        from server import app, mail
        session = SessionManager.Session()
        try:
            user = session.query(User).filter(User.id == self.id).one()
            if check_password_hash(user.password, old_pass):
                user.password = UserCredential.get_pass_hash(new_pass)
                session.commit()
                if user.email is not None and user.email_confirmed:
                    # send notification mail
                    subject = u'[{0}] Password Update Notification'.format(app.config['SITE_NAME'])
                    email_content = render_template('update-pass-notification.html', info={
                        'title': subject,
                        'user_name': user.name,
                        'site_name': app.config['SITE_NAME']
                    })
                    msg = Message(subject, recipients=[self.email], html=email_content)
                    try:
                        mail.send(msg)
                    except SMTPAuthenticationError:
                        raise ServerError('SMTP authentication failed', 500)
                return True
            else:
                raise ClientError(ClientError.PASSWORD_INCORRECT)
        except NoResultFound:
            raise ServerError('user not found')
        finally:
            SessionManager.Session.remove()

    def update_email(self, new_email):
        from server import app, mail
        session = SessionManager.Session()
        try:
            user = session.query(User).filter(User.id == self.id).one()
            if user.email is not None and user.email_confirmed:
                # send notification mail
                subject = u'[{0}] Email Address Update Notification'.format(app.config['SITE_NAME'])
                email_content = render_template('email-change-notification.html', info={
                    'title': subject,
                    'user_name': user.name,
                    'site_name': app.config['SITE_NAME']
                })
                msg = Message(subject, recipients=[self.email], html=email_content)
                try:
                    mail.send(msg)
                except SMTPAuthenticationError:
                    raise ServerError('SMTP authentication failed', 500)
            # update
            user.email = new_email
            user.email_confirmed = False
            self.email = new_email
            self.email_confirmed = False
            # send email
            self.send_confirm_email()
            session.commit()
            return json_resp({'message': 'ok'})
        except IntegrityError:
            raise ClientError('duplicate email')
        except NoResultFound:
            raise ServerError('user not found')
        finally:
            SessionManager.Session.remove()

    def generate_confirm_email_token(self):
        """
        # https://realpython.com/blog/python/handling-email-confirmation-in-flask/
        :return: a serialized token contains email and token timestamp
        """
        from server import app
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        return serializer.dumps(self.email, salt=app.config['SECRET_PASSWORD_SALT'])

    def confirm_token(self, token, expiration=3600):
        from server import app
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        session = SessionManager.Session()
        try:
            email = serializer.loads(
                token,
                salt=app.config['SECRET_PASSWORD_SALT'],
                max_age=expiration
            )
            if (email == self.email) and (not self.email_confirmed):
                self.email_confirmed = True
                user = session.query(User).filter(User.id == self.id).one()
                user.email_confirmed = True
                session.commit()
                rpc_request.send('email_changed', {'email': self.email, 'user_id': user.id})
                return json_resp({'message': 'ok'})
            else:
                raise ClientError('Invalid Token')
        except:
            raise ClientError('Invalid Token')
        finally:
            SessionManager.Session.remove()

    def send_confirm_email(self):
        """
        Send an confirm email to user. contains a link to confirm the email
        confirm link is not provide by this app, a client must implement this endpoint to complete the confirmation.
        """
        from server import app, mail
        token = self.generate_confirm_email_token()
        confirm_url = '{0}://{1}/email-confirm?token={2}'.format(app.config['SITE_PROTOCOL'],
                                                                 app.config['SITE_HOST'],
                                                                 token)
        subject = u'[{0}] Email Address Confirmation'.format(app.config['SITE_NAME'])
        email_content = render_template('email-confirm.html', info={
            'confirm_title': subject,
            'confirm_url': confirm_url,
            'site_name': app.config['SITE_NAME'],
            'user_name': self.name
        })
        msg = Message(subject, recipients=[self.email], html=email_content)
        try:
            mail.send(msg)
        except SMTPAuthenticationError:
            raise ServerError('SMTP authentication failed', 500)

    @staticmethod
    def get_password_digest(password):
        """
        Get last 8 hash string from password
        :return: digest of password
        """
        return password[-PASSWORD_DIGEST_LENGTH:]

    @staticmethod
    def generate_reset_email_token(user):
        """
        Generate a one-time token used for resetting password, this token contains a digest of current password and
        email of a valid user.
        :return: a serialized token contains email, a password digest and a token timestamp
        """
        from server import app
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        combine_str = '{0}&{1}'.format(user.email, UserCredential.get_password_digest(user.password))
        return serializer.dumps(combine_str, salt=app.config['SECRET_PASSWORD_SALT'])

    @staticmethod
    def send_pass_reset_email(email):
        """
        Send a password reset email which includes a link to navigate user to a endpoint to reset his/her password.
        The link contains a token get from self.generate_reset_email_token method. end point has the responsibility
        to verify the token.
        :param email: the user email from user input. this must be a confirmed email of a valid user.
        :return:
        """
        from server import app, mail
        session = SessionManager.Session()
        try:
            user = session.query(User). \
                filter(User.email == email). \
                one()
            if not user.email_confirmed:
                raise ClientError(ClientError.EMAIL_NOT_CONFIRMED)

            # generate token
            token = UserCredential.generate_reset_email_token(user)

            reset_url = '{0}://{1}/reset-pass?token={2}'.format(app.config['SITE_PROTOCOL'],
                                                                app.config['SITE_HOST'],
                                                                token)
            subject = u'[{0}] Password Request for {1}'.format(app.config['SITE_NAME'], user.name)
            reset_content = render_template('reset-pass.html', info={
                'reset_title': subject,
                'reset_url': reset_url,
                'site_name': app.config['SITE_NAME'],
                'user_name': user.name
            })
            msg = Message(subject, recipients=[email], html=reset_content)
            mail.send(msg)
            session.commit()
        except SMTPAuthenticationError:
            raise ServerError('SMTP authentication failed', 500)
        except NoResultFound:
            raise ClientError(ClientError.EMAIL_NOT_EXISTS, 400)
        finally:
            SessionManager.Session.remove()

    @staticmethod
    def update_password_with_token(new_pass, token, expiration=3600):
        from server import app
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        session = SessionManager.Session()
        try:
            combine_str = serializer.loads(token,
                                           salt=app.config['SECRET_PASSWORD_SALT'],
                                           max_age=expiration)
            email = combine_str[:-(PASSWORD_DIGEST_LENGTH + 1)]
            old_pass_digest = combine_str[-PASSWORD_DIGEST_LENGTH:]
            user = session.query(User).filter(User.email == email).one()
            if not user.email_confirmed:
                raise ClientError(ClientError.EMAIL_NOT_CONFIRMED)

            if old_pass_digest != UserCredential.get_password_digest(user.password):
                raise ClientError('invalid token')

            user.password = UserCredential.get_pass_hash(new_pass)

            session.commit()

            return json_resp({'message': 'ok'})

        except NoResultFound:
            raise ClientError(ClientError.EMAIL_NOT_EXISTS, 400)
        finally:
            SessionManager.Session.remove()

    @classmethod
    def get(cls, user_id):
        session = SessionManager.Session()
        try:
            user = session.query(User).filter(User.id == user_id).one()
            credential = cls(user)
            return credential
        except Exception as error:
            logger.warn(error)
            return None
        finally:
            SessionManager.Session.remove()

    @classmethod
    def login_user(cls, name, password):
        session = SessionManager.Session()
        try:
            user = session.query(User).filter(User.name == name).one()
            if check_password_hash(user.password.encode('utf-8'), password.encode('utf-8')):
                credential = cls(user)
                SessionManager.Session.remove()
                return credential
            else:
                raise ClientError(ClientError.LOGIN_FAIL)
        except NoResultFound:
            raise ClientError(ClientError.LOGIN_FAIL)
        except DataError:
            raise ClientError(ClientError.LOGIN_FAIL)
        except ClientError as error:
            raise error
        except Exception as error:
            raise ServerError(error.message)
        finally:
            SessionManager.Session.remove()

    @staticmethod
    def register_user(name, password, email, invite_code):
        email_patteren = re.compile("(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
        if not email_patteren.match(email):
            raise ClientError(ClientError.INVALID_EMAIL)
        session = SessionManager.Session()
        try:
            code = session.query(InviteCode).filter(InviteCode.code == invite_code).one()
            if code.used_by is not None:
                raise ClientError(ClientError.INVALID_INVITE_CODE)
            user = User(name=name,
                        password=UserCredential.get_pass_hash(password),
                        email=email,
                        level=0)
            session.add(user)
            session.commit()
            code.used_by = user.id
            session.commit()
            return True
        except NoResultFound:
            raise ClientError(ClientError.INVALID_INVITE_CODE)
        except DataError:
            raise ClientError(ClientError.INVALID_INVITE_CODE)
        except IntegrityError as error:
            if error.diag.column_name == 'name':
                raise ClientError(ClientError.DUPLICATE_NAME)
            elif error.diag.column_name == 'email':
                raise ClientError(ClientError.DUPLICATE_EMAIL)
        except ClientError as error:
            raise error
        except Exception as error:
            raise ServerError(error.message)
        finally:
            SessionManager.Session.remove()
