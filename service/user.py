from flask_login import UserMixin
from sqlalchemy.exc import IntegrityError, DataError
from sqlalchemy.orm.exc import NoResultFound

from domain.InviteCode import InviteCode
from utils.SessionManager import SessionManager
from domain.User import User
from werkzeug.security import generate_password_hash, check_password_hash

from utils.exceptions import ClientError, ServerError


class UserCredential(UserMixin):

    def __init__(self, user):
        self.id = user.id
        self.name = user.name
        self.password = user.password
        self.level = user.level

    @classmethod
    def get(cls, id):
        session = SessionManager.Session()
        try:
            user = session.query(User).filter(User.id == id).one()
            credential =  cls(user)
            SessionManager.Session.remove()
            return credential
        except Exception as error:
            return None

    @classmethod
    def login_user(cls,name, password):
        session = SessionManager.Session()
        try:
            user = session.query(User).filter(User.name == name).one()
            if check_password_hash(user.password, password):
                credential = cls(user)
                SessionManager.Session.remove()
                return credential
            else:
                ClientError('invalid name or password')
        except NoResultFound:
            raise ClientError('invalid name or password')
        except DataError:
            raise ClientError('invalid name or password')
        except ClientError as error:
            raise error
        except Exception as error:
            raise ServerError(error.message)
        finally:
            SessionManager.Session.remove()

    @staticmethod
    def register_user(name, password, invite_code):
        session = SessionManager.Session()
        try:
            invite_code = session.query(InviteCode).filter(InviteCode.code == invite_code).one()
            if invite_code.used_by is not None:
                raise ClientError('invite code already used')
            user = User(name=name,
                        password=generate_password_hash(password),
                        level=0)
            session.add(user)
            session.commit()
            invite_code.used_by = user.id
            session.commit()
            return True
        except NoResultFound:
            raise ClientError('invalid invite code')
        except DataError:
            raise ClientError('invalid invite code')
        except IntegrityError:
            raise ClientError('duplicate name')
        except ClientError as error:
            raise error
        except Exception as error:
            raise ServerError(error.message)
        finally:
            SessionManager.Session.remove()