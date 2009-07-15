"""The store service is a simple document store. It stores key/value pairs on
the documents. This is currently a dummy implementation with ony in-memory
storage.
"""

import uuid
from wsgiservice import *
import logging
import sys

logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

data = {}


@mount('/{id}')
@validate('id', re=r'[-0-9a-zA-Z]{36}', doc='User ID, must be a valid UUID.')
class Document(Resource):
    """Represents an individual document in the document store. The storage
    is only persistent in-memory, so it will go away when the service is
    restarted.
    """
    NOT_FOUND = (KeyError,)

    def GET(self, id):
        "Return the document indicated by the ID."
        return data[id]

    def PUT(self, id):
        """Overwrite or create the document indicated by the ID. Parameters
        are passed as key/value pairs in the POST data."""
        data.setdefault(id, {'id': id})
        for key in self.request.POST:
            data[id][key] = self.request.POST[key]
        return {'id': id, 'saved': True}

    def DELETE(self, id):
        "Delete the document indicated by the ID."
        del data[id]

@mount('/')
class Documents(Resource):
    def POST(self):
        """Create a new document, assigning a unique ID. Parameters are
        passed in as key/value pairs in the POST data."""
        id = str(uuid.uuid4())
        res = self.get_resource(Document)
        self.response.body_raw = res.PUT(id)
        raise_201(self, id)

app = get_app(globals())

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    print "Running on port 8001"
    make_server('', 8001, app).serve_forever()
