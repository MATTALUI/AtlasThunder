from twisted.web.resource import Resource
import cgi
from pymongo import MongoClient, DESCENDING
import datetime
from twisted.web.util import redirectTo
from bson.objectid import ObjectId
from twisted.web.static import File
from atlas.config import config
from atlas.template import render_response

class PostResource(Resource):
    def __init__(self, post_id):
        Resource.__init__(self)
        self.client = MongoClient('localhost', 27017)
        self.db = self.client.atlas

        self.post_id = post_id
    def render_GET(self, request):
        blogposts = self.db.posts.find({'_id': ObjectId(self.post_id)})
        context = {'posts': blogposts}
        return render_response('singlepost.html', context)


class PostsResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.client = MongoClient('localhost', 27017)
        self.db = self.client.atlas
    def render_GET(self, request):
        blogposts = self.db.posts.find().sort('date', DESCENDING)
        context = {'posts': blogposts}
        return render_response('posts.html', context)
    def getChild(self, path, request):
        return PostResource(path)

class AdminCreateResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.client = MongoClient('localhost', 27017)
        self.db = self.client.atlas
    def render_GET(self, request):
        return render_response('create.html')

    def render_POST(self, request):
        blogpost = {'author': cgi.escape(request.args['author'][0]),
                    'text': cgi.escape(request.args['text'][0]),
                    'tags': cgi.escape(request.args['tags'][0]),
                    'date': datetime.datetime.utcnow(), }
        posts = self.db.posts
        posts.insert(blogpost)
        return redirectTo('admin', request)

class AdminUpdateResource(Resource):
    def __init__(self, post_id=None):
        Resource.__init__(self)
        self.client = MongoClient('localhost', 27017)
        self.db = self.client.atlas
        self.post_id = post_id

    def render_GET(self, request):
        post = self.db.posts.find({'_id': ObjectId(self.post_id)}).next()
        context = {'post': post}
        return render_response('create.html', context)
    def render_POST(self, request):
        data = {'author': cgi.escape(request.args['author'][0]),
                    'text': cgi.escape(request.args['text'][0]),
                    'tags': cgi.escape(request.args['tags'][0]),}
        self.db.posts.update({'_id': ObjectId(cgi.escape(request.args['id'][0]))}, {'$set': data})
        return redirectTo('/admin', request)
    def getChild(self, path, request):
        return AdminUpdateResource(post_id=path)

class AdminDeleteResource(Resource):
    def __init__(self, post_id):
        Resource.__init__(self)
        self.client = MongoClient('localhost', 27017)
        self.db = self.client.atlas
        self.post_id = post_id

    def render_POST(self, request):
        pass


class AdminReadResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.client = MongoClient('localhost', 27017)
        self.db = self.client.atlas

    def render_GET(self, request):
        blogposts = self.db.posts.find().sort('date', DESCENDING)
        context = {'posts': blogposts}
        return render_response('read.html', context)

    def getChild(self, path, request):
        if path == 'edit':
            return AdminUpdateResource()
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
