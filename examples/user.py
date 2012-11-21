"""The user service is a simple user storage which allows users to
authenticate. This is currently a dummy implementation with ony in-memory
storage.

Similar to store.py but uses more of the REST framework."""
import hashlib
import uuid
from datetime import timedelta
import sys
import logging
import paste.urlmap
from wsgiservice import Resource, mount, validate, expires, raise_201, get_app


def get_hashed(password):
    SALT = 'some_pwd_salt'
    return hashlib.sha1(SALT + password).hexdigest()

logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

users = {}


@mount('/{id}')
@validate('id', re=r'[-0-9a-zA-Z]{36}', doc='User ID, must be a valid UUID.')
class User(Resource):
    NOT_FOUND = (KeyError,)

    @expires(timedelta(days=1))
    def GET(self, id):
        "Return the document indicated by the ID."
        return users[id]

    @validate('email', doc="User's email. This is the unique identifier of a user.")
    @validate('password', doc="User's password.")
    def PUT(self, id, email=None, password=None):
        """Overwrite or create the document indicated by the ID. Parameters
        are passed as key/value pairs in the POST data."""
        users.setdefault(id, {'id': id})
        if email:
            users[id]['email'] = email
        if password:
            users[id]['password'] = get_hashed(password)
        return {'id': id, 'saved': True}

    def DELETE(self, id):
        "Delete the document indicated by the ID."
        del users[id]
        return {'id': id, 'deleted': True}

    def to_text_xml(self, retval):
        if isinstance(retval, dict) and 'saved' in retval:
            return '<status saved="{0}"><id>{1}</id></status>'.format(
                retval['saved'], retval['id'])
        elif isinstance(retval, dict) and 'deleted' in retval:
            return '<status deleted="{0}"><id>{1}</id></status>'.format(
                retval['deleted'], retval['id'])
        else:
            return Resource.to_text_xml(self, retval)


@mount('/')
class Users(Resource):
    @validate('email', doc="User's email. This is the unique identifier of a user.")
    @validate('password', doc="User's password.")
    def POST(self, email, password):
        """Create a new document, assigning a unique ID. Parameters are
        passed in as key/value pairs in the POST data."""
        id = str(uuid.uuid4())
        res = self.get_resource(User)
        self.response.body_raw = res.PUT(id, email, password)
        raise_201(self, id)


@mount('/auth/{email}')
@validate('email', doc="User's email. This is the unique identifier of a user.")
@validate('password', doc="User's password.")
class UserEmailView(Resource):
    """Authenticate users."""
    @expires(timedelta(hours=4))
    def POST(self, email, password, request):
        """Checks if the given user/password combination is correct. Returns
        the user hash if successful, returns False otherwise."""
        the_user = self.getUser(email)
        if the_user and the_user.get('password', '') == get_hashed(password):
            return users
        else:
            return False

    def getUser(self, email):
        """Returns the user with the given email address."""
        for u in users:
            if email == users[u].get('email'):
                return users[u]
        return None


userapp = get_app(globals())

app = paste.urlmap.URLMap()
app['/1'] = userapp

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    print "Running on port 8000"
    make_server('', 8000, app).serve_forever()
