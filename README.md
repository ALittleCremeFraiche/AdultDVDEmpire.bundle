# AdultDVDEmpire.bundle

Plex metadata agent for fetching metadata from AdultDVDEmpire.

## Setup:

The config.py file is located in: Plex Media Server\Plug-ins\AdultDVDEmpire.bundle\Contents\Code and the values must be set before the plugin will work:

**PMS_DATA_LOCATION** = the location of your Plex Media Server appdata folder (by default on Windows: C:\Users\<username>\AppData\Local)  
**COOKIE_VALUE** = you will need to open the AE website in your browser, then with the Network tab of developer tools open, click the "Enter" button to pass the 'Over 18' screen. You can then copy the cookie from the request headers. Everything between etoken= and ; ageConfirmed=true is what you need. 

**Example config.py file:**

**COOKIE_VALUE=**"a1=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890&a2=1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef&a3=98765432109876"  
**PMS_DATA_LOCATION=**"C:\Users\<username>\AppData\Local" + "\Plex Media Server\Plug-ins\AdultDVDEmpire.bundle\Contents\Libraries\Shared"

###  Disclaimer:

I'm not an expert in Python, or anything, really. Please forgive any shortcomings. All credit goes to the original developers. With thanks to: AndieUK, jesperrasmussen, macr0dev, adultplexdev and anyone else who has helped to keep this old plugin going over the years. 

### Info:

This version was originally from macr0dev (I think) but I have had to make small updates to it over the years to keep it working, mostly due to changes on the AE website. The most recent issue was the toughest - the introduction of an age restriction screen which effectively blocks the script from parsing a search page until the button has been clicked. Since I couldn't come up with a way to deal with the button without something like Selenium, we have to use a cookie from a browser where the button has already been clicked. This cookie will likely need to be updated regularly whenever it expires.  
The other issue is that the old Python 2.7 environment which Plex uses only includes urllib2 which is now too old to talk to the modern AE website, so urllib3 has been bundled with the plugin. This is not ideal, but we're working with an outdated and limited Python environment within Plex. Since there is now no working version of this plugin available, I decided to share it with the three people still using it.

### Changelog:

Update: 14 Nov 2024  
Description: Bundled urllib3 and reworked code since urllib2 in the Python 2.7 environment Plex uses is too old for AE and causes an SSL error. Also now need to pass in cookie from browser in config.py to bypass age restricted page.

Update: 4 Aug 2023  
Description: Fixed missing summary due to AE site change and also fixed cast pulling into studio field.

Update: 23 June 2021  
Description: New updates from a lot of diffrent forks and people.

20210624  
Update to fix issues created by a Plex update.  
Adds:
Option to make the studio name a collection tag, off by default
