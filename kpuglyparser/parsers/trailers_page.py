import re
import json
from typing import List

import requests
from bs4 import BeautifulSoup, SoupStrainer

from ..utils.get_page import LinkGP, get_page, get_pages, get_pages_g
from ..utils.decorators import compose, to_filter, to_map

TRAILER_PAGE_STRAINER = SoupStrainer("td", class_='news')
MAIN_TRAILERS_PAGE_STRAINER = SoupStrainer("div", class_='block_left')
CACHEDIR = ""
CACHETIME = 60 * 60 * 60


def __get_list_page(movie_id) -> BeautifulSoup:
    """ return table of trailers from page"""
    link = "https://www.kinopoisk.ru/film/{}/video/".format(movie_id)
    gplink = get_page(LinkGP(link), cachedir=CACHEDIR, cachetime=CACHETIME)
    return BeautifulSoup(gplink.content, 'lxml', parse_only=MAIN_TRAILERS_PAGE_STRAINER)


def __get_gp_links_from_list_page(list_page: BeautifulSoup) -> List[LinkGP]:
    links = list_page.find_all('a', attrs={
        "href": re.compile(r"/film/.+/video/(\d+)/$"),
        "style": None
    })
    return [LinkGP("https://www.kinopoisk.ru{}".format(i.attrs['href'])) for i in links if i.attrs['href']]


def __get_blocks_from_links(links: List[LinkGP]) -> List[BeautifulSoup]:
    return get_pages_g(links, cachedir=CACHEDIR, cachetime=CACHETIME)


def __linksgp_to_pages(link: LinkGP):
    b = BeautifulSoup(link.content, 'lxml', parse_only=TRAILER_PAGE_STRAINER)
    b.data = {
        'original_link': link.url
    }

    return b
    # return BeautifulSoup(link.content, 'lxml', parse_only=TRAILER_PAGE_STRAINER)


# def __add_data_attr(block: BeautifulSoup) -> BeautifulSoup:
#     block.data = {}
#     return block


def __get_title(block: BeautifulSoup) -> BeautifulSoup:
    try:
        title_tag = block.find_all(
            'td', attrs={"style": "color: #333; font-size: 27px; padding-left: 30px"})[0]
        title = title_tag.text
        block.data['title'] = title
    except:
        block.data['title'] = "Error"
    return block


# def __get_links_from_blocks(blocks: List[BeautifulSoup]):
#     links_reg = re.compile(
#         "https?:\/\/(www\.kinopoisk\.ru|)\/getlink\.php\?type=trailer&trailer_id=(\d+?)&quality=(.+?)$")

#     def parse_link(link):
#         match = links_reg.search(link.attrs['href'])
#         return {
#             'quality':  match.group(3),
#             'url':  match.group(0),
#         }

#     def get_links(block):
#         links = block.find_all('a', attrs={'href': links_reg})
#         block.data['links'] = list(map(parse_link, links))
#         return block
#     return map(get_links, blocks)

def __get_video_iframe(block: BeautifulSoup):
    player_div = block.find("iframe", attrs={
        'id': 'movie-trailer'
    })
    src = player_div.attrs.get("src")
    gplink = get_page(LinkGP(src), cachedir=CACHEDIR, cachetime=CACHETIME)
    return BeautifulSoup(gplink.content, 'lxml'), block


def __get_links_from_frame_block(frame_block__block):
    frame_block, block = frame_block__block
    # player_div = frame_block__block.find("div", attrs={
    #     'id': 'player'
    # })
    # player_div_json = player_div.attrs['data-params']
    # player_data = json.loads(player_div_json)
    try:
        # video_url = player_data.get('html5').get('mp4').get('videoUrl')
        block.data['links'] = [{
            'quality': 720,
            'url': ''
        }]
    except BaseException as error:
        block.data['links'] = []
        pass
    return block


def __get_posters(block: BeautifulSoup) -> BeautifulSoup:
    link = block.find("meta", attrs={'itemprop': "thumbnail"})
    if link:
        block.data['poster'] = link.attrs.get("content")
    if not link:
        link = block.find("link", attrs={'itemprop': "thumbnailUrl"})
        if link:
            block.data['poster'] = link.attrs.get("href")
    if not link:
        link = block.find("link", attrs={'rel': "videothumbnail"})
        if link:
            block.data['poster'] = link.attrs.get("href")
    return block


def __separate_data(block: BeautifulSoup) -> dict:
    return block.data


# def __get_redirect_result(trailer: dict):
#     def modify_link(link):
#         link['url'] = link['url'].replace('getlink', 'gettrailer')
#         response = requests.head(link['url'])
#         link['rurl'] = response.headers.get('location', '')
#         return link
#     trailer['links'] = list(map(modify_link, trailer['links']))
#     return trailer


# def __filter_only_mp4_links(trailer: dict):
#     trailer['links'] = list(
#         filter(lambda l: 'mp4' in l['rurl'], trailer['links']))
#     return trailer


def __filter_empty_links(trailer: dict):
    return len(trailer['links']) if 'links' in trailer else 0


def parse_trailers(movie_id: int, cachedir, cachetime):
    global CACHEDIR, CACHETIME
    CACHEDIR = cachedir
    CACHETIME = cachetime
    return list(compose(
        __get_list_page,
        __get_gp_links_from_list_page,
        __get_blocks_from_links,
        to_map(__linksgp_to_pages),
        # add data attribute
        # to_map(__add_data_attr),
        # parse blocks
        to_map(__get_title),
        # __get_links_from_blocks,
        to_map(__get_video_iframe),
        to_map(__get_links_from_frame_block),
        to_map(__get_posters),
        to_map(__separate_data),
        # parse trailers links
        # to_map(__get_redirect_result),
        # filter
        # to_map(__filter_only_mp4_links),
        # to_filter(__filter_empty_links),
        list
    )(movie_id))
