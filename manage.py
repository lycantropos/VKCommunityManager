import os

import PIL.Image
import click
from vk_app.services.loading import download
from vk_app.services.logging_config import LoggingConfig
from vk_app.utils import CallRepeater, CallDelayer
from vk_community.app import CommunityApp
from vk_community.models import Base
from vk_community.services.data_access import DataAccessObject

from settings import DATABASE_URL, BASE_DIR, LOGGING_CONFIG_PATH, LOGS_PATH
from settings import (DST_GROUP_ID, SRC_GROUP_ID, APP_ID, USER_LOGIN, USER_PASSWORD, SCOPE, FORBIDDEN_ALBUMS,
                      DST_ABSPATH, WATERMARK_PATH)

MINIMAL_INTERVAL_BETWEEN_DOWNLOAD_REQUESTS_IN_SECONDS = 0.35
download = CallDelayer.make_delayed(MINIMAL_INTERVAL_BETWEEN_DOWNLOAD_REQUESTS_IN_SECONDS)(download)

MINIMAL_INTERVAL_BETWEEN_DELETE_REQUESTS_IN_SECONDS = 1.7

CommunityApp.delete_wall_post = CallDelayer.make_delayed(MINIMAL_INTERVAL_BETWEEN_DELETE_REQUESTS_IN_SECONDS)(
    CommunityApp.delete_wall_post
)

MAX_POSTS_PER_DAY = 50
DAY_IN_SEC = 86400
CommunityApp.synchronize_and_mark = CallRepeater.make_periodic(DAY_IN_SEC)(CommunityApp.synchronize_and_mark)
POSTING_PERIOD_IN_SEC = DAY_IN_SEC / MAX_POSTS_PER_DAY
CommunityApp.post_random_photos_on_community_wall = CallRepeater.make_periodic(POSTING_PERIOD_IN_SEC)(
    CommunityApp.post_random_photos_on_community_wall
)


@click.group(name='run', invoke_without_command=False)
def run():
    logging_config = LoggingConfig(BASE_DIR, LOGGING_CONFIG_PATH, LOGS_PATH)
    logging_config.set()
    pass


@run.command(name='run_sync')
def sync():
    community_app = CommunityApp(APP_ID, DST_GROUP_ID, USER_LOGIN, USER_PASSWORD, SCOPE,
                                 dao=DataAccessObject(DATABASE_URL))
    images_path = os.path.join(DST_ABSPATH, community_app.community_info['screen_name'])
    watermark = PIL.Image.open(WATERMARK_PATH)
    community_app.synchronize_and_mark(images_path, watermark, owner_id=-SRC_GROUP_ID)


@run.command(name='run_post_bot')
def post_bot():
    community_app = CommunityApp(APP_ID, DST_GROUP_ID, USER_LOGIN, USER_PASSWORD, SCOPE,
                                 dao=DataAccessObject(DATABASE_URL))
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
