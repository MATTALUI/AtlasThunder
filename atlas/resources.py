from twisted.web.resource import Resource
import bcrypt
from twisted.web.server import NOT_DONE_YET
import txmongo
from txmongo import filter as _filter
import cgi
import datetime
from txmongo._pymongo.objectid import ObjectId
from twisted.web.static import File
from atlas.template import render_response
_client = txmongo.lazyMongoConnectionPool()
_db = _client.atlas
sessions = set()


class PostResource(Resource):
    def __init__(self, post_id):
        Resource.__init__(self)

        self.post_id = post_id

    def render_GET(self, request):
        def handle_post(post):
            context = {'post': post}
            request.write(render_response('singlepost.html', context))
            request.finish()
        _id = ObjectId(self.post_id)
        deferred = _db.posts.find_one(_id)
        deferred.addCallback(handle_post)
        return NOT_DONE_YET


class PostsResource(Resource):
    def __init__(self):
        Resource.__init__(self)

    def render_GET(self, request):
        def handle_posts(posts):
            context = {'posts': posts}
            request.write(render_response('posts.html', context))
            request.finish()
        f = _filter.sort(_filter.DESCENDING('date'))
        deferred = _db.posts.find(filter=f)
        deferred.addCallback(handle_posts)
        return NOT_DONE_YET

    def getChild(self, path, request):
        return PostResource(path)


class AdminCreateResource(Resource):
    def __init__(self):
        Resource.__init__(self)

    def render_GET(self, request):
        session = request.getSession()
        if session.uid not in sessions:
            request.redirect('/login')
            return ''
        return render_response('create.html')

    def render_POST(self, request):
        def finish(posts):
            request.redirect('/admin')
            request.finish()
        blogpost = {'author': cgi.escape(request.args['author'][0]),
                    'text': cgi.escape(request.args['text'][0]),
                    'tags': cgi.escape(request.args['tags'][0]),
                    'date': datetime.datetime.utcnow(), }
        posts = _db.posts
        d = posts.insert(blogpost)
        d.addCallback(finish)
        return NOT_DONE_YET


class AdminUpdateResource(Resource):
    def __init__(self, post_id=None):
        Resource.__init__(self)
        self.post_id = post_id

    def render_GET(self, request):
        session = request.getSession()
        if session.uid not in sessions:
            request.redirect('/login')
            return ''

        def handle_post(post):
            context = {'post': post}
            request.write(render_response('create.html', context))
            request.finish()
        d = _db.posts.find_one(ObjectId(self.post_id))
        d.addCallback(handle_post)
        return NOT_DONE_YET

    def render_POST(self, request):
        def finish(_):
            request.redirect('/admin')
            request.finish()
        data = {'author': cgi.escape(request.args['author'][0]),
                'text': cgi.escape(request.args['text'][0]),
                'tags': cgi.escape(request.args['tags'][0]), }
        d = _db.posts.update(
            {'_id': ObjectId(cgi.escape(request.args['id'][0]))},
            {'$set': data})
        d.addCallback(finish)
        return NOT_DONE_YET

    def getChild(self, path, request):
        return AdminUpdateResource(post_id=path)


class AdminDeleteResource(Resource):
    def __init__(self, post_id=None):
        Resource.__init__(self)
        self.post_id = post_id

    def render_GET(self, request):
        session = request.getSession()
        if session.uid not in sessions:
            request.redirect('/login')
            return ''

        def handle_post(post):
            context = {'post': post}
            request.write(render_response('delete.html', context))
            request.finish()
        _id = ObjectId(self.post_id)
        deferred = _db.posts.find_one(_id)
        deferred.addCallback(handle_post)
        return NOT_DONE_YET

    def render_POST(self, request):
        def finish(_):
            request.redirect('/admin')
            request.finish()
        _id = ObjectId(self.post_id)
        d = _db.posts.remove({'_id': _id})
        d.addCallback(finish)
        return NOT_DONE_YET

    def getChild(self, path, request):
        return AdminDeleteResource(post_id=path)


class AdminReadResource(Resource):
    def render_GET(self, request):
        session = request.getSession()
        if session.uid not in sessions:
            request.redirect('/login')
            return ''

        def handle_posts(posts):
            context = {'posts': posts}
            request.write(render_response('read.html', context))
            request.finish()
        f = _filter.sort(_filter.DESCENDING('date'))
        d = _db.posts.find(filter=f)
        d.addCallback(handle_posts)
        return NOT_DONE_YET

    def getChild(self, path, request):
        if path == 'edit':
            return AdminUpdateResource()
        elif path == 'new':
            return AdminCreateResource()
        elif path == 'delete':
            return AdminDeleteResource()

    def render_POST(self, request):
        return render_response('nope.html')


class LoginResource(Resource):
    def __init__(self):
        Resource.__init__(self)

    def render_GET(self, request):
        request.write(render_response('login.html'))
        request.finish()
        return NOT_DONE_YET

    def render_POST(self, request):
        username = cgi.escape(request.args['username'][0])
        password = cgi.escape(request.args['password'][0])
        d = _db.users.find_one({'username': username})

        def user_found(user):
            if not user:
                context = {'key':
                           "You're "
                           'not a user! Would you like to '
                           '<a href="/register">register</a>?'}
                request.write(render_response('sorry.html', context))
                request.finish()
                return 'not user'
            if bcrypt.hashpw(password, user['password']) == user['password']:
                session = request.getSession()
                if session.uid not in sessions:
                    sessions.add(session.uid)
                request.redirect('/admin')
                request.finish()
                return 'password correct'
            else:
                context = {'key': 'Incorrect password!'}
                request.write(render_response('sorry.html', context))
                request.finish()
                return 'password incorrect'
        d.addCallback(user_found)
        return NOT_DONE_YET


class LogoutResource(Resource):
    def render_GET(self, request):
        session = request.getSession()
        sessions.remove(session.uid)
        request.redirect('/posts')
        return ''


class SignUpResource(Resource):
    def render_GET(self, request):
        session = request.getSession()
        if session.uid in sessions:
            context = {'key': "You're already registered!"}
            request.write(render_response('sorry.html', context))
            request.finish()
            return NOT_DONE_YET
        return render_response('signup.html')

    def render_POST(self, request):
        dusername = cgi.escape(request.args['username'][0])
        dpassword = cgi.escape(request.args['password'][0])
        dpassword2 = cgi.escape(request.args['passwordconfirm'][0])

        if dpassword != dpassword2:
            context = {'key': 'Your passwords did not match!'}
            request.write(render_response('sorry.html', context))
            request.finish()
            return NOT_DONE_YET
        d = _db.users.find_one({'username': dusername})

        def verify_user(user):
            if user:
                context = {'key': 'That username already exists!'}
                request.write(render_response('sorry.html', context))
                request.finish()
            else:
                salt = bcrypt.gensalt()
                dhashword = bcrypt.hashpw(dpassword, salt)
                userinfo = {'username': dusername,
                            'password': dhashword}
                return _db.users.insert(userinfo)
        d.addCallback(verify_user)

        def user_created(_):
            request.redirect('/login')
            request.finish()
        d.addCallback(user_created)
        return NOT_DONE_YET
RESOURCE_MAPPING = {
    'admin': AdminReadResource(),
    'static': File('static'),
    'posts': PostsResource(),
    'login': LoginResource(),
    'logout': LogoutResource(),
    'register': SignUpResource(),
}


def build_resource():
    root = Resource()

    for key, val in RESOURCE_MAPPING.iteritems():
        root.putChild(key, val)

    return root
