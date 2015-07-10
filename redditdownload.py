#!/usr/bin/env python2
"""Download images from a reddit.com subreddit."""

import re
import StringIO
import logging
import time
import urllib
import string
from urllib2 import urlopen, HTTPError, URLError
from httplib import InvalidURL
from argparse import ArgumentParser
from os.path import exists as pathexists, join as pathjoin, basename as pathbasename, splitext as pathsplitext, split as pathsplit
from os import mkdir
from reddit import getitems
from HTMLParser import HTMLParser
from gfycatupdloader import gfycat
import imgrush

# Used to extract src from Deviantart URLs
class DeviantHTMLParser(HTMLParser):
    """
    Parses the DeviantArt Web page in search for a link to the main image on page

    Attributes:
        IMAGE  - Direct link to image
    """

    def __init__(self):
        HTMLParser.__init__(self)
        self.reset()
        self.IMAGE = None
    # Handles HTML Elements eg <img src="//blank.jpg" class="picture"/> ->
    #      tag => "img", attrs => [("src", "//blank.jpg"), ("class", "picture")]
    def handle_starttag(self, tag, attrs):
        # Only interested in img when we dont have the url
        if (tag == "a" or tag == "img") and self.IMAGE is None:
            # Check attributes for class
            for classAttr in attrs:
                # Check class is dev-content-normal
                if classAttr[0] == "class":
                    # Incase page doesnt have a download button
                    if classAttr[1] == "dev-content-normal":
                        for srcAttr in attrs:
                            if srcAttr[0] == "src":
                                self.IMAGE = srcAttr[1]
                    else:
                        return


class WrongFileTypeException(Exception):
    """Exception raised when incorrect content-type discovered"""


class FileExistsException(Exception):
    """Exception raised when file exists in specified directory"""


def extract_imgur_album_urls(album_url):
    """
    Given an imgur album URL, attempt to extract the images within that
    album

    Returns:
        List of qualified imgur URLs
    """
    album_url = urllib.unquote(album_url).decode('utf8')
    response = urlopen(album_url)
    info = response.info()

    # Rudimentary check to ensure the URL actually specifies an HTML file
    if 'content-type' in info and not info['content-type'].startswith('text/html'):
        return []

    filedata = response.read()
    match = re.compile(r'\"hash\":\"(.[^\"]*)\"')
    items = []
    memfile = StringIO.StringIO(filedata)

    for line in memfile.readlines():
        results = re.findall(match, line)
        if not results:
            continue

        items = results

    memfile.close()

    urls = ['http://i.imgur.com/%s.jpg' % imghash for imghash in items]

    return urls


def extract_gfycat_album_urls(album_url):
    """
    Given a gfycat album URL, attempt to extract the gfys within that
    album

    :rtype : object
    Returns:
        List of qualified gfycat URLs
    """
    items = []
    p = re.compile('^(?:https?:\/\/[\da-z\.-]+\.[a-z\.]{2,6})\/([\w \.-]*)\/([\/\w \.-]*)')
    m = p.match(album_url)
    if m != None:
        user = m.group(1)
        album = m.group(2)
        astring = 'username='+user+'&albumUrl='+album

        gfy = gfycat().album(astring)
        gfyurl = gfy.res[1].values()

        for i in range(0,gfyurl[0].__len__()):
            gfyurls = gfyurl[0][i]
            items += [gfyurls["webmUrl"]]
            urls = items

    return urls


def download_from_url(url, dest_file):
    """
    Attempt to download file specified by url to 'dest_file'

    Raises:
        WrongFileTypeException

            when content-type is not in the supported types or cannot
            be derived from the URL

        FileExceptionsException

            If the filename (derived from the URL) already exists in
            the destination directory.
    """
    # Don't download files multiple times!
    if pathexists(dest_file):
        raise FileExistsException('URL [%s] already downloaded.' % url)

    url = urllib.unquote(url).encode('utf8')
    response = urlopen(url)
    info = response.info()
    # self.response.headers['Location'] = urllib.quote(absolute_url.encode("utf-8"))

    # Work out file type either from the response or the url.
    if 'content-type' in info.keys():
        filetype = info['content-type']
    elif url.endswith('.jpg') or url.endswith('.jpeg'):
        filetype = 'image/jpeg'
    elif url.endswith('.png'):
        filetype = 'image/png'
    elif url.endswith('.gif'):
        filetype = 'image/gif'
    elif url.endswith('.webm'):
        filetype = 'video/webm'
    elif url.endswith('.mp4'):
        filetype = 'video/mp4'
    elif url.endswith('.gifv'):
        filetype = 'video/webm'
    else:
        filetype = 'unknown'

    # Fix broken filetype descriptors on minus.com
    if ITEM['domain'] == 'i.minus.com' and filetype == 'image%2Fgif; charset=ISO-8859-1':
        filetype = 'image/gif'
    elif ITEM['domain'] == 'i.minus.com' and filetype == 'image%2Fjpeg; charset=ISO-8859-1':
        filetype = 'image/jpeg'
    elif ITEM['domain'] == 'imgrush.com' and filetype == 'text/html; charset=utf-8':
        filetype = 'video'
    elif 'imgur.com' in ITEM['domain'] and filetype == 'text/html; charset=utf-8':
	filetype = 'video/webm'

    # Only try to download acceptable image types
    if not filetype in ['image/jpeg', 'image/png', 'image/gif', 'image%2Fgif', 'image%2Fjpeg', 'video/webm', 'video/mp4', 'video', 'video/gifv']:
        raise WrongFileTypeException('WRONG FILE TYPE: %s has type: %s!' % (url, filetype))

#    if ITEM['domain'] == 'youtu.be' or ITEM['domain'] == 'youtube.com':
#        try:
#		subprocess.check_output(["youtube-dl",'-o',dest_file,url])
#        except subprocess.CalledProcessError, e:
#            print e.output

    filedata = response.read()
    filehandle = open(dest_file, 'wb')
    filehandle.write(filedata)
    filehandle.close()


def process_imgur_url(url):
    """
    Given an imgur URL, determine if it's a direct link to an image or an
    album.  If the latter, attempt to determine all images within the album

    Returns:
        list of imgur URLs
    """
    if ('imgur.com/a/' or 'imgur.com/gallery/') in url:
        return extract_imgur_album_urls(url)

    # Change .png to .jpg for imgur urls.
    if url.endswith('.png'):
        url = url.replace('.png', '.jpg')
    elif url.endswith('%2Fgif'):
        url = url.replace('%2Fgif', '.gif')
    elif url.endswith('%2Fjpeg'):
        url = url.replace('%2Fjpeg', '.jpg')
    elif url.endswith('.gifv'):
	url = url.replace('.gifv', '.webm')
    else:
        # Extract the file extension
        ext = pathsplitext(pathbasename(url))[1]
        if not ext:
            # Append a default
            url += '.jpg'

    return [url]


def  process_deviant_url(url):
    """
    Given a DeviantArt URL, determine if it's a direct link to an image, or
    a standard DeviantArt Page. If the latter, attempt to acquire Direct link.

    Returns:
        deviantart image url
    """
    # We have it! Dont worry
    if url.endswith('.jpg'):
        return [url]
    else:
        # Get Page and parse for image link
        response = urlopen(url)
        filedata = response.read()
        parser = DeviantHTMLParser()
        try:
            parser.feed(filedata)
            if parser.IMAGE != None:
                return [parser.IMAGE]
            return [url]
        # Exceptions thrown when non-ascii chars are found
        except UnicodeDecodeError as ERROR:
            if parser.IMAGE != None:
                return [parser.IMAGE]
            else:
                return[url]
    # Dont return None!
#    return [url]

def process_gfycat_url(url):
    """
    Given a gfycat URL, determine if it's a direct link to a webm/gif.
    If not, attempt to determine the proper URL

    Returns:
        gfycat webm URL
    """
    p = re.compile('^(?:https?:\/\/[\da-z\.-]+\.[a-z\.]{2,6})\/([\w \.-]*)\/([\/\w \.-]*)')
    m = p.match(url)
    if m != None:
        return extract_gfycat_album_urls(url)
    elif 'gfycat.com' in url:
          tail = pathsplit(url)[1]
          query = gfycat().more(tail)
          url = query.get("webmUrl")
    return [url]

def process_imgrush_url(url):

#    Given a imgrush URL, parse the webm link and return it for downloading.

    if 'imgrush.com' in url:
        tail = pathsplit(url)[1]
        query = imgrush.info(tail)
        files = query['files'][0]
        url = files.get("url")
    return[url]


def extract_urls(url):
    """
    Given an URL checks to see if its an imgur.com URL, handles imgur hosted
    images if present as single image or image album.

    Returns:
        list of image urls.
    """
#    urls = []

    if 'imgur.com' in url:
        urls = process_imgur_url(url)
    elif 'deviantart.com' in url:
        urls = process_deviant_url(url)
    elif 'gfycat.com' in url:
        urls = process_gfycat_url(url)
    elif 'mediacru.sh' in url:
        url = url.replace('mediacru.sh','imgrush.com')
	urls = process_imgrush_url(url)
    elif 'imgrush.com' in url:
        urls = process_imgrush_url(url)
    else:
        urls = [url]

    return urls


if __name__ == "__main__":
    PARSER = ArgumentParser(description='Downloads files with specified extension from the specified subreddit.')
    PARSER.add_argument('reddit', metavar='<subreddit>', help='Subreddit name.')
    PARSER.add_argument('dir', metavar='<dest_file>', help='Dir to put downloaded files in.')
    PARSER.add_argument('-last', metavar='l', default='', required=False, help='ID of the last downloaded file.')
    PARSER.add_argument('-score', metavar='s', default=0, type=int, required=False, help='Minimum score of images to download.')
    PARSER.add_argument('-num', metavar='n', default=0, type=int, required=False, help='Number of images to download.')
    PARSER.add_argument('-update', default=False, action='store_true', required=False, help='Run until you encounter a file already downloaded.')
    PARSER.add_argument('-sfw', default=False, action='store_true', required=False, help='Download safe for work images only.')
    PARSER.add_argument('-nsfw', default=False, action='store_true', required=False, help='Download NSFW images only.')
    PARSER.add_argument('-regex', default=None, action='store', required=False, help='Use Python regex to filter based on title.')
    PARSER.add_argument('-verbose', default=False, action='store_true', required=False, help='Enable verbose output.')
    ARGS = PARSER.parse_args()

# Debug logging
    logger = logging.getLogger('red_up')
    logger.setLevel(logging.DEBUG)
    # create file handler and set level to debug
    if not pathexists('./logs'):
        mkdir('./logs')
    fh = logging.FileHandler('./logs/reddit_update.log')
    fh.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    # add formatter to ch and fh
    fh.setFormatter(formatter)
    #add ch and fh to logger
    logger.addHandler(fh)

    logger.debug('')
    print 'Downloading images from "%s" subreddit' % (ARGS.reddit)
    logger.debug('Downloading images from "%s" subreddit' % (ARGS.reddit))

    TOTAL = DOWNLOADED = ERRORS = SKIPPED = FAILED = 0
    FINISHED = False

    # Create the specified directory if it doesn't already exist.
    if not pathexists(ARGS.dir):
        mkdir(ARGS.dir)

    # If a regex has been specified, compile the rule (once)
    RE_RULE = None
    if ARGS.regex:
        RE_RULE = re.compile(ARGS.regex)

    LAST = ARGS.last

    while not FINISHED:
        ITEMS = getitems(ARGS.reddit, LAST)
        if not ITEMS:
            # No more items to process
            break

        for ITEM in ITEMS:
            TOTAL += 1
            IDENTIFIER = ITEM['title'].replace('/', '\'').replace('"', '\'').replace('*', '\'').replace(':', '-').replace('?', '\'').replace('|', '-').replace('\\', '\'').replace('>','\'').replace('<','\'').replace('\n','-').replace('\t','-')

            if ITEM['score'] < ARGS.score:
                if ARGS.verbose:
                    print '    SCORE: %s has score of %s which is lower than required score of %s.' % (ITEM['id'], ITEM['score'], ARGS.score)

                SKIPPED += 1
                continue
            elif ARGS.sfw and ITEM['over_18']:
                if ARGS.verbose:
                    print '    NSFW: %s is marked as NSFW.' % (ITEM['id'])

                SKIPPED += 1
                continue
            elif ARGS.nsfw and not ITEM['over_18']:
                if ARGS.verbose:
                    print '    Not NSFW, skipping %s' % (ITEM['id'])

                SKIPPED += 1
                continue
            elif ARGS.regex and not re.match(RE_RULE, ITEM['title']):
                if ARGS.verbose:
                    print '    Regex match failed'

                SKIPPED += 1
                continue

            FILECOUNT = 0
            try:
                URLS = extract_urls(ITEM['url'])
            except HTTPError as ERROR:
                print '    HTTP ERROR: Code %s. ID = %s.' % (ERROR.code, ITEM['id'])
                logger.debug('    HTTP ERROR: Code %s. ID = %s.' % (ERROR.code, ITEM['id']))
                FAILED+=1
            for URL in URLS:
                try:
                    # Trim any http query off end of file extension.
                    FILEEXT = pathsplitext(URL)[1]
                    if '?' in FILEEXT:
                        FILEEXT = FILEEXT[:FILEEXT.index('?')]

                    # Only append numbers if more than one file.
                    FILENUM = ('_%d' % FILECOUNT if len(URLS) > 1 else '')
                    FILENAME = '%s%s%s%s%s' % (ITEM['id'], ' - ', IDENTIFIER, FILENUM, FILEEXT)
                    FILEPATH = pathjoin(ARGS.dir, FILENAME)

#                    # Improve debuggability list URL before download too.
#                    print '    Attempting to download URL [%s] as [%s].' % (
#                        URL.encode('utf-8'), FILENAME.encode('utf-8'))

                    # Download the image
                    download_from_url(URL, FILEPATH)

                    # Image downloaded successfully!
                    print '    Downloaded URL [%s] as [%s].' % (URL, FILENAME)
                    logger.debug('    Downloaded URL [%s] as [%s].' % (URL, FILENAME))
                    DOWNLOADED += 1
                    FILECOUNT += 1
                    time.sleep(2)
                    if 0 < ARGS.num <= DOWNLOADED:
                        FINISHED = True
                        break
                except WrongFileTypeException as ERROR:
                    print '    %s' % (ERROR)
                    logger.debug('    %s' % (ERROR))
                    SKIPPED += 1
                except FileExistsException as ERROR:
                    print '    %s' % (ERROR)
                    logger.debug('    %s' % (ERROR))
                    ERRORS += 1
                    if ARGS.update:
                        print '    Update complete, exiting.'
                        logger.debug('    Update complete, exiting.')
                        FINISHED = True
                        break
                except HTTPError as ERROR:
                    print '    HTTP ERROR: Code %s for %s. ID = %s' % (ERROR.code, URL, ITEM['id'])
                    logger.debug('    HTTP ERROR: Code %s for %s. ID = %s' % (ERROR.code, URL, ITEM['id']))
                    FAILED += 1
                except URLError as ERROR:
                    print '    URL ERROR: %s!' % (URL)
                    logger.debug('    URL ERROR: %s!' % (URL))
                    FAILED += 1
                except InvalidURL as ERROR:
                    print '    Invalid URL: %s!' % (URL)
                    logger.debug('    Invalid URL: %s!' % (URL))
                    FAILED += 1

            if FINISHED:
                break

        LAST = ITEM['id']

    print 'Downloaded %d files (Processed %d, Skipped %d, Exists %d)' % (DOWNLOADED, TOTAL, SKIPPED, ERRORS)
    logger.debug('Downloaded %d files (Processed %d, Skipped %d, Exists %d)' % (DOWNLOADED, TOTAL, SKIPPED, ERRORS))
