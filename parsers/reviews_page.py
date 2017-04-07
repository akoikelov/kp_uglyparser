import re
import math

from typing import List, Union

from bs4 import BeautifulSoup, SoupStrainer
import dateparser
from ..utils.get_page import get_pages, LinkGP, get_page


class ReviewsPageParser:
    """
    Parser of reviews for film
    WARNING! This parser work with plus.kinopoisk.ru
    """
    reviews = []
    film_id = None
    blocks = []  # type: List[BeautifulSoup]
    _page = 1
    _page_count = None
    _links = []
    _reviews = []

    @property
    def full(self):
        return self.reviews

    def generate_url(self, page: int = 0):
        return "https://www.kinopoisk.ru/film/{0}/ord/rating/perpage/200/page/{1}".format(self.film_id, page)

    def __init__(self, film_id):
        self.film_id = film_id
        self.cachedir = None
        self.cachetime = None

    def start(self):
        self.parse()

    def parse(self):
        self.get_first_page()
        if self._page_count > 1:
            self.get_another_pages()
        self.get_subsoup_from_block()
        self.read_soups()

    def get_another_pages(self):
        linksgp = self.generate_links(self.film_id, self._page_count)
        linksgp = get_pages(linksgp, cachedir=self.cachedir, cachetime=self.cachetime)
        if linksgp:
            for linkgp in linksgp:
                self.blocks.append(
                    self.generate_block_soup_from_str(linkgp.content))

    @staticmethod
    def generate_links(film_id, page_count):
        return [LinkGP("https://www.kinopoisk.ru/film/{0}/ord/rating/perpage/200/page/{1}".format(film_id, page + 1)) for page in range(page_count)][1:]

    def get_first_page(self):
        """Get block from first page and detect count of pages"""
        first_block = self.get_reviews_block_soup(1)
        self._page_count = self.get_pages_count(first_block)
        self.blocks.append(first_block)

    @staticmethod
    def get_pages_count(soup: BeautifulSoup):
        soup = soup.find("div", class_='pagesFromTo')  # type: BeautifulSoup
        if soup:
            match = re.match(r'(\d+.\d+ из )(?P<full_count>\d+)', soup.text)
            if match:
                reviews_count = int(match.group('full_count'))
                return math.ceil(reviews_count / 200)

    def get_reviews_block_soup(self, page: int) -> Union[BeautifulSoup, bool]:
        """TODO"""
        rewiews_linkgp = get_page(LinkGP(self.generate_url(page)), cachedir=self.cachedir, cachetime=self.cachetime)
        page_soup = self.generate_block_soup_from_str(rewiews_linkgp.content)
        # if this block is empty?
        if page_soup.ul:
            return page_soup
        else:
            return False

    @staticmethod
    def generate_block_soup_from_str(page_text):
        strainer = SoupStrainer("div", class_="clear_all")
        return BeautifulSoup(page_text, 'lxml', parse_only=strainer)

    def get_subsoup_from_block(self):
        for block in self.blocks:
            reviews_items = block.find_all("div", class_="response")
            if reviews_items:
                self._reviews += reviews_items

    def read_soups(self):
        for page in self._reviews:
            # getting of type (negative, positive, neutral)
            class_list = page.attrs['class']
            if 'good' in class_list:
                review_type = "positive"
            elif 'bad' in class_list:
                review_type = "negative"
            else:
                review_type = 'neutral'
            # getting Author poster
            author_poster = 'https://st.kinopoisk.ru/images/no-poster.gif'
            author_span = page.find('div', attrs={'itemprop': 'author'})
            if author_span.img:
                if author_span.img.attrs:
                    if 'src' in author_span.img.attrs:
                        author_poster = author_span.img.attrs['src']
            self.reviews.append({
                'type': review_type,
                'id': int(re.search(r'\d+', page.attrs['id']).group(0)),
                'title': page.find('p', class_='sub_title').text,
                'text': page.find('span', attrs={'itemprop': 'reviewBody'}).text,
                'author_name': page.find('p', class_='profile_name').text,
                'author_poster': author_poster,
                'create_date': int(dateparser.parse(page.find('span', class_='date').text).timestamp())
            })
