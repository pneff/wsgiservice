"""The user service is a simple user storage which allows users to
authenticate. This is currently a dummy implementation with ony in-memory
storage.

Similar to store.py but uses more of the REST framework."""

import uuid
import wsgiservice

users = {}


def status_xml(self, retval):
    """XML response for status of PUT and POST."""
    return '<status saved="{0}"><id>{1}</id></status>'.format(
        retval['id'], retval['saved'])


@wsgiservice.mount('/{id}')
@wsgiservice.validate('id', re=r'[0-9a-zA-Z-]{36}', doc='Document ID, must be a valid UUID.')
class User(wsgiservice.Resource):
    @wsgiservice.expires(wsgiservice.duration.1day)
    def GET(self, id):
        "Return the document indicated by the ID."
        with wsgiservice.etag(id):
            return users[id]

    @wsgiservice.validate('email', doc="User's email. This is the unique identifier of a user.")
    @wsgiservice.validate('password', doc="User's password.")
    def PUT(self, request, id, email=None, password=None):
        """Overwrite or create the document indicated by the ID. Parameters
        are passed as key/value pairs in the POST data."""
        users.setdefault(id, {'id': id})
        if email:
            users[id]['email'] = email
        if password:
            users[id]['password'] = password
        return {'id': id, 'saved': True}
    PUT.to_xml = status_xml

    def DELETE(self, id):
        "Delete the document indicated by the ID."
        del users[id]
        return {'id': id, 'deleted': True}
    DELETE.to_xml = status_xml


@wsgiservice.mount('/')
class Users(wsgiservice.Resource):
    def POST(self, request):
        """Create a new document, assigning a unique ID. Parameters are
        passed in as key/value pairs in the POST data."""
        id = str(uuid.uuid4())
        res = Document()
        return res.PUT(request, id)
    POST.to_xml = status_xml


@wsgiservice.mount('/{email}')
class UserEmailView(wsgiservice.Resource):
    @wsgiservice.validate('email', doc="User's email. This is the unique identifier of a user.")
    @wsgiservice.validate('password', doc="User's password.")
    @wsgiservice.expires(wsgiservice.duration.4hours)
    def POST(self, email, password, request):
        """Checks if the given user/password combination is correct. Returns
        the user hash if successful, returns False otherwise."""
        if id in users and users['id'].get('password', '') == password:
            return users
        else:
            return False


app = wsgiservice.get_app(globals(), '/1')

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    print "Running on port 8000"
    make_server('', 8000, app).serve_forever()
