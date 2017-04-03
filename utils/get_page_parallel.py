import logging
import threading
import time
from typing import List, Union, Dict, Callable

from .get_page import GetPage


def mkreq(link: str, requests_list: List[GetPage], **kwargs):
    """
    Create GetPage
    :param link:
    :param requests_list: List in which it is necessary to put object of GetPage
    :return:
    """
    if len(kwargs) > 1:
        new_gp = {
            'req': GetPage(link, 'main_kinopoisk'),
            **kwargs
        }
        pass
    else:
        new_gp = GetPage(link, 'main_kinopoisk')
    requests_list.append(new_gp)


# noinspection PyTypeChecker
def get_pages(page_links: Union[List[str], List[Dict]], sleep=0.10, *, callback: Callable = None) -> List[GetPage]:
    """
    Get pages in threads
    :param page_links: If this argument is list of dicts, each dict must contain field "url"
    :param sleep:
    :return: list of GetPage
    """
    requests_list = []  # type List[GetPage]
    threads_list = []

    for link in page_links:
        if type(link) == str:
            thread = threading.Thread(target=mkreq, args=(link, requests_list))

        elif type(link) == dict:
            if isinstance(link['url'], str):
                thread = threading.Thread(target=mkreq, args=(
                    link['url'], requests_list), kwargs=link)
            else:
                logging.error("First element is not \"str\"")
        else:
            return False

        threads_list.append(thread)
        thread.start()
        time.sleep(sleep)

    for thread in threads_list:
        thread.join()
    
    if callback:
        for req in requests_list:
            callback(req)
    else:
        return [req for req in requests_list]
