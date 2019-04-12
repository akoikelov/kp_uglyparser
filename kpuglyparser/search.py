import random
import re

import requests
import json

from kpuglyparser.film import Film
from .utils.memoize import memoize_fs

PROXIES = ['http://3bNPxH5eI1:cODSo1CIei@91.243.61.152:24145',
           'http://Zw2nuO81I5:KwuAmOGBTS@37.139.59.237:17179',
           'http://YeE0q4MQ3Z:DQg1Xc5SCT@185.192.110.248:24902',
           'http://xJAVOqdUn8:tjIDWKTy5g@195.158.224.246:17778',
           'http://KUTejf6vDP:BHrOFhU6VC@185.66.12.105:25240',
           'http://WGlTsEvVhe:OipX8VLGAd@185.194.105.231:20335',
           ]


def _format_item(result_item):
    pass
    return {
        'id': result_item['entityId'] if 'entityId' in result_item else None,
        'nameru': result_item['title'] if 'title' in result_item else None,
        'nameen': result_item['originalTitle'] if 'originalTitle' in result_item else None,
        'rating': result_item['rating']['rate'] if 'rating' in result_item else None,
        'year': result_item['years'][0] if 'years' in result_item and len(result_item['years']) > 0 else None
    }


def search_movie(q, cachedir=False, cachetime=3600 * 24):
    """
    find movie on kinopoisk.ru
    :param cachetime: 
    :param cachedir: 
    :param q:
    :return:
    """

    # @memoize_fs(cachedir, "search_movie", cachetime)
    def search(q):
        resp = requests.get(
            'https://suggest-kinopoisk.yandex.net/suggest-kinopoisk?srv=kinopoisk&part={search}'.format(search=q),
            proxies={
                'http': random.choice(PROXIES)
            })
        if resp.status_code == 200:
            _json = json.loads(resp.text)
            items = []
            for item in _json[2]:
                one_item = json.loads(item)
                if one_item['searchObjectType'] != 'PERSON':
                    items.append(one_item)
            return list(map(_format_item, items))
        else:
            return []

    matches = re.findall('([0-9]+)/$', q)

    if len(matches) > 0:
        movie = Film(matches[0], cachedir=cachedir, cachetime=cachetime)
        movie.get_content('main_page')

        data = movie.full

        return [
            {
                'id': data['id'],
                'nameru': data['main_page']['nameru'],
                'nameen': data['main_page']['nameen'],
                'rating': data['main_page']['rating'],
                'year': data['main_page']['year'],
            }
        ]
    else:
        return search(q)
