import re
from typing import List

import requests
from bs4 import BeautifulSoup, SoupStrainer

from ..utils.get_page import LinkGP, get_page, get_pages, get_pages_g
from ..utils.decorators import compose, to_filter, to_map

TRAILER_PAGE_STRAINER = SoupStrainer("td", class_='news')
MAIN_TRAILERS_PAGE_STRAINER = SoupStrainer("div", class_='block_left')
CACHEDIR = ""
CACHEDIR = ""


def __get_list_page(movie_id) -> BeautifulSoup:
    """ return table of trailers from page"""
    link = "https://www.kinopoisk.ru/film/{}/video/".format(movie_id)
    gplink = get_page(LinkGP(link), cachedir=CACHEDIR, cachetime=CACHEDIR)
    return BeautifulSoup(gplink.content, 'lxml', parse_only=MAIN_TRAILERS_PAGE_STRAINER)


def __get_gp_links_from_list_page(list_page: BeautifulSoup) -> List[LinkGP]:
    links = list_page.find_all('a', attrs={
        "href": re.compile(r"/film/.+/video/(\d+)/$"),
        "style": None
    })
    return [LinkGP("https://www.kinopoisk.ru{}".format(i.attrs['href'])) for i in links if i.attrs['href']]


def __get_blocks_from_links(links: List[LinkGP]) -> List[BeautifulSoup]:
    return get_pages_g(links, cachedir=CACHEDIR, cachetime=CACHEDIR)


def __linksgp_to_pages(link: List[LinkGP]):
    return BeautifulSoup(link.content, 'lxml', parse_only=TRAILER_PAGE_STRAINER)


def __add_data_attr(block: BeautifulSoup) -> BeautifulSoup:
    block.data = {}
    return block


def __get_title(block: BeautifulSoup) -> BeautifulSoup:
    try:
        title_tag = block.find_all(
            'td', attrs={"style": "color: #333; font-size: 27px; padding-left: 30px"})[0]
        title = title_tag.text
        block.data['title'] = title
    except:
        block.data['title'] = "Error"
    return block

# def __get_runtime_from_blocks(blocks: List[BeautifulSoup]):
#     return map()

# def __get_public_date_from_blocks()


def __get_links_from_blocks(blocks: List[BeautifulSoup]):
    links_reg = re.compile(
        "https?:\/\/(www\.kinopoisk\.ru|)\/getlink\.php\?type=trailer&trailer_id=(\d+?)&quality=(.+?)$")

    def parse_link(link):
        match = links_reg.search(link.attrs['href'])
        return {
            'quality':  match.group(3),
            'url':  match.group(0),
        }

    def get_links(block):
        links = block.find_all('a', attrs={'href': links_reg})
        block.data['links'] = list(map(parse_link, links))
        return block
    return map(get_links, blocks)


def __get_posters(block: BeautifulSoup) -> BeautifulSoup:
    link = block.find("link", attrs={
        "itemprop": "thumbnailUrl"
    })
    block.data['poster'] = link.attrs.get("href")
    return block


def __separate_data(block: BeautifulSoup) -> dict:
    return block.data


def __get_redirect_result(trailer: dict):
    replaced_link = trailer['links'][0]['url'].replace('getlink', 'gettrailer')
    response = requests.head(replaced_link)
    trailer['links'][0]['url'] = response.headers.get('location')
    return trailer


def __filter_only_mp4_links(trailer: dict):
    trailer['links'] = list(
        filter(lambda l: 'mp4' in l['url'], trailer['links']))
    return trailer


def __filter_empty_links(trailer: dict):
    return len(trailer['links'])


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
        to_map(__add_data_attr),
        # parse blocks
        to_map(__get_title),
        __get_links_from_blocks,
        to_map(__get_posters),
        to_map(__separate_data),
        # parse trailers links
        to_map(__get_redirect_result),
        # filter
        to_map(__filter_only_mp4_links),
        to_filter(__filter_empty_links),
        list
    )(movie_id))
