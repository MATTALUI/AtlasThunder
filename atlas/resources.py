from twisted.web.resource import Resource
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
        if not request.getCookie('username') == 'matt':
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
        if not request.getCookie('username') == 'matt':
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
    def __init__(self, post_id):
        Resource.__init__(self)
        self.post_id = post_id
#    if not request.getCookie('username') == 'matt':
#        request.redirect('/login')
#        return ''

    def render_POST(self, request):
        pass


class AdminReadResource(Resource):
    def render_GET(self, request):
        if not request.getCookie('username') == 'matt':
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
        raise Exception('unknown path: {0}'.format(path))

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
        if username == 'matt' and password == 'cats':
            request.addCookie('username', 'matt')
            request.redirect('/admin')
            return ''
        else:
            request.redirect('/login')
            return ''


class LogoutResource(Resource):
    def render_GET(self, request):
        request.addCookie('username', None)
        request.redirect('/posts')
        return ''
RESOURCE_MAPPING = {
    'admin': AdminReadResource(),
    'static': File('static'),
    'posts': PostsResource(),
    'login': LoginResource(),
    'logout': LogoutResource(),
}


def build_resource():
    root = Resource()

    for key, val in RESOURCE_MAPPING.iteritems():
        root.putChild(key, val)

    return root
