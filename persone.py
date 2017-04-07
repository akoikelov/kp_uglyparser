import dateparser
from delorean import Delorean
from datetime import datetime
from bs4 import BeautifulSoup, SoupStrainer
import logging

from typing import List

from .utils.get_page import LinkGP, get_pages
from .settings import KINOPOISK_LINK

_cachedir = None
_cachetime = None


class Persone:
    def __init__(self, ids, cachedir, cachetime=3600 * 48):
        """
        Create Persone parser and get info about persons
        :param ids: string like 1,2,3,4 ...
        :param cachedir: 
        :param cachetime: 
        """
        global _cachetime, _cachedir
        self.ids = ids.split(',')
        self.persones = []
        _cachedir = cachedir
        _cachetime = cachetime

        self.persones = self.parse(self.ids)

    @property
    def full(self):
        if len(self.persones) == 1:
            return self.persones[0]
        else:
            return self.persones

    def parse(self, persone_ids):
        """
        parse
        :param persone_ids: 
        """
        return Persone.parse_soups(Persone.create_soups(self.get_requests(persone_ids)))

    @staticmethod
    def get_requests(id_list: List) -> List[LinkGP]:
        links = [LinkGP("{kp_link}/name/{p_id}/".format(p_id=i_d, kp_link=KINOPOISK_LINK), id=i_d) for i_d in id_list]
        return get_pages(links, cachedir=_cachedir, cachetime=_cachetime)

    @staticmethod
    def create_soups(links: List[LinkGP]):
        """Create Soups objects from self.reqs"""
        strainer = SoupStrainer('div', attrs={'id': 'viewPeopleInfoWrapper'})
        soups = []
        # noinspection PyTypeChecker
        for link in links:
            link.req.encoding = 'utf-8'
            if link.status_code == 200:
                soup = BeautifulSoup(link.content, 'lxml', parse_only=strainer, from_encoding='utf-8')
                soup.person_id = link.additional['id']
                soup.link = link
                soups.append(soup)
            else:
                logging.error("Bad response from kinopoisk; Status code: {0}; Persone id: {1}"
                              .format(link.status_code, link.additional.id))
        return soups

    @staticmethod
    def parse_soups(soups):
        """Walk on soups and get information about persones"""
        result = []
        for soup in soups:
            result.append({
                'id': int(soup.person_id),
                'nameru': Persone.get_name(soup),
                'nameen': Persone.get_name_en(soup),
                'birthdate': Persone.get_birthdate(soup),
                'diedate': Persone.get_diedate(soup),
                'birthplace': Persone.get_birthplace(soup),
                'photo': Persone.get_photourl(soup),
            })
        return result

    # Parse funcs
    @staticmethod
    def get_name(soup):
        nameru = soup.find("h1", class_="moviename-big")
        return nameru.text

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
            birthplace.append(place.text)
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
