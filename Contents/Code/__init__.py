"""Agent for scraping AdultDVDEmpire"""

import re
import datetime
from lxml import html
import urllib3

# preferences
preference = Prefs
DEBUG = preference['debug']
if DEBUG:
    Log('Agent debug logging is enabled!')
else:
    Log('Agent debug logging is disabled!')

studioascollection = preference['studioascollection']

if len(preference['searchtype']) and preference['searchtype'] != 'all':
    searchtype = preference['searchtype']
else:
    searchtype = 'allsearch'
if DEBUG:Log('Search Type: %s' % str(preference['searchtype']))

# URLS
ADE_BASEURL = 'https://www.adultempire.com'
ADE_SEARCH_MOVIES = ADE_BASEURL + '/' + searchtype + '/search?view=list&q=%s'
ADE_MOVIE_INFO = ADE_BASEURL + '/%s/'

scoreprefs = int(preference['goodscore'].strip())
if scoreprefs > 1:
    GOOD_SCORE = scoreprefs
else:
    GOOD_SCORE = 98
if DEBUG:Log('Result Score: %i' % GOOD_SCORE)

INITIAL_SCORE = 100

titleFormats = r'\(DVD\)|\(Blu-Ray\)|\(BR\)|\(VOD\)'

def Start():
    pass

def ValidatePrefs():
    pass

# Create a PoolManager instance and set headers
http = urllib3.PoolManager()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Cookie': 'ageConfirmed=true',
}

class ADEAgent(Agent.Movies):
    name = 'Adult DVD Empire'
    languages = [Locale.Language.English]
    primary_provider = True
    accepts_from = ['com.plexapp.agents.localmedia']

    def search(self, results, media, lang):
        """Scrape AE site for metadata"""
        title = media.name
        if media.primary_metadata is not None:
            title = media.primary_metadata.title

        query = String.URLEncode(String.StripDiacritics(title.replace('-', '')))
        if DEBUG: Log('Search Query: %s' % str(ADE_SEARCH_MOVIES % query))
        url = ADE_SEARCH_MOVIES % query

        # resultarray[] is used to filter out duplicate search results
        resultarray = []

        try:
            # GET request using bundled urllib3
            response = http.request('GET', url, headers=headers)
            if DEBUG: Log('Response Status: %d' % response.status)

            if response.status == 200:
                # Parse the HTML content using lxml
                tree = html.fromstring(response.data.decode('utf-8'))
                # if DEBUG: Log('Raw Response Data: %s' % response.data.decode('utf-8')[:3500])

                movie_elements = tree.xpath('//div[contains(@class,"row list-view-item")]')
                if DEBUG: Log('Found %d movie elements' % len(movie_elements))

                # Finds the entire media enclosure <DIV> elements and steps through them
                for movie in tree.xpath('//div[contains(@class,"row list-view-item")]'):
                    try:
                        moviehref = movie.xpath('.//a[contains(@label,"Title")]')[0]
                        curName = moviehref.text_content().strip()
                        if DEBUG: Log('Initial Result Name found: %s' % str(curName))
                        if curName.count(', The'):
                            curName = 'The ' + curName.replace(', The', '', 1)
                        yearName = curName
                        relName = curName

                        # curID = the ID portion of the href in 'movie'
                        curID = moviehref.get('href').split('/', 2)[1]
                        score = INITIAL_SCORE - Util.LevenshteinDistance(title.lower(), curName.lower())
                        if DEBUG: Log('Score calculated: %s' % str(score))

                        # Get the release date (if available)
                        try:
                            moviedate = movie.xpath('.//small[contains(text(),"released")]/following-sibling::text()[1]')[0].strip()
                            if len(moviedate) > 0:
                                moviedate = datetime.datetime.strptime(moviedate, "%m/%d/%Y").strftime("%Y-%m-%d")
                                yearName = curName
                                relName += " [" + moviedate + "]"
                                if DEBUG: Log('Release date found: %s' % str(moviedate))
                        except Exception as e:
                            if DEBUG: Log('Error getting release date: %s' % str(e))

                        # Parse out the Production Year
                        try:
                            curYear = movie.xpath('//div[contains(@class, "list-view-item-info__title")]/a/following-sibling::text()')[0].strip()
                            if len(curYear):
                                if not re.match(r"\(\d\d\d\d\)", curYear):
                                    curYear = None
                                else:
                                    yearName += " " + curYear
                                if DEBUG: Log('Production Year found: %s' % str(curYear))
                        except Exception as e:
                            if DEBUG: Log('Error getting production year: %s' % str(e))

                        # Determine the media format (DVD, Blu-ray, etc.)
                        if preference['searchtype'] == 'all':
                            # List of media formats to check for
                            formats = {
                                "DVD-Video": "dvd",
                                "Blu-ray": "br",
                                "Video On Demand": "vod"
                            }
                            # Loop through formats to check and assign
                            for format_name, format_code in formats.items():
                                movie2 = movie.xpath('.//div[contains(@class, "list-view-item-controls_content-type") and contains(text(), "%s")]' % format_name)
                                if len(movie2) > 0:
                                    mediaformat = format_code
                                    if DEBUG: Log('%s format detected' % format_name)
                        else:
                            mediaformat = 'NA'
                        if DEBUG: Log('Media format: %s' % str(mediaformat))

                        # Build up the result array
                        resultrow = yearName + "<DIVIDER>" + curID + "<DIVIDER>" + mediaformat + "<DIVIDER>" + str(score) + "<DIVIDER>" + relName
                        if DEBUG:
                            Log('Result to process for appending: %s' % str(resultrow))

                        if preference['searchtype'] == 'all':
                            resulttemparray = []
                            resultpointer = None
                            for resulttempentry in resultarray:
                                resultname, resultid, resultformat, resultscore, resultrelname = resulttempentry.split("<DIVIDER>")
                                # Check if we have a better result based on format and year
                                if (((mediaformat == 'vod' and (resultformat == 'dvd' or resultformat == 'br')) or
                                    (mediaformat == 'br' and resultformat == 'dvd')) and resultname == yearName):
                                    resultpointer = 1  # Indicate we have a better result, don't write
                                # Only append the result if the current entry doesn't match the better condition
                                if not (((resultformat == 'vod' and (mediaformat == 'dvd' or mediaformat == 'br')) or
                                        (resultformat == 'br' and mediaformat == 'dvd')) and resultname == yearName):
                                    resulttemparray.append(resulttempentry)
                            # Update the result array with the new filtered list
                            resultarray = resulttemparray
                            # If resultpointer is None (i.e., no better result found), add the resultrow
                            if resultpointer is None:
                                resultarray.append(resultrow)

                    except Exception as e:
                        if DEBUG: Log('Error processing movie: %s (Year: %s)' % (str(e), yearName))

                # Step through the returned result array and append results
                for entry in resultarray:
                    entryYearName, entryID, entryFormat, entryScore, entryRelName = entry.split("<DIVIDER>")
                    if preference['dateformat']:
                        moviename = entryYearName
                        if (not re.search('\(\d{4}\)', entryYearName)) and (re.search('\[\d{4}-\d{2}-\d{2}\]', entryRelName)):
                            moviename = entryRelName
                            if DEBUG: Log('No Production Year Found, ReleaseDate Movie returned: %s' % str(moviename))
                        else:
                            if DEBUG: Log('Prod Year Movie returned: %s' % str(moviename))
                    else:
                        moviename = entryRelName
                        if (re.search('\(\d{4}\)', entryYearName)) and (not re.search('\[\d{4}-\d{2}-\d{2}\]', entryRelName)):
                            moviename = entryYearName
                            if DEBUG: Log('No Release Date Found, Year Movie returned: %s' % str(moviename))
                        else:
                            if DEBUG: Log('ReleaseDate Movie returned: %s' % str(moviename))

                    entryScore = int(entryScore)
                    if moviename.lower().count(title.lower()):
                        results.Append(MetadataSearchResult(id=entryID, name=moviename, score=entryScore, lang=lang))
                    elif entryScore >= GOOD_SCORE:
                        results.Append(MetadataSearchResult(id=entryID, name=moviename, score=entryScore, lang=lang))

                results.Sort('score', descending=True)
            else:
                if DEBUG: Log('Failed to retrieve data from URL: %s with status code %d' % (url, response.status))

        except Exception as e:
            if DEBUG: Log('Failed to retrieve data from URL: %s due to error: %s' % (url, str(e)))

    def update(self, metadata, media, lang):
        """Update Plex metadata"""
        if DEBUG: Log('Beginning Update...')

        # Using urllib3 to get HTML content
        response = http.request('GET', ADE_MOVIE_INFO % metadata.id, headers=headers)
        html_content = response.data.decode('utf-8')
        tree = html.fromstring(html_content)
        metadata.title = media.title
        metadata.title = re.sub(r'\ \[\d{4}-\d{2}-\d{2}\]','',metadata.title).strip()
        metadata.title = re.sub(r'\ \(\d{4}\)','',metadata.title).strip()
        if DEBUG: Log('Title Metadata Key: [Movie Title]   Value: [%s]', metadata.title)

        # Thumb and Poster
        try:
            if DEBUG: Log('Looking for thumb and poster')
            img = tree.xpath('//*[@id="front-cover"]/img')[0]
            thumbUrl = img.get('src')
            thumb_response = http.request('GET', thumbUrl, headers=headers)
            posterUrl = img.get('src')
            metadata.posters[posterUrl] = Proxy.Preview(thumb_response.data)
        except Exception as e:
            Log('Exception while fetching thumb/poster: %s' % str(e))

        # Tagline
        try:
            metadata.tagline = tree.xpath('//div[@class="row breakout bg-lightgrey"]//h2/text()')[0].strip()
            if DEBUG: Log('Tagline Found: %s' % str( metadata.tagline))
        except Exception as e:
            Log('Tagline not found: %s' % str(e))

        # Summary old style
        try:
            summary = tree.xpath('//div[@class="col-xs-12 text-center p-y-2 bg-lightgrey"]/div/p')[0].text_content().strip()
            summary = re.sub('<[^<]+?>', '', summary)
            if DEBUG: Log('Summary Found: %s' % str(summary))
            metadata.summary = summary
        except Exception as e:
            Log('Old style summary not found: %s' % str(e))

        # Summary new style
        try:
            paragraphs = tree.xpath('//div[@class="synopsis-content"]/p')
            summary2 = "\n".join(p.text_content().strip() for p in paragraphs)
            summary2 = re.sub('<[^<]+?>', '', summary2)
            # Update metadata.summary only if summary2 has a value
            if summary2:  # Checks if summary2 has a value
                if DEBUG: Log('New style summary found: %s' % str(summary2))
                metadata.summary = summary2
            else:
                Log('New style summary not found')
        except Exception as e:
            Log('Exception while parsing summary: %s' % str(e))

        # Studio
        try:
            studio = tree.xpath('//div[@class="movie-page__heading__movie-info item-info"]/a')[0].text_content().strip()
            studio = re.sub('<[^<]+?>', '', studio)
            metadata.studio = studio
            if DEBUG: Log('Studio Found: %s' % str(studio))
        except Exception as e:
            Log('Exception while parsing studio: %s' % str(e))

        # Product info div
        data = {}

        # Match different code blocks for product info
        if DEBUG: Log('Detecting Product info...')
        xpaths = [
            '//*[@id="content"]/div[2]/div[3]/div/div[1]/ul',
            '//*[@id="content"]/div[2]/div[4]/div/div[1]/ul',
            '//*[@id="content"]/div[2]/div[2]/div/div[1]/ul',
            '//*[@id="content"]/div[3]/div[3]/div/div[1]/ul',
            '//*[@id="content"]/div[3]/div[4]/div/div[1]/ul',
            '//ul[@class="list-unstyled m-b-2"]/li'
        ]
        for path in xpaths:
            productinfo_elements = tree.xpath(path)
            if productinfo_elements:
                productinfo = html.tostring(productinfo_elements[0], encoding='utf-8').decode('utf-8')
                break

        if productinfo:
            productinfo = productinfo.replace('<small>', '|')
            productinfo = productinfo.replace('</small>', '')
            productinfo = productinfo.replace('<li>', '').replace('</li>', '')
            productinfo = productinfo.replace('Features', '|')
            productinfo = html.fromstring(productinfo).text_content()

            for div in productinfo.split('|'):
                if ':' in div:
                    name, value = div.split(':')
                    data[name.strip()] = value.strip()
                    if DEBUG: Log('Title Metadata Key: [%s]   Value: [%s]', name.strip(), value.strip())
                    if name.strip() == "Studio": break

        if DEBUG: Log('Parsing of product info complete...')

        # Rating
        if 'Rating' in data:
            if DEBUG: Log('Rating Present...')
            metadata.content_rating = data['Rating']

        # Release Date
        if 'Released' in data:
            if DEBUG: Log('Release Date Present...')
            try:
                metadata.originally_available_at = Datetime.ParseDate(data['Released']).date()
                metadata.year = metadata.originally_available_at.year
            except Exception as e:
                Log('Exception while parsing release date: %s' % str(e))

        # Production Year
        if preference['useproductiondate']:
            if 'Production Year' in data:
                productionyear = int(data['Production Year'])
                if productionyear > 1900:
                    if DEBUG: Log('Release Date Year for Title: %i' % metadata.year)
                    if DEBUG: Log('Production Year for Title: %i' % productionyear)
                    if (metadata.year > 1900) and ((metadata.year - productionyear) > 1):
                        metadata.year = productionyear
                        metadata.originally_available_at = Datetime.ParseDate(str(productionyear) + "-01-01")
                        if DEBUG: Log('Production Year earlier than release, setting date to: %s' % (str(productionyear) + "-01-01"))

        # Cast
        try:
            metadata.roles.clear()
            if tree.xpath('//div[@class="hover-popover-detail"]'):
                htmlcast = tree.xpath('//div[@class="hover-popover-detail"]/img')
                upperlist = []
                for htmlcastUpper in htmlcast:
                    uppername = htmlcastUpper.xpath('./@title')[0]
                    upperurl = htmlcastUpper.xpath('./@src')[0]
                    upperurl = upperurl.replace("h.jpg", ".jpg")
                    if DEBUG: Log('Upper Star Data: %s     %s' % (uppername, upperurl))
                    upperlist.append(uppername)
                    role = metadata.roles.new()
                    role.name = uppername
                    role.photo = upperurl

                # Bottom List
                if tree.xpath('//a[contains(@class,"PerformerName")][not(ancestor::small)]'):
                    htmlcastLower = tree.xpath('//a[contains(@class,"PerformerName")][not(ancestor::small)]')
                    lowerlist = []
                    for removedupestar in htmlcastLower:
                        lowername = removedupestar.xpath('./text()')[0]
                        lowerurl = removedupestar.xpath('./@href')[0]
                        lowerurlre = re.search('\d{3,8}', lowerurl)
                        lowerentry = lowername.strip() + '|' + lowerurlre.group(0).strip()
                        lowerlist.append(lowerentry)
                    lowerlist = list(set(lowerlist))
                    for lowerstar in lowerlist:
                        if len(lowerstar) > 0:
                            lowerstarname, lowerstarurl = lowerstar.split("|")
                            if (lowerstarname not in upperlist and lowerstarname.lower() != 'bio' and lowerstarname.lower() != 'interview'):
                                role = metadata.roles.new()
                                role.name = lowerstarname
                                if len(lowerstarurl) > 1:
                                    photourl = "https://imgs1cdn.adultempire.com/actors/" + lowerstarurl + ".jpg"
                                    role.photo = photourl
                                else:
                                    photourl = "Image Not Available"
                                if DEBUG: Log('Added Lower List Star: %s    URL: %s' % (lowerstarname, photourl))
        except Exception as e:
            Log('Exception while parsing cast: %s' % str(e))

        # Director
        try:
            metadata.directors.clear()
            if tree.xpath('//a[contains(@label, "Director - details")]'):
                if DEBUG: Log('Director Label Found...')
                htmldirector = tree.xpath('//a[contains(@label, "Director - details")]/text()')
                if len(htmldirector) > 0:
                    director = metadata.directors.new()
                    director.name = htmldirector[0]
        except Exception as e:
            Log('Exception while parsing director: %s' % str(e))

        # Collections and Series
        try:
            metadata.collections.clear()
            series_elements = tree.xpath('//a[contains(@label, "Series")]')
            if series_elements:
                # Extracting the text content directly and cleaning up unnecessary text
                full_series_text = series_elements[0].text_content().strip()
                series = full_series_text.split("Series")[0].strip()
                series = series.strip('"')
                metadata.collections.add(series)
                # Studio as collection
                if studioascollection:
                    metadata.collections.add(studio)
                if DEBUG: Log('Series Found: %s' % str(series))
        except Exception as e:
            Log('Exception while parsing collections: %s' % str(e))

        # Genres
        try:
            genrelist = []
            metadata.genres.clear()
            ignoregenres = [x.lower().strip() for x in preference['ignoregenres'].split('|')]
            if tree.xpath('//ul[@class="list-unstyled m-b-2"]//a[@label="Category"]'):
                genres = tree.xpath('//ul[@class="list-unstyled m-b-2"]//a[@label="Category"]/text()')
                for genre in genres:
                    genre = genre.strip()
                    genrelist.append(genre)
                    if not genre.lower().strip() in ignoregenres:
                        metadata.genres.add(genre)
                if DEBUG: Log('Found Genres: %s' % (' | '.join(genrelist)))
        except Exception as e:
            Log('Exception while parsing genres: %s' % str(e))
