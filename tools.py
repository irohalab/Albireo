import argparse

from sqlalchemy.orm import joinedload

from utils.SessionManager import SessionManager
from werkzeug.security import generate_password_hash

# Unused domain is also necessary for initializing table
from domain.Bangumi import Bangumi
from domain.Episode import Episode
from domain.InviteCode import InviteCode
from domain.TorrentFile import TorrentFile
from domain.User import User
from domain.base import Base
from domain.Feed import Feed
from domain.Favorites import Favorites
from domain.ServerSession import ServerSession
from domain.WatchProgress import WatchProgress
from domain.Task import Task
from domain.VideoFile import VideoFile
from domain.Image import Image
from domain.Announce import Announce
from domain.WebHook import WebHook
from domain.WebHookToken import WebHookToken

from utils.http import FileDownloader
from utils.image import get_dominant_color, get_dimension
import yaml, os, errno, re
from urlparse import urlparse
from alembic import command
from alembic.config import Config
from StringIO import StringIO

parser = argparse.ArgumentParser(description='Tools for management database')
group = parser.add_mutually_exclusive_group()
group.add_argument('--invite', type=int, metavar=('NUMBER'), help='generate n invite codes')
group.add_argument('--user-add', nargs=2, metavar=('USERNAME', 'PASSWORD'), help='add an user')
group.add_argument('--user-del', nargs=1, metavar=('USERNAME'), help='delete an user')
group.add_argument('--user-promote', nargs=2, metavar=('USERNAME', 'LEVEL'), help='promote an user')
group.add_argument('--db-init', action='store_true', help='init database, if tables not exists, create it')
group.add_argument('--cover', action='store_true',
                   help='scan bangumi, download missing cover or generate missing color palette')
group.add_argument('--bgm-reset', nargs=1, metavar=('BANGUMI_ID'), help='clear a bangumi\'s related table records')
group.add_argument('--clean-video', action='store_true', help='clean all unlinked video, use with caution')

args = parser.parse_args()

if args.invite is not None:
    session = SessionManager.Session()
    invite_code_list = []
    for i in range(args.invite):
        invite_code = InviteCode()
        invite_code_list.append(invite_code)
        session.add(invite_code)

    session.commit()

    for invite_code in invite_code_list:
        print(invite_code.code)

    SessionManager.Session.remove()

elif args.user_add is not None:
    session = SessionManager.Session()
    username = args.user_add[0]
    password = args.user_add[1]
    user = User(name=username, password=generate_password_hash(password), level=User.LEVEL_DEFAULT)
    session.add(user)
    session.commit()
    print('Successfully create user, id is %s' % user.id)
    SessionManager.Session.remove()

elif args.user_del is not None:
    session = SessionManager.Session()
    username = args.user_del[0]
    session.query(User).filter(User.name==username).delete()
    session.commit()
    print('Delete successfully')
    SessionManager.Session.remove()

elif args.user_promote is not None:
    session = SessionManager.Session()
    username = args.user_promote[0]
    level = int(args.user_promote[1])
    user = session.query(User).filter(User.name==username).one()
    user.level = level
    session.commit()
    print('Update successfully')
    SessionManager.Session.remove()

elif args.db_init:
    Base.metadata.create_all(SessionManager.engine)
    fp = StringIO()
    alembic_config = Config('./alembic.ini', stdout=fp)
    command.heads(alembic_config)
    content = fp.getvalue()
    fp.close()
    revision_hash = re.search('^([0-9a-f]+)\s\(head\)', content, re.U).group(1)
    print('set current revision {0}'.format(revision_hash))
    new_alembic_config = Config('./alembic.ini')
    command.stamp(new_alembic_config, revision=revision_hash)
    print('Database initialized')

elif args.cover:
    fr = open('./config/config.yml', 'r')
    config = yaml.load(fr)
    download_location = config['download']['location']
    session = SessionManager.Session()
    cur = session.query(Bangumi)
    resp_cookies = None
    file_downloader = FileDownloader()
    for bangumi in cur:
        if bangumi.image is not None:
            try:
                bangumi_dir = download_location + '/' + str(bangumi.id)
                # if bangumi folder is not existence create it
                if not os.path.exists(bangumi_dir):
                    os.makedirs(bangumi_dir)
                    print 'bangumi %s folder created' % (str(bangumi.id),)

                path = urlparse(bangumi.image).path
                extname = os.path.splitext(path)[1]
                bangumi_cover_path = bangumi_dir + '/cover' + extname
                if not os.path.exists(bangumi_cover_path):
                    # download bangumi image
                    print 'start to download bangumi cover of %s (%s)' % (bangumi.name, str(bangumi.id))
                    file_downloader.download_file(bangumi.image, bangumi_cover_path)
                if bangumi.cover_color is None:
                    try:
                        bangumi.cover_color = get_dominant_color(bangumi_cover_path, 5)
                        session.commit()
                    except Exception as err:
                        print err
                if bangumi.cover_image_id is None:
                    try:
                        width, height = get_dimension(bangumi_cover_path)
                        cover_image = Image(file_path='{0}/cover{1}'.format(str(bangumi.id), extname),
                                            dominant_color=bangumi.cover_color,
                                            width=width,
                                            height=height)
                        bangumi.cover_image = cover_image
                        session.commit()
                    except Exception as err:
                        print err
            except OSError as exception:
                if exception.errno == errno.EACCES:
                    # permission denied
                    raise exception
                else:
                    print exception

        # check episode thumbnail color
        eps_cur = session.query(Episode).filter(Episode.bangumi_id == bangumi.id)
        for episode in eps_cur:
            if episode.status == Episode.STATUS_DOWNLOADED and episode.thumbnail_color is None:
                thumbnail_path = '{0}/{1}/thumbnails/{2}.png'.format(download_location, str(bangumi.id), str(episode.episode_no))
                try:
                    episode.thumbnail_color = get_dominant_color(thumbnail_path, 5)
                    session.commit()
                except Exception as err:
                    print err
            if episode.status == Episode.STATUS_DOWNLOADED and episode.thumbnail_image_id is None:
                thumbnail_path = '{0}/thumbnails/{1}.png'.format(str(bangumi.id), str(episode.episode_no))
                thumbnail_file_path = '{0}/{1}'.format(download_location, thumbnail_path)
                width, height = get_dimension(thumbnail_file_path)
                thumbnail_image = Image(file_path=thumbnail_path,
                                        dominant_color=episode.thumbnail_color,
                                        width=width,
                                        height=height)
                episode.thumbnail_image = thumbnail_image
                session.commit()
        print 'finish check bangumi #{0}'.format(str(bangumi.id))

elif args.bgm_reset:
    session = SessionManager.Session()
    bangumi_id = args.bgm_reset[0]
    episode_list = session.query(Episode).filter(Episode.bangumi_id == bangumi_id).all()
    video_file_list = session.query(VideoFile).filter(VideoFile.bangumi_id == bangumi_id).all()
    for video_file in video_file_list:
        session.delete(video_file)

    for episode in episode_list:
        episode.status = Episode.STATUS_NOT_DOWNLOADED
    session.commit()
    print('cleared')
    SessionManager.Session.remove()

elif args.clean_video:
    print('Query all bangumi and video_file')
    session = SessionManager.Session()
    video_file_list = session.query(VideoFile).options(joinedload(Bangumi)).all()

else:
    parser.print_help()
