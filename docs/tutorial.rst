Tutorial
========

Creating a WsgiService application requires very little code. First you'll need to import wsgiservice of course::

    from wsgiservice import *

Next you create a subclass :class:`wsgiservice.Resource` which will handle the different representations of a source. For example a document resource which stores documents in an in-memory dictionary::

    data = {}

    @mount('/{id}')
    class Document(Resource):
        def GET(self, id):
            """Return the document indicated by the ID."""
            return data[id]

        def PUT(self, request, id):
            """Overwrite or create the document indicated by the ID."""
            data.setdefault(id, {'id': id})
            for key in request.POST:
                data[id][key] = request.POST[key]
            return {'id': id, 'saved': True}

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
        def POST(self, request):
            """Create a new document, assigning a unique ID. Parameters are
            passed in as key/value pairs in the POST data."""
            id = str(uuid.uuid4())
            res = Document()
            return res.PUT(request, id)

You see how easy it is to use an existing request to do the work of saving. Unfortunately there is currently no way to put that POST action for creation in the ``Document`` resource where it would semantically belong.

Finally you'll need to create the actual WSGI application and serve it::

    app = get_app(globals())

    if __name__ == '__main__':
        from wsgiref.simple_server import make_server
        print "Running on port 8001"
        make_server('', 8001, app).serve_forever()

This uses the wsgiref simple server which comes with Python. For production you'll probably want to use a different server. But for now you can now run the resulting file and on port 8001 you'll have a simple document server available.
