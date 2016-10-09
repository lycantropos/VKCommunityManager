from settings import APP_ID, DST_GROUP_ID, USER_LOGIN, USER_PASSWORD, SCOPE
from vk_community.app import CommunityApp

from vk_app.utils import CallDelayer

if __name__ == '__main__':
    community_app = CommunityApp(APP_ID, DST_GROUP_ID, USER_LOGIN, USER_PASSWORD, SCOPE)
    params = dict()
    community_app.synchronize_wall_posts(**params)
