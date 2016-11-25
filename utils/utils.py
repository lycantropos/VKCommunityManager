import logging
from typing import List, Callable

from vk_app.utils import make_delayed
from vk_community.app import CommunityApp
from vk_community.models import Post

from settings import PROCESSED_POSTS_FILE_ABSPATH, POSTING_PERIOD_IN_SEC


def duplicate_posts(community_app: CommunityApp, posts: List[Post],
                    selector: Callable[[Post], bool] = lambda x: True,
                    sorter: Callable[[Post], str] = lambda x: x.vk_id,
                    editor: Callable[[str], str] = lambda x: x,
                    reload_path: str = None, **params) -> List[str]:
    filtered_posts = list(
        post
        for post in posts
        if selector(post)
    )
    filtered_posts.sort(key=sorter)
    return list(duplicate_post(community_app, editor, filtered_posts,
                               ind, post, reload_path, **params)
                for ind, post in enumerate(filtered_posts))


@make_delayed(POSTING_PERIOD_IN_SEC)
def duplicate_post(community_app, editor, filtered_posts,
                   ind, post, reload_path, **params) -> Post:
    with open(PROCESSED_POSTS_FILE_ABSPATH, mode='a') as processed_posts_file:
        try:
            logging.info(
                'Post {num} of {total}: {post}'.format(num=ind + 1, total=len(filtered_posts), post=post)
            )
            post_id = community_app.duplicate_post(post, reload_path=reload_path, editor=editor, comment=post.text,
                                                   **params)
            processed_posts_file.write(post.vk_id + '\n')
            return post_id
        except OSError:
            logging.exception(post)
