"""Example of how to use a GZIP middleware. Example usage:

curl -H 'Accept-Encoding: gzip' -D - -d foo=abc http://localhost:8001/; echo
"""

import paste.gzipper
from store import app

app = paste.gzipper.middleware(app)

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    print "Running on port 8001"
    make_server('', 8001, app).serve_forever()
