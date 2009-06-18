"""The store service is a simple document store. It stores key/value pairs on
the documents. This is currently a dummy implementation with ony in-memory
storage."""

import uuid
import wsgiservice
import logging
import sys

logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)


data = {}

@wsgiservice.mount('/{id}')
@wsgiservice.validate('id', re=r'[-0-9a-zA-Z]{36}', doc='User ID, must be a valid UUID.')
class Document(wsgiservice.Resource):
    def GET(self, id):
        "Return the document indicated by the ID."
        try:
            return data[id]
        except KeyError:
            wsgiservice.raise_404(self)

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

@wsgiservice.mount('/')
class Documents(wsgiservice.Resource):
    def POST(self):
        """Create a new document, assigning a unique ID. Parameters are
        passed in as key/value pairs in the POST data."""
        id = str(uuid.uuid4())
        res = Document(self.request, self.response, self.path_params)
        return res.PUT(id)


import inspect
@wsgiservice.mount('/_internal/docs')
class Help(wsgiservice.Resource):
    XML_ROOT_TAG = 'help'
    app = None

    def GET(self):
        "Returns documentation for the application."
        retval = []
        for res in app._resources:
            retval.append({
                'name': res.__name__,
                'properties': {
                    'XML_ROOT_TAG': res.XML_ROOT_TAG,
                    'KNOWN_METHODS': res.KNOWN_METHODS,
                    'EXTENSION_MAP': dict((key[1:], value) for key, value
                        in res.EXTENSION_MAP.iteritems()),
                    'NOT_FOUND': [ex.__name__ for ex in res.NOT_FOUND],
                },
                'methods': self._get_methods(res),
                'path': res._path,
            })
        return retval

    def _get_methods(self, res):
        """Return a dictionary of method descriptions for the given resource.
        """
        retval = {}
        instance = res(None, None, None)
        methods = [m.strip() for m in instance.get_allowed_methods().split(',')]
        for method_name in methods:
            method = getattr(res, method_name)
            retval[method_name] = {
                'desc': method.__doc__.strip(),
                'parameters': self._get_parameters(res, method)
            }
        return retval
    
    def _get_parameters(self, res, method):
        """Return a parameters dictionary for the given resource/method."""
        method_params, varargs, varkw, defaults = inspect.getargspec(method)
        if method_params:
            method_params.pop(0) # pop the self off
        retval = {}
        for param in method_params:
            is_path_param = '{' + param + '}' in res._path
            retval[param] = {
                'path_param': is_path_param,
                'mandatory': is_path_param,
                'validate_re': None,
                'desc': '',
            }
            validation = self._get_validation(method, param)
            if validation:
                retval[param]['validate_re'] = validation['re']
                retval[param]['desc'] = validation['doc'] or ''
        return retval

    def _get_xml_value(self, value):
        """Treat arrays better."""
        if isinstance(value, list):
            retval = []
            for key, value in enumerate(value):
                retval.append('<resource>')
                retval.append(self._get_xml_value(value))
                retval.append('</resource>')
            return "".join(retval)
        else:
            return wsgiservice.Resource._get_xml_value(self, value)



app = wsgiservice.get_app(globals())
# Help.app = app

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    print "Running on port 8001"
    make_server('', 8001, app).serve_forever()
