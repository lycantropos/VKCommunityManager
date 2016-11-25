import configparser
import os

from sqlalchemy.engine import url

CONFIGURATION_FILE_NAME = 'configuration.conf'
CURRENT_FILE_PATH = os.path.realpath(__file__)
CURRENT_FILE_ABSPATH = os.path.abspath(CURRENT_FILE_PATH)
BASE_DIR = os.path.dirname(CURRENT_FILE_ABSPATH)
CONFIGURATION_FILE_FOLDER = 'configurations'
CONFIGURATION_FILE_PATH = os.path.join(BASE_DIR, CONFIGURATION_FILE_FOLDER, CONFIGURATION_FILE_NAME)
config = configparser.ConfigParser()
config.read(CONFIGURATION_FILE_PATH)

user = config['user']
USER_LOGIN = user.get('user_login')
USER_PASSWORD = user.get('user_password')
ACCESS_TOKEN = user.get('access_token')

app = config['app']
APP_ID = int(app.get('app_id'))
SCOPE = app.get('scope')
SRC_GROUP_ID = int(app.get('src_group_id'))
DST_GROUP_ID = int(app.get('dst_group_id'))
FORBIDDEN_ALBUMS = app.get('forbidden_albums').split(',')
COMMUNITY_TAG = app.get('community_tag')
TARGET_POST_TAGS = app.get('target_post_tags').split(',')

files = config['files']
DST_ABSPATH = files.get('dst_abspath')
TMP_ABSPATH = files.get('tmp_abspath')
PHANTOMJS_PATH = files.get('phantomjs_path')

database = config['database']
DATABASE_URL = url.make_url(database['database_url'])

logger = config['logger']
LOGS_DIR = logger.get('logs_dir')
LOGS_FILE_NAME = logger.get('logs_file_name')
LOGS_PATH = os.path.join(LOGS_DIR, LOGS_FILE_NAME)
LOGGING_CONFIG_PATH = logger.get('logging_config_path')

WATERMARK_DIR_PATH = os.path.join(BASE_DIR, 'utils')
WATERMARK_FILE_NAME = 'watermark.png'
WATERMARK_PATH = os.path.join(WATERMARK_DIR_PATH, WATERMARK_FILE_NAME)

MINIMAL_INTERVAL_BETWEEN_POST_EDITING_REQUESTS_IN_SECONDS = 25

MAX_POSTS_PER_DAY = 50
DAY_IN_SEC = 86400
POSTING_PERIOD_IN_SEC = DAY_IN_SEC / MAX_POSTS_PER_DAY
MINIMAL_INTERVAL_BETWEEN_DOWNLOAD_REQUESTS_IN_SECONDS = 0.35
MINIMAL_INTERVAL_BETWEEN_DELETE_REQUESTS_IN_SECONDS = 1.7

PROCESSED_POSTS_FILE_NAME = 'processed.log'
PROCESSED_POSTS_FILE_ABSPATH = os.path.join(BASE_DIR, LOGS_DIR, PROCESSED_POSTS_FILE_NAME)
