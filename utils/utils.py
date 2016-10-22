import logging
from typing import List, Callable

from vk_app.post import VKPost
from vk_community.app import CommunityApp

from settings import PROCESSED_POSTS_FILE_ABSPATH


def duplicate_posts(community_app: CommunityApp, posts: List[VKPost],
                    selector: Callable[[VKPost], bool] = lambda x: True,
                    sorter: Callable[[VKPost], str] = lambda x: x.vk_id, editor: Callable[[str], str] = lambda x: x,
                    reload_path: str = None, **params):
    filtered_posts = list(
        post
        for post in posts
        if selector(post)
    )
    filtered_posts.sort(key=sorter)
    with open(PROCESSED_POSTS_FILE_ABSPATH, mode='a+') as processed_posts_file:
        for ind, post in enumerate(filtered_posts):
            try:
                logging.info(
                    'Post {num} of {total}: {post}'.format(num=ind + 1, total=len(filtered_posts), post=post)
                )
                community_app.duplicate_post(post, reload_path=reload_path, editor=editor, **params)
                processed_posts_file.write(post.vk_id + '\n')
            except OSError:
                logging.exception(post)
