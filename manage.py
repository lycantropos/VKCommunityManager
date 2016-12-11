import logging
import os
import random
import time

import PIL.Image
import click
import vk.exceptions
from selenium import webdriver
from vk_app.app import captchured
from vk_app.models import VKAudio
from vk_app.services import download
from vk_app.utils import make_delayed, make_periodic, set_logging_config
from vk_community.app import CommunityApp
from vk_community.models import Base, Audio
from vk_community.services.data_access import DataAccessObject

import utils
from settings import (DATABASE_URL, BASE_DIR, LOGGING_CONFIG_PATH, LOGS_PATH,
                      PROCESSED_POSTS_FILE_ABSPATH, TMP_ABSPATH, PHANTOMJS_PATH,
                      COMMUNITY_TAG, TARGET_POST_TAGS)
from settings import (DAY_IN_SEC, MINIMAL_INTERVAL_BETWEEN_DOWNLOAD_REQUESTS_IN_SECONDS,
                      POSTING_PERIOD_IN_SEC)
from settings import (DST_GROUP_ID, SRC_GROUP_ID, APP_ID, USER_LOGIN, USER_PASSWORD, SCOPE, FORBIDDEN_ALBUMS,
                      DST_ABSPATH, WATERMARK_PATH)

PAGE_LOAD_TIME_IN_SEC = 5
PAGE_WAIT_TIME_IN_SEC = 5
download = make_delayed(MINIMAL_INTERVAL_BETWEEN_DOWNLOAD_REQUESTS_IN_SECONDS)(download)
Audio.load_lyrics = make_delayed(2 * (PAGE_LOAD_TIME_IN_SEC + PAGE_WAIT_TIME_IN_SEC))(Audio.load_lyrics)


@click.group(name='run', invoke_without_command=False)
def run():
    pass


@run.command(name='sync')
@click.option('--mark', '-m', is_flag=True)
@click.option('--src', default='all', help='Source of community photos ("wall", "album", "all")')
def sync(mark, src):
    community_app = CommunityApp(APP_ID, DST_GROUP_ID, USER_LOGIN, USER_PASSWORD, SCOPE,
                                 dao=DataAccessObject(DATABASE_URL))

    images_path = os.path.join(DST_ABSPATH, community_app.community_info['screen_name'])
    params = dict(owner_id=-SRC_GROUP_ID)
    if mark:
        community_app.synchronize_and_mark = make_periodic(DAY_IN_SEC)(community_app.synchronize_and_mark)

        watermark = PIL.Image.open(WATERMARK_PATH)
        community_app.synchronize_and_mark(images_path, src, watermark, **params)
    else:
        community_app.synchronize = make_periodic(DAY_IN_SEC)(community_app.synchronize)

        community_app.synchronize(images_path, src, **params)


def post_selector(post):
    with open(PROCESSED_POSTS_FILE_ABSPATH) as processed_posts_file:
        processed_posts = processed_posts_file.read().split('\n')
    if post.vk_id not in processed_posts and \
            any(tag in post.text for tag in TARGET_POST_TAGS) and \
                    post.attachments is not None and \
                    len(post.attachments) == 6:
        return True
    else:
        return False


def post_editor(message):
    return message.replace(COMMUNITY_TAG, '')


@run.command(name='duplicate')
def duplicate():
    community_app = CommunityApp(APP_ID, DST_GROUP_ID, USER_LOGIN, USER_PASSWORD, SCOPE)

    if os.path.exists(PHANTOMJS_PATH):
        web_driver = webdriver.PhantomJS(PHANTOMJS_PATH)
        web_driver.set_page_load_timeout(PAGE_LOAD_TIME_IN_SEC)
        web_driver.implicitly_wait(PAGE_WAIT_TIME_IN_SEC)
    else:
        web_driver = None
        logging.warning('No PhantomJS specified. No lyrics will be attached to audio.')

    params = dict(owner_id=-SRC_GROUP_ID)
    posts = community_app.load_posts(**params)

    try:
        duplicated_posts_ids = utils.duplicate_posts(community_app, posts=posts,
                                                     selector=post_selector,
                                                     sorter=lambda post: post.object_id,
                                                     editor=post_editor,
                                                     reload_path=TMP_ABSPATH,
                                                     web_driver=web_driver,
                                                     website='https://vk.com/e1337fm')
        logging.debug('Duplication ended. Number of posts generated: {}.'.format(len(duplicated_posts_ids)))
    finally:
        if web_driver:
            web_driver.quit()


@run.command(name='post_bot')
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


@run.command(name='set_lyrics')
@click.option('--randomize', '-r', is_flag=True, help='Shuffles audios.')
def set_lyrics(randomize):
    if not os.path.exists(PHANTOMJS_PATH):
        logging.warning('No PhantomJS specified.')

    web_driver = webdriver.PhantomJS(PHANTOMJS_PATH)
    web_driver.set_page_load_timeout(PAGE_LOAD_TIME_IN_SEC)
    web_driver.implicitly_wait(PAGE_WAIT_TIME_IN_SEC)

    community_app = CommunityApp(APP_ID, DST_GROUP_ID, USER_LOGIN, USER_PASSWORD, SCOPE)

    raw_audios = community_app.get_all_objects('audio.get')
    audios = list(Audio.from_raw(raw_audio) for raw_audio in raw_audios)
    if randomize:
        random.shuffle(audios)

    try:
        for audio in audios:
            if audio.lyrics_id:
                continue
            lyrics = audio.load_lyrics(web_driver=web_driver)
            if lyrics:
                logging.info('Found lyrics for {}'.format(audio.get_file_name()))
            else:
                logging.warning('No lyrics found for {}'.format(audio.get_file_name()))
            try:
                community_app.api_session.audio.edit(owner_id=audio.owner_id,
                                                     audio_id=audio.object_id,
                                                     text=lyrics)
            except vk.exceptions.VkAPIError:
                logging.exception('')
                continue
    finally:
        web_driver.quit()


@run.command(name='init_db')
def init_db():
    dao = DataAccessObject(DATABASE_URL)
    Base.metadata.create_all(dao.engine)


@run.command(name='sync_audios')
@captchured()
def sync_audios(**params):
    community_app = CommunityApp(APP_ID, DST_GROUP_ID, USER_LOGIN, USER_PASSWORD, SCOPE)

    dst_audios = list(VKAudio.from_raw(raw_audio)
                      for raw_audio in community_app.get_all_objects('audio.get',
                                                                     owner_id=-DST_GROUP_ID, **params))

    src_albums = community_app.get_all_objects('audio.getAlbums', owner_id=-SRC_GROUP_ID, **params)
    dst_albums = community_app.get_all_objects('audio.getAlbums', owner_id=-DST_GROUP_ID, **params)
    dst_albums_ids_by_src = dict()
    for src_album in src_albums:
        try:
            album_id = next(album['id'] for album in dst_albums if album['title'] == src_album['title'])
        except StopIteration:
            album_id = community_app.api_session.audio.addAlbum(group_id=DST_GROUP_ID,
                                                                title=src_album['title'], **params)['album_id']
            time.sleep(5)
        dst_albums_ids_by_src[src_album['id']] = album_id

    audios = list(dict(audio_id=raw_audio['id'], owner_id=raw_audio['owner_id'],
                       album_id=dst_albums_ids_by_src[album['id']])
                  for album in src_albums
                  for raw_audio in community_app.get_all_objects('audio.get',
                                                                 owner_id=-SRC_GROUP_ID,
                                                                 album_id=album['id'],
                                                                 **params)
                  if not any(raw_audio['artist'] == audio.artist and
                             raw_audio['title'] == audio.title
                             for audio in dst_audios))

    for audio in audios:
        community_app.api_session.audio.add(group_id=DST_GROUP_ID, **audio, **params)
        time.sleep(0.5)


if __name__ == '__main__':
    set_logging_config(BASE_DIR, LOGGING_CONFIG_PATH, LOGS_PATH)
    run()
