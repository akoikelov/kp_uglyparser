from typing import Union

from bs4 import BeautifulSoup, SoupStrainer
import htmlmin
import re
import logging
import dateparser
from ..utils.get_page import GetPage
from ..settings import LINK_TO_MAIN_PAGE


class TrailersPageParser(object):
    """
    Get trailers and another videos for the movie
    """

    def __init__(self, src: str, movie_id: Union[int, bool] = False):
        """
        Init instance of TrailersPageParser
        :param movie_id: id of movie
        :param src: Link to trailers page of film (Example: https://www.kinopoisk.ru/film/film_id/video/)
        """
        # Set defaults
        self.src = src
        self.trailers = []
        self.trailers_page = None
        self.trailers_soup = None
        self.trailers_blocks = []  # beutiul soups
        # start parsing
        self.parse()
        if movie_id:
            self.movie_id = movie_id
            self.get_main_trailer()

    def parse(self):
        reqex_between_comments = r"<!-- ролик -->([^≠]+?)<!-- /ролик -->"
        strainer = SoupStrainer("div", class_='block_left')
        self.trailers_page = GetPage(self.src, 'trailers_page')
        if self.trailers_page.content:
            self.trailers_soup = BeautifulSoup(self.trailers_page.content, 'lxml', parse_only=strainer)
            min_text = htmlmin.minify(self.trailers_soup.prettify(), remove_empty_space=True)
            trailer_blocks = re.findall(reqex_between_comments, min_text)[1:]
            for trailer_block in trailer_blocks:
                self.trailers_blocks.append(BeautifulSoup(trailer_block, 'lxml'))
            self.parse_trailers_blocks()
        else:
            logging.error("Cannot get trailers page; Status code: {0}".format(self.trailers_page.status_code))

    @property
    def full(self):
        return self.trailers

    def parse_trailers_blocks(self):
        """
        Walk on trailers blocks(three tr-elements between comments: <!-- ролик --> {trailer_block} <!-- /ролик -->  ).
        and parse from they trailers
        :return:
        """
        for trailer in self.trailers_blocks:
            title = trailer.find_all('a', class_='all', href=re.compile(r"/film/"))[0]
            # runtime
            runtime_tds = title.next_sibling.find_all("td")
            runtime = None
            if runtime_tds:
                runtime = runtime_tds[1].text if len(runtime_tds) > 2 else None
            # public_date
            public_date = None
            public_date = title.next_sibling.find_all("td")[-1]
            # noinspection PyUnusedLocal
            flag = (trailer.find_all('div', class_='flag') or None)
            links = TrailersPageParser.links_detect(trailer)
            poster = TrailersPageParser.get_preview(trailer)
            if poster:
                self.append_in_trailers(title.text, runtime, TrailersPageParser.get_mktime_from_str(public_date.text), links, poster)

    @staticmethod
    def get_preview(trailer_block):
        reg_ex_poster = re.compile(r"'previewFile'.+'(.+).jpg'")
        flat_text = htmlmin.minify(trailer_block.prettify())
        result = reg_ex_poster.findall(flat_text)
        if result and result[0]:
            return 'https://kp.cdn.yandex.net/' + result[0] + '.jpg'
        else:
            return False

    # UTILS FUNCS
    @staticmethod
    def links_detect(trailer_block):
        """
        Function of getting links in trailer_block
        :param trailer_block: Soup object of elements between comments (<!-- ролик --><tr><tr><tr><!-- /ролик -->)
        :return:
        """
        b_texts = trailer_block.find_all('b', text=re.compile(r"((.+) качество)"))  # array of b elements(instance of Soup)
        links = []
        for b in b_texts:
            link = b.parent
            links.append(TrailersPageParser.create_link_dict(TrailersPageParser.quality_detect(b.text),
                                                             TrailersPageParser.get_mp4_from_url(link.attrs['href'])))
        if len(links) == 0:
            a_texts = trailer_block.find_all('a', text=re.compile(r"((.+) качество)"))
            for a in a_texts:
                links.append(TrailersPageParser.create_link_dict(TrailersPageParser.quality_detect(a.text),
                                                                 TrailersPageParser.get_mp4_from_url(a.attrs['href'])))
        return links

    @staticmethod
    def create_link_dict(quality, url):
        return {
            'quality': quality,
            'url': url
        }

    @staticmethod
    def quality_detect(link_text):
        """
        Translate text of link in short form
        :param link_text: Text of link ("Высокое качество", "Низкое качество")
        :return:
        """
        low_regex = r'Низкое'
        middle_regex = r'Среднее'
        high_reg_ex = r'Высокое'
        if re.search(low_regex, link_text):
            return "low"
        if re.search(middle_regex, link_text):
            return "middle"
        if re.search(high_reg_ex, link_text):
            return "high"

    @staticmethod
    def get_mp4_from_url(url):
        """
        Get target link to mp4 from url of type:
        '/getlink.php?id=306903&type=trailer&link=https://file_link.mp4'
        :return: target link to mp4
        """
        link_regex = r"link=(https?://.+?.(mp4|flv|avi|mov|wmv))"
        mp4_link = re.search(link_regex, url)
        if mp4_link and mp4_link.group(1):
            return mp4_link.group(1)
        else:
            logging.error("Cannot get url to mp4 file in link: <<<{0}>>>".format(url))
            return None

    @staticmethod
    def get_mktime_from_str(public_date: str) -> int:
        """
        Transform " – 20 april 2015" to Unix time
        :param public_date:
        :return:
        """
        date = dateparser.parse(public_date, date_formats=[' – %d %B %Y'])
        if date:
            return int(date.timestamp())
        else:
            logging.error("Cannot get timestamp from date: {0}".format(public_date))
            return None

    def append_in_trailers(self, title: str, runtime: str, public_date, links: list, poster: str):
        """Add trailer in list
        :param title:
        :param runtime:
        :param public_date:
        :param links:
        :param poster:
        """
        self.trailers.append({
            'title': title,
            'runtime': runtime,
            'public_date': public_date,
            'links': links,
            'poster': poster
        })

    def get_language(self):
        pass

    def get_main_trailer(self):
        page = GetPage(LINK_TO_MAIN_PAGE.format(self.movie_id), 'main_kinopoisk')  # type: GetPage
        if page.status_code == 200 and page.content:
            soup = BeautifulSoup(page.content, 'lxml')  # type: BeautifulSoup
            if soup:
                trailer_block = soup.find("div", id=re.compile(r'trt\d+'))
                if trailer_block:
                    trailer_block = trailer_block.parent
                    script = trailer_block.script
                    if script:
                        script_text = script.text
                        trailer_file_regex = re.compile(r'\"trailerFile\":.+\"(.+\.(mp4|avi))\"')
                        trailer_preview_regex = re.compile(r'\"previewFile\":.+\"(.+\.jpg)\"')

                        trailer_file = None
                        trailer_preview = None

                        trailer_file_regex_groups = trailer_file_regex.search(script_text)
                        if trailer_file_regex_groups:
                            trailer_file = trailer_file_regex_groups.group(1)
                            if trailer_file:
                                trailer_file = "https://kp.cdn.yandex.net/" + trailer_file

                        trailer_preview_regex_groups = trailer_preview_regex.search(script_text)
                        if trailer_preview_regex_groups:
                            trailer_preview = trailer_preview_regex_groups.group(1)
                            if trailer_preview:
                                trailer_preview = "https://kp.cdn.yandex.net/" + trailer_preview
                        if trailer_file and trailer_preview:
                            self.append_in_trailers("Trailer", "0:0", 0,
                                                    [TrailersPageParser.create_link_dict("middle", trailer_file)],
                                                    trailer_preview)
