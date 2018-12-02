#!/usr/bin/env python3
"""Return list of items from a sub-reddit of reddit.com."""

import sys
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from json import JSONDecoder


def getitems(subreddit, previd=''):
    """Return list of items from a subreddit."""
    url = 'http://www.reddit.com/r/%s/new/.json' % subreddit
    # Get items after item with 'id' of previd.
    
#    hdr = { 'User-Agent' : 'RedditImageGrab script.' }
    hdr = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0 '}
    
    if previd:
        url = '%s?after=t3_%s' % (url, previd)
    try:
        req = Request(url, headers=hdr)
        json = urlopen(req).read().decode('utf-8')
#        data = json.decode("utf-8")
        data = JSONDecoder().decode(json)
        items = [x['data'] for x in data['data']['children']]
    except HTTPError as ERROR:
        error_message = '\tHTTP ERROR: Code %s for %s.' % (ERROR.code, url)
        sys.exit(error_message)
    except ValueError as ERROR:
        if ERROR.args[0] == 'No JSON object could be decoded':
            error_message = 'ERROR: subreddit "%s" does not exist' % subreddit
            sys.exit(error_message)
        raise ERROR
    return items

if __name__ == "__main__":

    print('Recent items for Python.')
    ITEMS = getitems('python')
    for ITEM in ITEMS:
        print('\t%s - %s' % (ITEM['title'], ITEM['url']))

    print('Previous items for Python.')
    OLDITEMS = getitems('python', ITEMS[-1]['id'])
    for ITEM in OLDITEMS:
        print('\t%s - %s' % (ITEM['title'], ITEM['url']))
