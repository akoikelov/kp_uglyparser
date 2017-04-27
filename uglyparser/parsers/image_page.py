import re
from typing import Union, List
from ..utils.get_page import get_page, get_pages, LinkGP
from bs4 import BeautifulSoup, SoupStrainer
import logging
from ..settings import LINK_TO_MAIN_PAGE, KINOPOISK_LINK


class ImagePageParser:
    """
    Get images for movie from images page; Result will be in field "pictures"
    """

    def __init__(self, src: str):
        """
        Init instance of ImagePageParser
        :param src: Link to page with images (Example: https://www.kinopoisk.ru/film/[film_id]/stills/)
        """
        self.pictures = []  # future result
        self.pictures_pages = []  # type: List[BeautifulSoup]
        self.src = src
        self.cachedir = None
        self.cachetime = None

    def start(self, get_main_poster: Union[bool, int] = False):
        self.parse()

        if type(get_main_poster) is int:
            self.get_poster_from_main_page(get_main_poster)

    def parse(self, page=1):
        """
        Get page of list of pictures(thumbnails and links)
        """
        # get pictures page
        strainer = SoupStrainer('div', attrs={'class': 'block_left'})
        logging.debug("Start getting pictures_page")
        pictures_page_linkgp = get_page(LinkGP(self.src + "page/{0}/".format(page)), self.cachedir, self.cachetime)
        logging.debug("Finish getting pictures_page")
        if pictures_page_linkgp.status_code == 200:
            if ImagePageParser.test_on_404(pictures_page_linkgp.content):
                # save page(BeautifulSoup object) in self.pictures_pages
                self.pictures_pages.append(BeautifulSoup(
                    pictures_page_linkgp.content, 'lxml', parse_only=strainer))
                self.test_page_count(page)
        else:
            logging.info("Cannot get pictures page; Status code: {0} ; Link: {1}".format(
                pictures_page_linkgp.status_code, self.src))

    @property
    def full(self):
        return self.pictures

    @staticmethod
    def test_on_404(html_of_page):
        """
        Because kinopoisk not respond with error 404 if
        movie have not the posters or the skills
        we must check page by another way
        :return:
        """
        soup = BeautifulSoup(html_of_page, 'lxml')
        fotos_block = soup.find('table', class_='fotos')
        if fotos_block:
            return True
        else:
            return False

    def test_page_count(self, prev_page):
        """
        Read page of list of images;
        For example: https://www.kinopoisk.ru/film/840152/posters/page/1;
        and check: should we get more pages; If not that we get images from geted images
        """
        pages_block = self.pictures_pages[0].find("ul", class_='list')
        page_count = 0
        if pages_block:
            pages_list = pages_block.find_all("li", class_='')
            page_count = len(pages_list)
        if len(self.pictures_pages) < page_count:
            self.parse(prev_page + 1)
        else:
            logging.info(
                "List of main pages is full; Total count: {0}".format(prev_page))
            self.get_pictures_links()

    def get_pictures_links(self):
        """
        Get all pictures from self.pictures_pages
        """
        for page in self.pictures_pages:
            photos_block = page.find("table", class_='fotos')
            links = photos_block.find_all("a")
            for link in links:
                if not link.img:
                    continue
                self.pictures.append({
                    "href": KINOPOISK_LINK + link.attrs['href'],
                    "thumbnail": link.img.attrs['src'],
                    "full": None
                })
        logging.debug(
            "We have collected links to images pages; Count of links: %s" % len(self.pictures))
        self.walk_on_pictures()

    def walk_on_pictures(self):
        """
        Get full size for pictures
        """
        strainer = SoupStrainer("table", id='main_table')

        def filter_without_sm_pictures(pic):
            """
            function for filtering of pictures with thumbnail link matched sm_{pic_id}
            """
            return "thumbnail" in pic and "sm_" not in pic['thumbnail']

        def append_full_size_image_to_pic(linkgp):
            """
            callback function get req object and another arguments that
            """
            image_page = BeautifulSoup(
                linkgp.content, 'lxml', parse_only=strainer)
            if image_page:
                img = image_page.find('img', id='image')

        # get images page for pics which don't have link to the thumbnail like sm_id.jpg
        # and execute callback function append_full_size_to_pic for every result
        pics_for_getting = list(filter(filter_without_sm_pictures, self.pictures))
        if len(pics_for_getting) > 0:
            get_pages(
                [LinkGP(pic['href'], ) for pic in pics_for_getting],
                cachedir=self.cachedir, cachetime=self.cachetime, callback=append_full_size_image_to_pic
            )

        for pic in self.pictures:
            if pic not in pics_for_getting:
                pic['full'] = pic['thumbnail'].replace("sm_", "")

    # MAIN POSTER FROM FILM PAGE

    def insert_main_poster_in_list(self, poster):
        self.pictures.insert(0, poster)

    def get_poster_from_main_page(self, movie_id: int):
        strainer = SoupStrainer("div", class_="film-img-box")
        main_page_link = LINK_TO_MAIN_PAGE.format(movie_id)
        linkgp_main_page = get_page(LinkGP(main_page_link), cachedir=self.cachedir, cachetime=self.cachetime)
        if linkgp_main_page.status_code == 200:
            main_page = BeautifulSoup(
                linkgp_main_page.content, 'lxml', parse_only=strainer)
            if main_page:
                img = main_page.find('img')  # type: BeautifulSoup
                if img and img.parent and 'onclick' in img.parent.attrs:
                    popup_link = re.search(
                        r"(?<=openImgPopup\(').+(?='\))", img.parent.attrs['onclick'])
                    if popup_link:
                        self.insert_main_poster_in_list({
                            "src": "http://kinopoisk.ru" + popup_link.group(),
                            "thumbnail": img.attrs['src']
                        })
