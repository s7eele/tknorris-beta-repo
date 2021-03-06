"""
    SALTS XBMC Addon
    Copyright (C) 2014 tknorris

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import scraper
import urllib
import urlparse
import re
import xbmcaddon
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import QUALITIES

BASE_URL = 'http://film-streaming.in'

class FilmStreaming_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = xbmcaddon.Addon().getSetting('%s-base_url' % (self.get_name()))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.MOVIE])

    @classmethod
    def get_name(cls):
        return 'FilmStreaming.in'

    def resolve_link(self, link):
        if 'videomega' in link:
            html = self._http_get(link, cache_limit=.5)
            match = re.search('ref="([^"]+)', html)
            if match:
                return 'http://videomega.tv/iframe.php?ref=%s' % (match.group(1))
        else:
            return link

    def format_source_label(self, item):
        return '[%s] %s (%s views)' % (item['quality'], item['host'], item['views'])

    def get_sources(self, video):
        source_url = self.get_url(video)
        hosters = []
        if source_url:
            url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(url, cache_limit=.5)

            views = None
            match = re.search('class="sirala">([,\d]+) views', html, re.DOTALL)
            if match:
                views = match.group(1)
                views = views.replace(',', '')

            for match in re.finditer('class="tab_part".*?src=["\']([^\'"]+)', html, re.I):
                url = match.group(1)
                host = urlparse.urlparse(url).hostname
                if 'youtube' not in host:
                    hoster = {'multi-part': False, 'url': url, 'host': host, 'class': self, 'quality': QUALITIES.HIGH, 'views': views, 'rating': None, 'direct': False}
                    hosters.append(hoster)
        return hosters

    def get_url(self, video):
        return super(FilmStreaming_Scraper, self)._default_get_url(video)

    def search(self, video_type, title, year):
        search_url = urlparse.urljoin(self.base_url, '/?s=')
        search_url += urllib.quote_plus('%s %s' % (title, year))
        html = self._http_get(search_url, cache_limit=.25)
        results = []
        if not re.search('I am sorry, what are you looking for', html, re.I):
            pattern = 'FilmBaslik">.*?href="([^"]+)"\s+title="([^"]+)\s+\((\d{4})\)'
            for match in re.finditer(pattern, html, re.DOTALL):
                url, title, match_year = match.groups('')
                if not year or not match_year or year == match_year:
                    result = {'url': url.replace(self.base_url, ''), 'title': title, 'year': match_year}
                    results.append(result)
        return results

    def _http_get(self, url, cache_limit=8):
        return super(FilmStreaming_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, cache_limit=cache_limit)
