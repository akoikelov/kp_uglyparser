"""
sdfsfd
"""
import pickle
import os
import logging
import requests


class GetPage(object):
    __headers = {
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4',
        'Accept-Encoding': 'gzip, deflate, sdch, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36',
        'Accept-Charset': 'utf-8,windows-1251;q=0.7,*;q=0.7',
        'Host': 'www.kinopoisk.ru'
    }

    __cookies = None
    __cookies_path = None
    __page = None
    __request = None

    @property
    def content(self):
        return self.__page

    @property
    def status_code(self):
        return self.__request.status_code

    def __init__(self, url, page_name):
        logging.debug("New GetPage")
        page_name = 'main_kinopoisk'
        self.url = url
        # Check cookies from file and get cookies
        self.checkdir()
        # If we have cookies for this page
        self.__cookies_path = GetPage.get_cookies_path(page_name)
        if os.path.exists(self.__cookies_path):
            with open(self.__cookies_path, 'rb') as file:
                logging.debug("Cookies exist")
                self.__cookies = requests.utils.cookiejar_from_dict(
                    pickle.load(file))
        #
        self.get_page()

    def write_cookies(self):
        """
        Write cookie of last request to file;
        """
        with open(self.get_cookies_path(), 'wb') as file:
            pickle.dump(requests.utils.dict_from_cookiejar(
                self.__request.cookies), file)

    @staticmethod
    def write_cookies_static(file_path, cookie_obj):
        """
        Create file with cookies for kinopoisk.ru
        :param file_path:
        :param cookie_obj:
        :return:
        """
        with open(file_path, 'wb') as file:
            pickle.dump(requests.utils.dict_from_cookiejar(cookie_obj), file)

    @staticmethod
    def get_cookies(file_name):
        result = False
        path = GetPage.get_cookies_path(file_name)
        if os.path.exists(path):
            with open(path, 'rb') as file:
                logging.debug("Cookies exist")
                result = requests.utils.cookiejar_from_dict(pickle.load(file))

        return result

    @staticmethod
    def get_cookies_path(name='main_kinopoisk'):
        return os.path.join(os.path.dirname(os.path.realpath(os.sys.argv[0])), "cookies", "{0}.cookies".format(name))

    def get_page(self):
        if not SESSION:
            self.__request = requests.get(
                self.url, cookies=self.__cookies, headers=self.__headers)
        else:
            self.__request = SESSION.get(self.url, headers=self.__headers)

        if self.__request.status_code == 200:
            if self.__request.url == self.url:
                # self.write_cookies()
                logging.debug("Update cookie file")
            self.__page = self.__request.text
        else:
            logging.error("Request from kinopoisk not is status 200")

    @staticmethod
    def checkdir():
        if not os.path.exists(os.path.join(os.path.dirname(os.path.realpath(os.sys.argv[0])), "cookies")):
            os.makedirs(os.path.join(os.path.dirname(
                os.path.realpath(os.sys.argv[0])), "cookies"))


# noinspection PyArgumentList
SESSION = requests.Session()

# noinspection PyUnresolvedReferences
ADAPTER = requests.adapters.HTTPAdapter(
    pool_connections=1000, pool_maxsize=1000)
SESSION.mount('https://', ADAPTER)
SESSION.cookies = GetPage.get_cookies(
    'main_kinopoisk') or requests.utils.cookiejar_from_dict({})
