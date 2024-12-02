# AdultDVDEmpire.bundle

Plex metadata agent for fetching metadata from AdultDVDEmpire.

###  Disclaimer:

I'm not an expert in Python, or anything, really. Please forgive any shortcomings. All credit goes to the original developers. With thanks to: AndieUK, jesperrasmussen, macr0dev, adultplexdev and anyone else who has helped to keep this old plugin going over the years. 

### Info:

This version was originally from macr0dev (I think) but I have had to make small updates to it over the years to keep it working, mostly due to changes on the AE website. The most recent issue was the introduction of an age restriction screen which effectively blocks the script from parsing a search page until the button has been clicked. Fixed by passing ageConfirmed=true in the cookie. Also bundled urllib3 since urllib2 was no longer playing nice with the modern AE site, causing an SSL error. Since there is now no working version of this plugin available, I decided to share it with the three people still using it.

### Changelog:

**Update:** 02 Dec 2024  
**Description:** Removed unused random function. Fixed scraping of production year (was only scraping release date). Fixed the media format always returning as 'NA' despite pref setting. Refactored some code for efficiency and to remove possibility of using a couple of variables before assignment. Fixed a lot of indentation issues etc. Tagline was also no longer scraping.

**Update:** 19 Nov 2024  
**Description:** Summary2 would only scrape first p tag even if summary spanned multiple p tags. Now scrapes all and separates with a new line. Don't need to pass in full browser cookie, just append ageConfirmed=true. Also learned how to import libraries without adding to sys.path. Removed the config.py file because of these lessons and improvements.

**Update:** 14 Nov 2024  
**Description:** Bundled urllib3 and reworked code since urllib2 in the Python 2.7 environment Plex uses is too old for AE and causes an SSL error. Also now need to pass in cookie from browser in config.py to bypass age restricted page.

**Update:** 4 Aug 2023  
**Description:** Fixed missing summary due to AE site change and also fixed cast pulling into studio field.

**Update:** 23 June 2021  
**Description:** New updates from a lot of diffrent forks and people.

20210624  
Update to fix issues created by a Plex update.  
Adds:
Option to make the studio name a collection tag, off by default
