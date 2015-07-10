# MIT license
# Created by Steven Smith (blha303) 2013

# r5: Return url if upload(blah, geturl=True)
# r4: Turns out I don't need cookielib.
# r3: Remove unneeded base64 import
# r2: Fixed file upload support, added __name__ == "__main__" section for easy testing or usage from other languages (?)
# r1: Initial. all functionality in place

import urllib.request, urllib.error, urllib.parse, urllib.request, urllib.parse, urllib.error
import json

BASE_URL = "https://imgrush.com/"
API_URL = BASE_URL + "api/"


def info(hash):
    """
       Returns dict:
       * compression: float representing amount of compression achieved
       * files: list containing dicts:
         * file: string, url of file
         * type: string, mime type of file. can be "video/mp4", "video/ogg", "image/gif"
       * original: string, url of original file
       * type: string, mime type of original file
    """
    return json.loads(urllib.request.urlopen(API_URL + hash).read().decode())

def info_list(hashlist):
    """
        Returns dict:
        * <hash>: dict of info, or None if hash isn't valid. see info() docs
    """
    return json.loads(urllib.request.urlopen(API_URL + "info?list=" + ",".join(hashlist)).read())

def exists(hash):
    """
        Returns boolean
    """
    return json.loads(urllib.request.urlopen(API_URL + hash + "/exists").read())["exists"]

def delete(hash):
    """
        Returns dict:
        Either
        * status: string, always "success", meaning: The IP matches the stored hash and the file was deleted.
        or
        * error: integer, error code.
          401 = The IP does not match the stored hash.
          404 = There is no file with that hash.
    """
    try:
        return json.loads(urllib.request.urlopen(API_URL + hash + "/delete").read())["status"]
    except urllib.error.HTTPError as e:
        return json.loads(e.read())

def status(hash):
    """
        Returns dict:
        Either
        * status: string, one of four values:
            "done": The file has been processed.
            "processing": The file is being processed or in the processing queue.
            "error": The processing step finished early with an abnormal return code.
            "timeout": The file took too long to process.
        or
        * error: integer, error code.
          404 = There is no file with that hash.
    """
    try:
        return json.loads(urllib.request.urlopen(API_URL + hash + "/status").read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())

def upload(address, url=True, geturl=False):
    """
        Returns dict:
        Either
        * hash: string, resulting image hash
        or
        * error: integer, error code
          409 = The file was already uploaded.
          420 = The rate limit was exceeded. Enhance your calm.
          415 = The file extension is not acceptable.
        * hash: string, resulting image hash, if error code is 409
    """
    if url:
        try:
            data = json.loads(urllib.request.urlopen(API_URL + "upload/url", urllib.parse.urlencode({'url': address})).read())
            if geturl:
                return BASE_URL + data["hash"]
            else:
                return data
        except urllib.error.HTTPError as e:
            return json.loads(e.read())
    else:
        import MultipartPostHandler
        opener = urllib.request.build_opener(MultipartPostHandler.MultipartPostHandler)
        try:
            data = json.loads(opener.open(API_URL + "upload/file", {'file': open(address, "rb")}).read())
            if geturl:
                return BASE_URL + data["hash"]
            else:
                return data
        except urllib.error.HTTPError as e:
            return json.loads(e.read())

if __name__ == "__main__":
    from sys import argv
    if len(argv) > 2:
        if argv[1] == "uploadf" or argv[1] == "upload":
            print(upload(argv[2], url=False))
        elif argv[1] == "uploadu" or argv[1] == "url":
            print(upload(argv[2]))
        elif argv[1] == "info":
            print(info(argv[2]))
        elif argv[1] == "infol":
            print(info_list(argv[2].split(",")))
        elif argv[1] == "exists":
            print(exists(argv[2]))
        elif argv[1] == "delete":
            print(delete(argv[2]))
        elif argv[1] == "status":
            print(status(argv[2]))
        else:
            print("Unsupported function.")
    else:
        print("Usage: %s <function> <value>" % argv[0])
        print("Functions:")
        print("upload: filename   uploadf: filename   uploadu: url")
        print("url: url           info: hash          infol: comma-separated hash list")
        print("exists: hash       delete: hash        status: hash")
        print("by Steven Smith (blha303) 2013")
        print("MIT license")
        print("Support: https://gist.github.com/blha303/6239248 or mcrush@blha303.com.au")
