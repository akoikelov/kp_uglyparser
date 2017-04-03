import dateparser
from delorean import Delorean
from datetime import datetime
from bs4 import BeautifulSoup, SoupStrainer
import logging
from .utils.get_page_parallel import get_pages
from .settings import KINOPOISK_LINK


class Persone:
    # default fields
    id = None
    ids = []
    reqs = []
    soups = []
    persones = []

    def __init__(self, id):
        self.id = id  # can be ids: "1234,11244,553335,774335,643566,345674"
        self.check_parameters()

    def check_parameters(self):
        """If id is int – create list of ids from one element"""
        if isinstance(self.id, int):
            self.ids.append(self.id)
        elif isinstance(self.id, str):
            ids = self.id.split(",")
            if ids:
                self.ids = ids
            else:
                logging.error("invalid string of id; Cannot find even one id")
                return
        else:
            logging.error("Unexpected type of id")
            return
        self.create_requests()

    @property
    def full(self):
        if len(self.persones) == 1:
            return self.persones[0]
        else:
            return self.persones

    def create_requests(self):
        """Get pages of persons from ids list"""
        self.reqs = get_pages([{"url": "{kp_link}/name/{p_id}/".format(
            p_id=i_d, kp_link=KINOPOISK_LINK), "id": i_d} for i_d in self.ids])
        self.create_soups_list()

    def create_soups_list(self):
        """Create Soups objects from self.reqs"""
        strainer = SoupStrainer('div', attrs={'id': 'viewPeopleInfoWrapper'})
        # noinspection PyTypeChecker
        for req, id in [(i['req'], i['id']) for i in self.reqs]:
            if req.status_code == 200:
                self.soups.append({
                    'soup': BeautifulSoup(req.content, 'lxml', parse_only=strainer),
                    'id': id
                })
            else:
                logging.error("Bad response from kinopoisk; Status code: {0}; Persone id: {1}"
                              .format(
                                  req.status_code,
                                  id
                              ))
        self.parse_soups()

    def parse_soups(self):
        """Walk on soups and get information about persones"""
        for soup in self.soups:
            self.persones.append(Persone.parse(soup))

    @staticmethod
    def parse(soup):
        id = soup['id']
        soup = soup['soup']
        return {
            'id': int(id),
            'nameru': Persone.get_name(soup),
            'nameen': Persone.get_name_en(soup),
            'birthdate': Persone.get_birthdate(soup),
            'diedate': Persone.get_diedate(soup),
            'birthplace': Persone.get_birthplace(soup),
            'photo': Persone.get_photourl(soup),
        }

    # Parse funcs
    @staticmethod
    def get_name(soup):
        nameru = soup.find("h1", class_="moviename-big")
        return nameru.string

    @staticmethod
    def get_name_en(soup):
        nameen = soup.find(
            "span", attrs={"itemprop": "alternateName"})
        if nameen:
            return nameen.string.strip()
        else:
            return False

    @staticmethod
    def get_birthdate(soup):
        birthdate = soup.find("td", attrs={"class": "birth"})
        if 'birthdate' in birthdate.attrs.keys():
            birthdate = birthdate.attrs["birthdate"]  # str year-month-day
            delorean_date = Delorean(datetime.strptime(
                birthdate, '%Y-%m-%d'), timezone='UTC')
            return int(delorean_date.epoch)
        else:
            return 0

    @staticmethod
    def get_diedate(soup):
        diedate = soup.find("td", string="дата смерти")
        if diedate:
            diedate = diedate.next_sibling.find("span").next
            delorean_date = Delorean(dateparser.parse(diedate), timezone='UTC')
            return int(delorean_date.epoch)
        else:
            return None

    @staticmethod
    def get_birthplace(soup):
        birthplace = []
        places = soup.find(
            "td", string="место рождения").next_sibling.find_all('a')  # 'a' tags
        for place in places:
            birthplace.append(place.string)
        return birthplace

    @staticmethod
    def get_photourl(soup):
        photo_block = soup.find(class_="originalPoster")
        if not photo_block:
            photo_block = soup.find(class_="film-img-box")

        if photo_block:
            img = photo_block.find('img')
            img_link = img.attrs['src']
            return img_link
        else:
            return None

    def __str__(self):
        return "<Persons>"
