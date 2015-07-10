#-------------------------------------------------------------------------------
# Name:        gfycat uploader
# Purpose:
#
# Author:      Nimrod Goldrat
#
# URL:         https://github.com/nim901/gfycatuploader
# Licence:     MIT Licence
#-------------------------------------------------------------------------------

from collections import namedtuple

class gfycat(object):
    """
    A very simple module that allows you to
    1. upload a gif to gfycat
    2. query the upload url
    3. query an existing gfycat link
    4. query if a link is already exist
    """
    def __init__(self):
        super(gfycat, self).__init__()

    def __fetch(self,url, param):
        import urllib.request, urllib.error, urllib.parse, json
#        hdr2 = { 'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:28.0) Gecko/20100101 Firefox/28.0' }
        hdr2 = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:31.0) Gecko/20100101 Firefox/31.0'}
        req = urllib.request.Request((url+param), headers=hdr2)
        connection = urllib.request.urlopen(req).read()
        connection = connection.decode('utf-8')
        result = namedtuple("result", "raw json")
        return result(raw=connection, json=json.loads(connection))

    def upload(self, param):
        import random,string
        # gfycat needs to get a random string before our search parameter
        randomString = ''.join(random.choice
            (string.ascii_uppercase + string.digits) for _ in range(5))
        url="http://upload.gfycat.com"
        result = self.__fetch(url,
            "/transcode/%s?fetchUrl=%s" % (randomString, param))
        if "error" in result.json:
            raise ValueError("%s" % result.json["error"])
        return _gfycatUpload(result)

    def more(self, param):
        url="http://gfycat.com"
        result = self.__fetch(url, "/cajax/get/%s" % param)
        if "error" in result.json["gfyItem"]:
             raise ValueError("%s" % self.json["gfyItem"]["error"])
        return _gfycatMore(result)

    def album(self, param):
        url="http://gfycat.com"
        result = self.__fetch(url, "/cajax/getPublicAlbumContents?%s" % param)
        if "error" in result.json["title"]:
            raise ValueError("%s" % self.json["title"]["error"])
        return _gfycatAlbum(result)

    def check(self, param):
        url="http://gfycat.com"
        res = self.__fetch(url, "/cajax/checkUrl/%s" % param)
        if "error" in res.json:
            raise ValueError("%s" % self.json["error"])
        return _gfycatCheck(res)

class _gfycatUtils(object):
    """
    A utility class that provides the necessary common
    for all the other classes
    """
    def __init__(self, param, json):
        super(_gfycatUtils, self).__init__()
        # This can be used for other functions related to this class
        self.res = param
        self.js = json

    def raw(self):
        return self.res.raw

    def json(self):
        return self.js

    def get(self, what):
        try:
            return self.js[what]
        except KeyError as error:
            return ("Sorry, can't find %s" % error)

    def formated(self, ignoreNull=False):
            import json
            if not ignoreNull:
                return json.dumps(self.js, indent=4,
                    separators=(',', ': ')).strip('{}\n')
            else:
                raise NotImplementedError

class _gfycatUpload(_gfycatUtils):
    """
    The upload class, this will be used for uploading files
    from a remote server
    """
    def __init__(self, param):
        super(_gfycatUpload, self).__init__(param, param.json)

class _gfycatMore(_gfycatUtils):
    """
    This class will provide more information for an existing url
    """
    def __init__(self, param):
        super(_gfycatMore, self).__init__(param, param.json["gfyItem"])

class _gfycatAlbum(_gfycatUtils):
    """
    This class will provide more information for an existing album
    """
    def __init__(self, param):
        super(_gfycatAlbum, self).__init__(param, param.json["title"])

class _gfycatCheck(_gfycatUtils):
    """
    This call will allow to query if a link is already known
    """
    def __init__(self, param):
        super(_gfycatCheck, self).__init__(param, param.json)
