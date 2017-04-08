import threading

import time
from typing import Union, List, Callable

import os
import logging
import requests
import random
from fake_useragent import UserAgent
from .memoize import memoize_fs, check_in_cache

proxies = []
sessions = []

ua = UserAgent()
FUNC_NAME = 'get_page'


def get_session(proxy=None):
    session = requests.Session()
    session.headers = {
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4',
        'Accept-Encoding': 'gzip, deflate, sdch, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'User-Agent': getattr(ua, random.choice(['chrome', 'opera', 'firefox'])),
        'Accept-Charset': 'utf-8,windows-1251;q=0.7,*;q=0.7',
        'Host': 'www.kinopoisk.ru'
    }
    if proxy:
        session.proxies = {
            'http': proxy,
            'https': proxy
        }

    # noinspection PyUnresolvedReferences
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=1000, pool_maxsize=1000)
    session.mount('https://', adapter)
    return session


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


if os.environ.get("PROXIES"):
    proxies_str = os.environ.get("PROXIES")
    proxies = proxies_str.split(';')
    for proxy in proxies:
        if check_proxy(proxy):
            sessions.append(get_session(proxy))
sessions.append(get_session())


def get_randsession():
    return random.choice(sessions)


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

    def set_req(self, req: Union[bool, requests.Response]):
        self.req = req
        self.status_code = req.status_code
        self.content = req.content


def get_page(link: LinkGP, cachedir: str, cachetime: int) -> LinkGP:
    """
    Get content for link
    
    :param link: 
    :param cachedir: 
    :param cachetime: 
    :return: 
    """
    session = get_randsession()
    link.proxy = session.proxies
    if cachedir and cachetime:
        @memoize_fs(cachedir, FUNC_NAME, cachetime)
        def req_mem(url) -> Union[bool, requests.Response]:
            req = session.get(url)
            if req.status_code == 200:
                if 'showcaptcha' not in req.url:
                    return req
                else:
                    logging.error("kinopoisk want your captcha; Proxy: {}".format(session.proxies))
                    return False
            else:
                return False

        response = req_mem(link.url)
        if response:
            link.set_req(req_mem(link.url))
    else:
        link.set_req(session.get(link.url))
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
    threads_list = []

    for link in page_links:
        if link is str:
            link = LinkGP(link)

        thread = threading.Thread(target=mkreq, args=(link, ready_linksgp, cachedir, cachetime))

        threads_list.append(thread)
        thread.start()
        if not check_in_cache(cachedir, FUNC_NAME, link.url):
            time.sleep(sleep)

    for thread in threads_list:
        thread.join()

    if callback:
        for linkgp in ready_linksgp:
            callback(linkgp)
    return ready_linksgp
