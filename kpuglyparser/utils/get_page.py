import threading

import time
from typing import Union, List, Callable

import os
import requests
import random
import logging
from grab import Grab
from grab.response import Response as GResponse
from fake_useragent import UserAgent
from .memoize import memoize_fs, check_in_cache

proxies = []
grabs = []

ua = UserAgent()
FUNC_NAME = 'get_page'


def get_grab(proxy=None):
    g = Grab()
    if proxy:
        g.setup(proxy=proxy, proxy_type='socks5', connect_timeout=60, timeout=60)
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
        grabs.append(get_grab(proxy))
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

    def set_req(self, req: Union[bool, GResponse]):
        self.req = req
        self.status_code = req.code
        self.content = req.body


def get_page(link: LinkGP, cachedir: str, cachetime: int) -> LinkGP:
    """
    Get content for link
    
    :param link: 
    :param cachedir: 
    :param cachetime: 
    :return: 
    """
    g = get_randgrab()
    link.proxy = g.config['proxy']
    if cachedir and cachetime:
        @memoize_fs(cachedir, FUNC_NAME, cachetime)
        def req_mem(url) -> Union[bool, GResponse]:
            res = g.go(url)
            if res.code == 200:
                if 'showcaptcha' not in res.url and 'DOCTYPE' in res.body[0:20].decode():
                    return res
                else:
                    logging.error("kinopoisk want your captcha; Proxy: {}".format(link.proxy))
                    return False
            else:
                return False

        response = req_mem(link.url)
        if response:
            link.set_req(req_mem(link.url))
    else:
        link.set_req(g.go(link.url))
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
def get_pages(page_links: Union[List[LinkGP], List[str]], sleep=1, *, callback: Callable = None, cachedir, cachetime) -> List[LinkGP]:
    """
    Get pages in threads
    :param cachetime:
    :param cachedir: 
    :param callback: 
    :param page_links: If this argument is list of dicts, each dict must contain field "url"
    :param sleep:
    :return: list of GetPage
    """
    ready_linksgp = []  # type List[GetPage]
    # threads_list = []

    for link in page_links:
        new_gp = get_page(link, cachedir=cachedir, cachetime=cachetime)
        ready_linksgp.append(new_gp)
        time.sleep(sleep)
        # if link is str:
        #     link = LinkGP(link)
        #
        # thread = threading.Thread(target=mkreq, args=(link, ready_linksgp, cachedir, cachetime))
        #
        # threads_list.append(thread)
        # thread.start()
        # if not check_in_cache(cachedir, FUNC_NAME, link.url):
        #     time.sleep(sleep)

    # for thread in threads_list:
    #     thread.join()

    if callback:
        for linkgp in ready_linksgp:
            callback(linkgp)
    return ready_linksgp
