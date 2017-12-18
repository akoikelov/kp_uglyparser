import logging
import os
import random
import re
import time
from typing import Callable, List, Union

import grab
import requests
from fake_useragent import UserAgent
from grab import Grab
from grab.response import Response as GResponse

from .memoize import check_in_cache, memoize_fs

proxies = []
grabs = []

ua = UserAgent()
FUNC_NAME = 'get_page'


def get_grab(proxy=None, login=None, password=None):
    g = Grab()
    if proxy:
        g.setup(proxy=proxy, proxy_type='socks5',
                connect_timeout=10, timeout=10)
    if login and password:
        g.setup(proxy_userpwd="{}:{}".format(login, password))
    return g


def check_proxy(checked_proxy):
    try:
        requests.get('http://google.com', proxies={
            'http': checked_proxy,
            'https': checked_proxy
        }, timeout=2)

        return True
    except requests.ReadTimeout:
        print('Broken proxy:', checked_proxy)
        return False
    except requests.ConnectionError:
        print('Broken proxy:', checked_proxy)
        return False


PROXIES_ENV = os.environ.get("PROXIES")
if PROXIES_ENV:
    proxies = PROXIES_ENV.split(';')
    for proxy in proxies:
        match = re.match(
            r'((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{3,5}))(\{((.*?):(.*?))\}|);?', proxy)
        host = match.group(2)
        port = match.group(3)
        login = match.group(6)
        password = match.group(7)
        grabs.append(get_grab("{}:{}".format(host, port), login, password))
grabs.append(get_grab())


# noinspection SpellCheckingInspection
def get_randgrab():
    return random.choice(grabs)


class LinkGP:
    def __init__(self, url: str, **kwargs):
        """
        :param url: 
        :param args: another arguments which saved in the field "additional'
        """
        self.url = url
        self.additional = kwargs  # type: dict

        self.req = None
        self.status_code = None
        self.content = None
        self.proxy = None
        self.final_url = None

    def set_req(self, req: Union[bool, GResponse]):
        self.req = req
        self.status_code = req.code
        self.content = req.body
        self.final_url = req.url


def get_from_grab(url, link, ):
    g = get_randgrab()
    try:
        res = g.go(url)
        return res
    except grab.error.GrabConnectionError as error:
        logging.error("Kinopoisk bad response; May be proxy server is failed; Proxy: {}".format(
            g.config['proxy']))
        return get_from_grab(url, link)
    except grab.error.GrabTimeoutError:
        logging.error("Grab timeout")
        return get_from_grab(url, link)
    except BaseException as error:
        logging.error(
            "Error on getting page; Grab proxy: {}".format(g.config['proxy']))
        raise error


def get_page(link: LinkGP, cachedir: str, cachetime: int) -> LinkGP:
    """
    Get content for link
    :param link: 
    :param cachedir: 
    :param cachetime: 
    :return: 
    """
    if cachedir and cachetime:
        @memoize_fs(cachedir, FUNC_NAME, cachetime)
        def req_mem(url) -> Union[bool, GResponse]:
            res = get_from_grab(url, link)
            if res.code == 200:
                if 'showcaptcha' not in res.url and 'DOCTYPE' in res.body[0:20].decode():
                    return res
                else:
                    logging.error(
                        "kinopoisk want your captcha; Proxy: {}".format(link.proxy))
                    return False
            else:
                return False

        response = req_mem(link.url)
        if response:
            link.set_req(response)
    else:
        link.set_req(get_from_grab(link.url, link))
    return link


def mkreq(link: LinkGP, ready_links_list: List[LinkGP], cachedir, cachetime):
    """
    Create GetPage
    :param cachetime: 
    :param cachedir: 
    :param link:
    :param ready_links_list: List in which it is necessary to put object of GetPage
    :return:
    """
    new_gp = get_page(link, cachedir=cachedir, cachetime=cachetime)
    ready_links_list.append(new_gp)


# noinspection PyTypeChecker
def get_pages(page_links: Union[List[LinkGP], List[str]], sleep=3, *, callback: Callable = None, cachedir, cachetime) -> List[LinkGP]:
    """
    Get pages in threads
    :param cachetime:
    :param cachedir: 
    :param callback: 
    :param page_links: If this argument is list of dicts, each dict must contain field "url"
    :param sleep:
    :return: list of GetPage
    """
    ready_linksgp = []  # type: List[GetPage]

    for link in page_links:
        new_gp = get_page(link, cachedir=cachedir, cachetime=cachetime)
        ready_linksgp.append(new_gp)
        time.sleep(sleep)

    if callback:
        for linkgp in ready_linksgp:
            callback(linkgp)
    return ready_linksgp


def get_pages_g(page_links: Union[List[LinkGP], List[str]], sleep=3, *, cachedir, cachetime) -> List[LinkGP]:
    for link in page_links:
        new_gp = get_page(link, cachedir=cachedir, cachetime=cachetime)
        yield new_gp
        time.sleep(sleep)