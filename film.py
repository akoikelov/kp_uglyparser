import logging
from .settings import KINOPOISK_LINK
from .parsers.image_page import ImagePageParser
from .parsers.trailers_page import TrailersPageParser
from .parsers.main_page import MainPageParser
from .parsers.reviews_page import ReviewsPageParser
from .parsers.staff_page import StaffPageParser

from .utils.memoize import memoize_fs


class Film(object):
    """
    Parse information about movie;
    IF you wonna to cache results for duplicated arguments you mau to use the cache
    """

    def __init__(self, film_id=0, cachedir=None, cachetime=3600 * 48):
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
        @memoize_fs(self.cachedir, "parse_main_page", self.cachetime)
        def parse(*args, **kwargs):
            parser = MainPageParser(*args, **kwargs)
            return parser.full
        self.main_page = parse(src, self.id)

    def parse_posters_page(self, src):
        @memoize_fs(self.cachedir, "parse_posters_page", self.cachetime)
        def parse(*args, **kwargs):
            parser = ImagePageParser(*args, **kwargs)
            return parser.full
        self.posters = parse(src, get_main_poster=self.id)

    def parse_stills_page(self, src):
        @memoize_fs(self.cachedir, "parse_stills_page", self.cachetime)
        def parse(*args, **kwargs):
            parser = ImagePageParser(*args, **kwargs)
            return parser.full
        self.stills = parse(src)

    def parse_fanart_page(self, src):
        @memoize_fs(self.cachedir, "parse_fanart_page", self.cachetime)
        def parse(*args, **kwargs):
            parser = ImagePageParser(*args, **kwargs)
            return parser.full
        self.fanart = parse(src)

    def parse_covers_page(self, src):
        @memoize_fs(self.cachedir, "parse_covers_page", self.cachetime)
        def parse(*args, **kwargs):
            parser = ImagePageParser(*args, **kwargs)
            return parser.full
        self.covers = parse(src)

    def parse_wall_page(self, src):
        @memoize_fs(self.cachedir, "parse_wall_page", self.cachetime)
        def parse(*args, **kwargs):
            parser = ImagePageParser(*args, **kwargs)
            return parser.full
        self.wall = parse(src)

    def parse_concept_page(self, src):
        @memoize_fs(self.cachedir, "parse_concept_page", self.cachetime)
        def parse(*args, **kwargs):
            parser = ImagePageParser(*args, **kwargs)
            return parser.full
        self.concept = parse(src)

    def parse_trailers_page(self, src):
        @memoize_fs(self.cachedir, "parse_trailers_page", self.cachetime)
        def parse(*args, **kwargs):
            parser = TrailersPageParser(*args, **kwargs)
            return parser.full
        self.trailers = parse(src, self.id)

    def parse_reviews_page(self, src: str):
        @memoize_fs(self.cachedir, "parse_reviews_page", self.cachetime)
        def parse(*args, **kwargs):
            parser = ReviewsPageParser(*args, **kwargs)
            return parser.full
        self.reviews = parse(self.id)

    def parse_staff_page(self, src: str):
        @memoize_fs(self.cachedir, "parse_staff_page", self.cachetime)
        def parse(*args, **kwargs):
            parser = StaffPageParser(*args, **kwargs)
            return parser.full
        self.staff = parse(src)
