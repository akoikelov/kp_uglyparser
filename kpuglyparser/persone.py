import dateparser
import re
from delorean import Delorean
from datetime import datetime
from bs4 import BeautifulSoup, SoupStrainer
from .parsers.image_page import ImagePageParser
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
        links = [LinkGP("{kp_link}/name/{p_id}/view_info/ok/#trivia".format(p_id=i_d, kp_link=KINOPOISK_LINK), id=i_d) for i_d in id_list]
        return get_pages(links, cachedir=_cachedir, cachetime=_cachetime)

    @staticmethod
    def create_soups(links: List[LinkGP]):
        """Create Soups objects from self.reqs"""
        soups = []
        # noinspection PyTypeChecker
        for link in links:
            # link.req.encoding = 'utf-8'
            if link.status_code == 200:
                soup = BeautifulSoup(link.content, 'lxml', from_encoding='utf-8')
                soup.person_id = link.additional['id']
                soup.link = link
                soups.append(soup)
            else:
                logging.error("Bad response from kinopoisk; Status code: {0}; Persone id: {1}"
                              .format(link.status_code, link.additional['id']))
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
                'growth': Persone.get_growth(soup),
                'photo': Persone.get_photourl(soup),
                'photos': Persone.get_photos('{0}/name/{1}/photos/'.format(KINOPOISK_LINK, soup.person_id)),
                'filmography': Persone.get_roles(soup),
                'trivia_facts': Persone.get_trivia(soup),
                'spouse': Persone.get_spouse(soup),
                'sex': Persone.get_gender(soup)
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
    def get_growth(soup: BeautifulSoup):
        growth_block = soup.find("td", string="рост")
        if growth_block:
            growth = growth_block.next_sibling.find("span").text.replace(' м', '')
            return float(growth)

    @staticmethod
    def get_birthdate(soup):
        birthdate = soup.find("td", attrs={"class": "birth"})
        if 'birthdate' in birthdate.attrs.keys():
            birthdate = birthdate.attrs["birthdate"]  # str year-month-day
            delorean_date = Delorean(datetime.strptime(
                birthdate, '%Y-%m-%d'), timezone='UTC')
            return delorean_date.datetime.isoformat()
        else:
            return None

    @staticmethod
    def get_diedate(soup):
        diedate = soup.find("td", string="дата смерти")
        if diedate:
            diedate = diedate.next_sibling.find("span").next
            delorean_date = Delorean(dateparser.parse(diedate), timezone='UTC')
            return delorean_date.datetime.isoformat()
        else:
            return None

    @staticmethod
    def get_birthplace(soup):
        birthplace = []
        try:
            places = soup.find(
                "td", string="место рождения").next_sibling.find_all('a')  # 'a' tags
            for place in places:
                birthplace.append(place.text)
        except BaseException as error:
            pass
        return birthplace

    @staticmethod
    def get_spouse(soup):
        td = soup.find('td', class_='female')
        if td:
            for br in td.find_all("br"):
                br.replace_with("\n")
            return td.text

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

    @staticmethod
    def get_trivia(soup):
        _trivias = []
        trivias = soup.find_all('li', class_="trivia")
        for trivia in trivias:
            _trivias.append(trivia.text)
        return _trivias

    @staticmethod
    def get_photos(src):
        parser = ImagePageParser(src)
        parser.cachedir = _cachedir
        parser.cachetime = _cachetime
        parser.start()
        return parser.full

    @staticmethod
    def get_roles(soup: BeautifulSoup):
        roles = {}
        tables = soup.find_all(class_="personPageItems")
        for table in tables:
            current_role = roles[table.attrs['data-work-type']] = []
            items = table.find_all("div", class_="item")
            for item in items:
                """
                :param item BeautifulSoup
                """
                re_year = re.compile(r'\((\d{4})\)')
                name = item.find("span", class_='name').a.text
                try:
                    year = int(re_year.search(name).groups()[0])
                except AttributeError:
                    year = None
                name = re_year.sub('', name)
                current_role.append({
                    'name': name,
                    'year': year,
                    'rating': item.attrs['data-imdbr'],
                    'role': item.find("span", class_='role').text,
                    'id': item.attrs['data-fid']
                })
        return roles

    @staticmethod
    def get_gender(soup: BeautifulSoup):
        meta = soup.find('meta', attrs={"itemprop": "gender"})
        if meta:
            return meta.attrs['content']

    def __str__(self):
        return "<Persons>"
