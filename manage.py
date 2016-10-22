import os

import PIL.Image
import click
from vk_app.services.loading import download
from vk_app.services.logging_config import LoggingConfig
from vk_app.utils import make_delayed, make_periodic
from vk_community.app import CommunityApp
from vk_community.models import Base
from vk_community.services.data_access import DataAccessObject

from settings import DATABASE_URL, BASE_DIR, LOGGING_CONFIG_PATH, LOGS_PATH, PROCESSED_POSTS_FILE_ABSPATH
from settings import (DAY_IN_SEC, MINIMAL_INTERVAL_BETWEEN_DOWNLOAD_REQUESTS_IN_SECONDS,
                      POSTING_PERIOD_IN_SEC)
from settings import (DST_GROUP_ID, SRC_GROUP_ID, APP_ID, USER_LOGIN, USER_PASSWORD, SCOPE, FORBIDDEN_ALBUMS,
                      DST_ABSPATH, WATERMARK_PATH)
from utils.utils import duplicate_posts

download = make_delayed(MINIMAL_INTERVAL_BETWEEN_DOWNLOAD_REQUESTS_IN_SECONDS)(download)


@click.group(name='run', invoke_without_command=False)
def run():
    logging_config = LoggingConfig(BASE_DIR, LOGGING_CONFIG_PATH, LOGS_PATH)
    logging_config.set()
    pass


@run.command(name='run_sync')
def sync():
    community_app = CommunityApp(APP_ID, DST_GROUP_ID, USER_LOGIN, USER_PASSWORD, SCOPE,
                                 dao=DataAccessObject(DATABASE_URL))
    community_app.synchronize_and_mark = make_periodic(DAY_IN_SEC)(community_app.synchronize_and_mark)
    images_path = os.path.join(DST_ABSPATH, community_app.community_info['screen_name'])
    watermark = PIL.Image.open(WATERMARK_PATH)
    community_app.synchronize_and_mark(images_path, watermark, owner_id=-SRC_GROUP_ID)


@run.command(name='run_duplicate')
def duplicate():
    community_app = CommunityApp(APP_ID, DST_GROUP_ID, USER_LOGIN, USER_PASSWORD, SCOPE)
    community_app.post_on_wall = make_delayed(POSTING_PERIOD_IN_SEC)(community_app.post_on_wall)

    params = dict()
    posts = community_app.load_posts(owner_id=-SRC_GROUP_ID, **params)
    with open(PROCESSED_POSTS_FILE_ABSPATH) as processed_posts_file:
        processed_posts = processed_posts_file.read().split('\n')
    duplicate_posts(
        community_app, posts=posts,
        selector=lambda post: True if '#sg_music' in post.text and
                                      post.vk_id not in processed_posts and
                                      post.attachments is not None and
                                      len(post.attachments) == 6 else False,
        sorter=lambda post: post.object_id,
        editor=lambda message: message.replace('#sg_music', ''),
        reload_path='/tmp/'
    )


@run.command(name='run_post_bot')
def post_bot():
    community_app = CommunityApp(APP_ID, DST_GROUP_ID, USER_LOGIN, USER_PASSWORD, SCOPE,
                                 dao=DataAccessObject(DATABASE_URL))
    community_app.post_random_photos_on_community_wall = make_periodic(POSTING_PERIOD_IN_SEC)(
        community_app.post_random_photos_on_community_wall
    )
    images_path = os.path.join(DST_ABSPATH, community_app.community_info['screen_name'])
    filters = dict(
        owner_id=-SRC_GROUP_ID,
        forbidden_albums=FORBIDDEN_ALBUMS,
        marked=1,
    )
    community_app.post_random_photos_on_community_wall(images_path, **filters)


@run.command(name='run_init_db')
def init_db():
    dao = DataAccessObject(DATABASE_URL)
    Base.metadata.create_all(dao.engine)


if __name__ == '__main__':
    run()
