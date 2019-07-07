from bs4 import BeautifulSoup, SoupStrainer, ResultSet
import re
import logging
import dateparser
import pydash
from ..utils.get_page import get_page, LinkGP

awards_list = [
    {
        "alias": "golden_globes",
        "nameru": "Золотой глобус",
        "nameen": "Golden Globe Award"
    },
    {
        "alias": "oscar",
        "nameru": "Оскар",
        "nameen": "Oscar"

    },
    {
        "alias": "mtv",
        "nameru": "Премия канала «MTV»",
        "nameen": "MTV Movie Awards"
    },
    {
        "alias": "bafta",
        "nameru": "Британская киноакадемия",
        "nameen": "The British Academy of Film and Television Arts"
    },
    {
        "alias": "saturn",
        "nameru": "Сатурн",
        "nameen": "Saturn"
    },
    {
        "alias": "sag",
        "nameru": "Премия Гильдии актеров",
        "nameen": "Screen Actors Guild Award"
    },
    {
        "alias": "efa",
        "nameru": "Европейская киноакадемия",
        "nameen": "European Film Academy"
    },
    {
        "alias": "nika",
        "nameru": "Ника",
        "nameen": "Nika Award"
    },
    {
        "alias": "mtv_russia",
        "nameru": "Кинонаграды «MTV-Россия»",
        "nameen": "MTV Russia Movie Awards"
    },
    {
        "alias": "sundance",
        "nameru": "Сандэнс",
        "nameen": " Sundance Film Festival"
    },
    {
        "alias": "georges",
        "nameru": "Жорж",
        "nameen": "Zhorzh"
    },
    {
        "alias": "emmy",
        "nameru": "Эмми",
        "nameen": "Emmy Award"
    },
    {
        "alias": "cesar",
        "nameru": "Сезар",
        "nameen": "César Award"
    },
    {
        "alias": "cannes",
        "nameru": "Каннский кинофестиваль",
        "nameen": "Cannes Film Festival"
    },
    {
        "alias": "venice",
        "nameru": "Венецианский кинофестиваль",
        "nameen": "Venice Film Festival"
    },
    {
        "alias": "goya",
        "nameru": "Гойя",
        "nameen": "Goya Awards"
    },
    {
        "alias": "asian",
        "nameru": "Азиатская киноакадемия",
        "nameen": "Asian Film Awards"
    },
    {
        "alias": "berlin",
        "nameru": "Берлинский кинофестиваль",
        "nameen": "Berlin International Film Festival"
    },
    {
        "alias": "miff",
        "nameru": "ММКФ",
        "nameen": "Moscow International Film Festival"
    },
    {
        "alias": "karlovy_vary",
        "nameru": "Карловы Вары",
        "nameen": "Karlovy Vary International Film Festival"
    },
    {
        "alias": "kinotavr",
        "nameru": "Кинотавр",
        "nameen": "Kinotavr"
    },
]


class MainPageParser():
    """
    Get page of movie
    """

    # noinspection PyShadowingBuiltins
    def __init__(self, src, id):
        self.film_id = id
        self.src = src
        self.page = None  # BeautifulSoup Object of main page
        self.info_table = None  # BeautifulSoup object of main info table on page
        self.poster_block = None  # BeautifulSoup object of div with poster of movie
        self.rating_block = None  # BeautifulSoup object of div with poster of movie
        # Set defaults
        self.nameru = None
        self.nameen = None
        self.description = None
        self.poster = None
        self.sequels = []
        self.trivia_facts = []
        self.recommendations = []

        self.year = None
        self.countries = []
        self.slogan = None
        self.genres = []
        self.budget = {
            'budget': None,
            'currency': None
        }
        self.boxoffice = {
            'USA': None,
            'RU': None,
            'WORLD': None
        }
        # premiere
        self.premiere_world = None
        self.premiere_russia = None
        self.premiere_DVD = None
        self.premiere_BluRay = None

        self.runtime = None
        self.rating = None
        self.ratingimdb = None
        self.awards = {}

        self.cachedir = None
        self.cachetime = None

    @property
    def full(self):
        return {
            'nameru': self.nameru,
            'nameen': self.nameen,
            'description': self.description,
            'poster': self.poster,
            'sequels': self.sequels,
            'recommendations': self.recommendations,
            'trivia_facts': self.trivia_facts,
            'year': self.year,
            'countries': self.countries,
            'slogan': self.slogan,
            'genres': self.genres,
            'budget': self.budget,
            'boxoffice': self.boxoffice,
            # premiere
            'premiere_world': self.premiere_world,
            'premiere_russia': self.premiere_russia,
            'premiere_DVD': self.premiere_DVD,
            'premiere_BluRay': self.premiere_BluRay,

            'runtime': self.runtime,
            'rating': self.rating,
            'ratingimdb': self.ratingimdb,
            'awards': self.awards
        }

    def start(self):
        # start parse
        self.parse()

    def parse(self):
        main_page_linkgp = get_page(LinkGP(self.src), cachedir=self.cachedir, cachetime=self.cachetime)

        if main_page_linkgp.content:
            strainer = SoupStrainer("div", id="content_block")
            self.page = BeautifulSoup(
                main_page_linkgp.content, 'lxml', parse_only=strainer)
            self.parse_by_steps()
        else:
            logging.error(
                "Cannot get page of film; Url: <<<{0}>>>".format(self.src))

    def parse_by_steps(self):
        self.get_names()

        # parse main table
        self.find_info_table()
        self.get_year()
        self.get_countries()
        self.get_slogan()
        self.get_genres()
        self.get_budget()
        self.get_boxoffice()
        self.get_premiere_world()
        self.get_premiere_russia()
        self.get_premiere_DVD()
        self.get_premiere_BluRay()
        self.get_runtime()

        self.get_description()
        # rating
        self.get_rating_block()
        self.get_rating()
        self.get_ratingimdb()
        # poster
        self.get_poster()
        # sequels
        self.get_sequels()
        # trivia
        self.get_trivia_data()
        # recommendations
        self.get_recommendations()
        # awards
        self.get_awards()

    def get_names(self):
        nameru = self.page.find('h1', class_='moviename-big')
        nameen = self.page.find(
            'span', attrs={'itemprop': 'alternativeHeadline'})
        if nameru:
            self.nameru = nameru.text
        if nameen:
            self.nameen = nameen.text

    # !===PARSE INFO TABLE===!
    def find_info_table(self):
        info_table = self.page.find('div', id='infoTable')
        if info_table:
            self.info_table = info_table

    def get_year(self):
        year_marker_td = self.info_table.find('td', text='год')
        if year_marker_td:
            year_tables_row = year_marker_td.parent
            year = year_tables_row.find('a').text
            if year:
                self.year = int(year)

    def get_countries(self):
        country_marker_td = self.info_table.find('td', text='страна')
        if country_marker_td:
            country_tables_row = country_marker_td.parent
            countries = [a.text for a in country_tables_row.find_all('a')]
            self.countries = countries

    def get_slogan(self):
        slogan_marker_td = self.info_table.find('td', text='слоган')
        if slogan_marker_td:
            slogan_tables_row = slogan_marker_td.parent
            slogan = slogan_tables_row.find_all('td')[1].text
            self.slogan = slogan

    def get_genres(self):
        genres_marker_td = self.info_table.find('td', text='жанр')
        if genres_marker_td:
            genres_table_row = genres_marker_td.parent
            genres_span = genres_table_row.find(
                'span', attrs={'itemprop': 'genre'})
            if genres_span:
                genres = [genre.text for genre in genres_span.find_all('a')]
                self.genres = genres

    def get_budget(self):
        budget_marker_td = self.info_table.find('td', text='бюджет')
        if budget_marker_td:

            budget_table_row = budget_marker_td.parent
            if 'en' in budget_table_row.attrs['class']:
                currency = 'USD'
            elif 'rubimpot' in budget_table_row.attrs['class']:
                currency = 'RUB'
            else:
                currency = 'undefined'

            budget_td = budget_table_row.find(
                class_=re.compile(r'(dollar|euro|pound|yen)'))
            # if currency is Euro
            if 'euro' in budget_td.attrs['class']:
                currency = 'EUR'
            elif 'pound' in budget_td.attrs['class']:
                currency = 'GBP'
            elif 'yen' in budget_td.attrs['class']:
                currency = 'JPY'

            budget = budget_td.find(string=re.compile(r'((\d+(?:\s|))+)'))
            self.budget['budget'] = int(
                ''.join(x for x in budget if x.isdigit()))
            self.budget['currency'] = currency

    def get_boxoffice(self):
        budget_marker_td = self.info_table.find('td', text='сборы в мире')
        if budget_marker_td:
            content_td = budget_marker_td.find_next_sibling('td')
            a = content_td.find('a')
            if a:
                self.boxoffice['WORLD'] = a.text
        budget_marker_td = self.info_table.find('td', text='сборы в России')
        if budget_marker_td:
            content_td = budget_marker_td.find_next_sibling('td')
            a = content_td.find('a')
            if a:
                self.boxoffice['RU'] = a.text
        budget_marker_td = self.info_table.find('td', text='сборы в США')
        if budget_marker_td:
            content_td = budget_marker_td.find_next_sibling('td')
            a = content_td.find('a')
            if a:
                self.boxoffice['USA'] = a.text

    def get_premiere_world(self):
        premiere_world_marker_td = self.info_table.find(
            'td', id='div_world_prem_td2')
        if premiere_world_marker_td:
            date = premiere_world_marker_td.find(
                string=re.compile(r'\d+\s.+\s\d\d\d\d'))
            if date:
                self.premiere_world = dateparser.parse(date).isoformat()

    def get_premiere_russia(self):
        premiere_russia_marker_td = self.info_table.find(
            'td', id='div_rus_prem_td2')
        if premiere_russia_marker_td:
            date = premiere_russia_marker_td.find(
                string=re.compile(r'\d+\s.+\s\d\d\d\d'))
            if date:
                self.premiere_russia = dateparser.parse(date).isoformat()

    # noinspection PyPep8Naming
    def get_premiere_DVD(self):
        premiere_DVD_marker_td = self.info_table.find(
            'td', class_='calendar dvd')
        if premiere_DVD_marker_td:
            date = premiere_DVD_marker_td.find(
                string=re.compile(r'\d+\s.+\s\d\d\d\d'))
            if date:
                parsed_date = dateparser.parse(date)

                if parsed_date:
                    self.premiere_DVD = parsed_date.isoformat()

    # noinspection PyPep8Naming
    def get_premiere_BluRay(self):
        premiere_BluRay_marker_td = self.info_table.find(
            'td', class_='calendar bluray')
        if premiere_BluRay_marker_td:
            date = premiere_BluRay_marker_td.find(
                string=re.compile(r'\d+\s.+\s\d\d\d\d'))
            if date:
                parsed_date = dateparser.parse(date)

                if parsed_date:
                    self.premiere_BluRay = parsed_date.isoformat()

    def get_runtime(self):
        runtime_marker_td = self.info_table.find('td', id='runtime')
        if runtime_marker_td:
            self.runtime = int(
                ''.join([x for x in runtime_marker_td.next if x.isdigit()]) or False) or None

    # !===PARSE DESCRIPTION===!
    def get_description(self):
        description_div = self.page.find(
            'div', class_='brand_words film-synopsys')
        if description_div:
            self.description = description_div.text

    # !===PARSE RATING===!
    def get_rating_block(self):
        self.rating_block = self.page.find('div', id='block_rating')

    def get_rating(self):
        if self.rating_block:
            rating_span = self.rating_block.find('span', class_='rating_ball')
            if rating_span:
                self.rating = float(rating_span.text)

    def get_ratingimdb(self):
        if self.rating_block:
            rating_imdb = re.compile(r'IMDb:\s(.+)\s(?:\(.+\))')
            ratingimdb_div = self.rating_block.find(string=rating_imdb)
            if ratingimdb_div:
                ratingimdb = re.findall(rating_imdb, ratingimdb_div)[0]
                if ratingimdb:
                    self.ratingimdb = float(ratingimdb)

    # !===PARSE POSTER===!
    def get_poster(self):
        poster_block = self.page.find('div', id='photoBlock')
        if poster_block:
            poster_a = poster_block.find('a', class_='popupBigImage')
            if poster_a and poster_a.attrs.get('onclick', False):
                poster_url = re.findall(
                    r'(/images/.+.jpg)', poster_a.attrs['onclick'])[0]
            else:
                poster_img = poster_block.find('img')
                poster_url = poster_img.attrs['src']
            self.poster = "https://www.kinopoisk.ru" + poster_url

    # !===PARSE SEQUELS===!
    def get_sequels(self):
        sequel_block = self.page.find('div', class_='sequel_scroller')
        if sequel_block:
            sequels = sequel_block.find_all('div', class_='scroll_photo')
            for sequel in sequels:
                sequel_en = sequel.find('b', class_='en')
                if sequel_en:
                    sequel_en = sequel_en.next
                sequel_link = sequel.find('a')
                if sequel_link:
                    if sequel_link.attrs['href'] != '#':
                        h = sequel_link.attrs['href'] # type: str
                        self.sequels.append({
                            'nameru': sequel_link.attrs['title'],
                            'nameen': sequel_en.text if sequel_en and getattr(sequel_en, 'text', False) else None,
                            'link': "https://kinopoisk.ru" + sequel_link.attrs['href'],
                            'id': int(''.join([x for x in h[h.rfind('-')+1:] if x.isdigit()]))
                        })

    def get_trivia_data(self):
        trivia_block = self.page.find("div", class_='triviaBlock')
        if trivia_block:
            trivia_list = trivia_block.find_all('li', class_='trivia')
            for trivia in trivia_list:
                self.trivia_facts.append(trivia.span.text)

    def get_recommendations(self):
        recommendations_page_linkgp = get_page(LinkGP(self.src + 'like/'), cachedir=self.cachedir, cachetime=self.cachetime)
        if recommendations_page_linkgp.content:
            strainer = SoupStrainer('div', class_='block_left_pad')
            recommendations_soup = BeautifulSoup(
                recommendations_page_linkgp.content, 'lxml', parse_only=strainer)
            if recommendations_soup:
                recommendations_trs = recommendations_soup.find_all(
                    'tr', class_='_NO_HIGHLIGHT_')
                if recommendations_trs:
                    for recommendation_tr in recommendations_trs:
                        film_link = recommendation_tr.find(
                            'a', class_=' b_gray i_orig')
                        if film_link:
                            h = film_link.attrs['href']
                            self.recommendations.append({
                                'id': int(''.join([c for c in h[h.rfind('-')+1:] if c.isdigit()])),
                                'poster': film_link.img.attrs['src'],
                                'nameru': film_link.img.attrs['alt']
                            })

    def get_awards(self):
        awards_page_linkgp = get_page(LinkGP(self.src + 'awards/'), cachedir=self.cachedir, cachetime=self.cachetime)

        strainer = SoupStrainer('div', class_='block_left')
        if awards_page_linkgp.content:
            awards_soup = BeautifulSoup(
                awards_page_linkgp.content, 'lxml', parse_only=strainer)  # type: BeautifulSoup
            link_list = awards_soup.find_all("li", class_="trivia")  # type: BeautifulSoup.ResultSet

            for link in link_list:
                if link.a and 'style' in link.a.attrs:
                    href = link.a.attrs['href']  # type: str

                    correct_award = pydash.find_where(awards_list, lambda x: x['alias'] in href)
                    if correct_award:
                        year = int(re.findall(r'\d{4}', href)[0])
                        award_key = correct_award['alias'] + str(year)
                        if award_key not in self.awards:
                            award_record = self.awards[award_key] = {
                                'alias': correct_award['alias'],
                                'nameru': correct_award['nameru'],
                                'nameen': correct_award['nameen'],
                                'year' : year,
                                'victory': []
                            }
                        else:
                            award_record = self.awards[award_key]
                        award_record['victory'].append(link.a.text)
                    else:
                        logging.warning("Undefined award: ${0}".format(link.a))
