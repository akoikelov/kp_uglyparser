import logging
from .parsers.image_page import ImagePageParser
from .parsers.main_page import MainPageParser
from .parsers.reviews_page import ReviewsPageParser
from .parsers.staff_page import StaffPageParser
from .parsers.trailers_page import parse_trailers


class Film(object):
    """
    Parse information about movie;
    IF you wonna to cache results for duplicated arguments you mau to use the cache
    """

    def __init__(self, film_id=0, cachedir=None, cachetime=3600 * 24 * 5):
        # set defaults
        self.id = film_id
        self.pages = None
        self.main_page = None
        self.posters = []
        self.stills = []
        self.fanart = []
        self.covers = []
        self.wall = []
        self.concept = []
        self.trailers = []
        self.reviews = []
        self.staff = []
        # functions
        self.register_pages()
        self.stills = []
        self.cachedir = cachedir
        self.cachetime = cachetime

    @property
    def full(self):
        return {
            'id': self.id,
            'main_page': self.main_page,
            'posters': self.posters,
            'stills': self.stills,
            'fanart': self.fanart,
            'covers': self.covers,
            'wall': self.wall,
            'concept': self.concept,
            'trailers': self.trailers,
            'reviews': self.reviews,
            'staff': self.staff,
        }

    def register_pages(self):
        self.pages = {
            # TODO write method of getting main page
            'main_page': {
                'src': "https://www.kinopoisk.ru/film/{0}/".format(self.id),
                'parser': self.parse_main_page
            },
            # Image pages
            'posters_page': {
                'src': "https://www.kinopoisk.ru/film/{0}/posters/".format(self.id),
                'parser': self.parse_posters_page
            },
            'stills_page': {
                'src': "https://www.kinopoisk.ru/film/{0}/stills/".format(self.id),
                'parser': self.parse_stills_page
            },
            'fanart_page': {
                'src': "https://www.kinopoisk.ru/film/{0}/fanart/".format(self.id),
                'parser': self.parse_fanart_page
            },
            'covers_page': {
                'src': "https://www.kinopoisk.ru/film/{0}/covers/".format(self.id),
                'parser': self.parse_covers_page
            },
            'wall_page': {
                'src': "https://www.kinopoisk.ru/film/{0}/wall/".format(self.id),
                'parser': self.parse_wall_page
            },
            'concept_page': {
                'src': "https://www.kinopoisk.ru/film/{0}/concept/".format(self.id),
                'parser': self.parse_concept_page
            },
            # Trailers pages
            'trailers_page': {
                'src': "https://www.kinopoisk.ru/film/{0}/video/".format(self.id),
                'parser': self.parse_trailers_page
            },
            'reviews_page': {
                'src': "https://plus.kinopoisk.ru/film/{0}/details/reviews/?page=1&tabId=reviews&chunkOnly=1".format(self.id),
                'parser': self.parse_reviews_page
            },
            'staff_page': {
                'src': "https://www.kinopoisk.ru/film/{0}/cast/".format(self.id),
                'parser': self.parse_staff_page
            }
        }

    # start parser func
    def get_content(self, page='main_page'):
        if page in self.pages.keys():
            self.pages[page]['parser'](self.pages[page]['src'])
        else:
            logging.error(
                "Undefinded page: '{}'; Select from ['main_page', 'posters_page', 'stills_page']".format(page))

    def parse_main_page(self, src):
        parser = MainPageParser(src, self.id)
        parser.cachedir = self.cachedir
        parser.cachetime = self.cachetime
        parser.start()
        self.main_page = parser.full

    def parse_posters_page(self, src):
        parser = ImagePageParser(src)
        parser.cachedir = self.cachedir
        parser.cachetime = self.cachetime
        parser.start(self.id)
        self.posters = parser.full

    def parse_stills_page(self, src):
        parser = ImagePageParser(src)
        parser.cachedir = self.cachedir
        parser.cachetime = self.cachetime
        parser.start()
        self.stills = parser.full

    def parse_fanart_page(self, src):
        parser = ImagePageParser(src)
        parser.cachedir = self.cachedir
        parser.cachetime = self.cachetime
        parser.start()
        self.fanart = parser.full

    def parse_covers_page(self, src):
        parser = ImagePageParser(src)
        parser.cachedir = self.cachedir
        parser.cachetime = self.cachetime
        parser.start()
        self.covers = parser.full

    def parse_wall_page(self, src):
        parser = ImagePageParser(src)
        parser.cachedir = self.cachedir
        parser.cachetime = self.cachetime
        parser.start()
        self.wall = parser.full

    def parse_concept_page(self, src):
        parser = ImagePageParser(src)
        parser.cachedir = self.cachedir
        parser.cachetime = self.cachetime
        parser.start()
        self.concept = parser.full

    def parse_trailers_page(self, src):
        self.trailers = parse_trailers(self.id, self.cachedir, self.cachetime)

    def parse_reviews_page(self, src: str):
        parser = ReviewsPageParser(self.id)
        parser.cachedir = self.cachedir
        parser.cachetime = self.cachetime
        parser.start()
        self.reviews = parser.full

    def parse_staff_page(self, src: str):
        parser = StaffPageParser(src)
        parser.cachedir = self.cachedir
        parser.cachetime = self.cachetime
        parser.start()
        self.staff = parser.full
