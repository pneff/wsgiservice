Tutorial
========

Creating a WsgiService application requires very little code. First you'll need to import wsgiservice of course::

    from wsgiservice import *

Next you create a subclass of :class:`wsgiservice.Resource` which will handle the different representations of a resource. For example a document resource which stores documents in an in-memory dictionary::

    data = {}

    @mount('/{id}')
    class Document(Resource):
        NOT_FOUND = (KeyError,)

        def GET(self, id):
            """Return the document indicated by the ID."""
            return data[id]

        def PUT(self, id):
            """Overwrite or create the document indicated by the ID."""
            is_new = id not in data
            data.setdefault(id, {'id': id})
            for key in self.request.POST:
                data[id][key] = self.request.POST[key]
            retval = {'id': id, 'saved': True}
            if is_new:
                self.response.body_raw = retval
                raise_201(self, id)
            else:
                return retval

        def DELETE(self, id):
            """Delete the document indicated by the ID."""
            del data[id]

        def get_etag(self, id):
            return id

Each resource defines the different HTTP methods it accepts. Additionally there are a special methods such as ``get_etag`` as described in :class:`wsgiservice.Resource` in more detail. All of these methods can specify any number of parameters to accept. Those will be filled automatically from these locations (in that order):

#. The special ``request`` parameter which will be filled with an instance of :class:`webob.Request` for the current request.
#. Parameters extracted from the path. `id` in the example above.
#. Parameters from the query string.
#. Parameters from the POST data.

Let's also create a ``Documents`` resource which can be used to create a new document::

    import uuid

    @mount('/')
    class Documents(Resource):
        def POST(self):
            """Create a new document, assigning a unique ID. Parameters are
            id = str(uuid.uuid4())
            res = self.get_resource(Document)
            return res.PUT(id)

You see how easy it is to use an existing request to do the work of saving.

Finally you'll need to create the actual WSGI application and serve it::

    app = get_app(globals())

    if __name__ == '__main__':
        from wsgiref.simple_server import make_server
        print "Running on port 8001"
        make_server('', 8001, app).serve_forever()

This uses the wsgiref simple server which comes with Python. For production you'll probably want to use a different server. But for now you can run the resulting file and on port 8001 you'll have a simple document server available.
