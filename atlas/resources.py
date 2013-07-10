from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
import txmongo
from txmongo import filter as _filter
import cgi
#from txmongo import MongoClient, DESCENDING
#from pymongo import MongoClient, DESCENDING
import datetime
from twisted.web.util import redirectTo
from txmongo._pymongo.objectid import ObjectId
from twisted.web.static import File
from atlas.config import config
from atlas.template import render_response

_client = txmongo.lazyMongoConnectionPool()
_db = _client.atlas

class PostResource(Resource):
    def __init__(self, post_id):
        Resource.__init__(self)

        self.post_id = post_id
    def render_GET(self, request):
        def handle_post(post):
            context = {'post' : post}
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
        #return render_response('posts.html', context)
    def getChild(self, path, request):
        return PostResource(path)

class AdminCreateResource(Resource):
    def __init__(self):
        Resource.__init__(self)
#        self.client = MongoClient('localhost', 27017)
     #   self.db = self.client.atlas
    def render_GET(self, request):
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
                    'tags': cgi.escape(request.args['tags'][0]),}
        d = _db.posts.update({'_id': ObjectId(cgi.escape(request.args['id'][0]))}, {'$set': data})
        d.addCallback(finish)
        return NOT_DONE_YET
    def getChild(self, path, request):
        return AdminUpdateResource(post_id=path)

class AdminDeleteResource(Resource):
    def __init__(self, post_id):
        Resource.__init__(self)
  #      self.client = MongoClient('localhost', 27017)
       # self.db = self.client.atlas
        self.post_id = post_id

    def render_POST(self, request):
        pass


class AdminReadResource(Resource):
    def render_GET(self, request):
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
        raise

    def render_POST(self, request):
        return render_response('nope.html')


RESOURCE_MAPPING = {
    'admin': AdminReadResource(),
    'static': File('static'),
    'posts' : PostsResource(),
}


def build_resource():
    root = Resource()

    for key, val in RESOURCE_MAPPING.iteritems():
        root.putChild(key, val)

    return root
