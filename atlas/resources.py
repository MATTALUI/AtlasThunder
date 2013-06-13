from twisted.web.resource import Resource
import cgi
from pymongo import MongoClient, DESCENDING
import datetime
from twisted.web.util import redirectTo
from bson.objectid import ObjectId

from atlas.config import config
from atlas.template import render_response


class CreateResource(Resource):

    def __init__(self):
        Resource.__init__(self)
        self.client = MongoClient(
            config['mongodb']['host'], config['mongodb']['port'])
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
        return redirectTo('posts', request)


class SinglePostResource(Resource):
    def __init__(self, post_id):
        Resource.__init__(self)
        self.client = MongoClient('localhost', 27017)
        self.db = self.client.atlas
        self.post_id = post_id

    def render_GET(self, request):
        blogposts = self.db.posts.find({'_id': ObjectId(self.post_id)})
        context = {'posts': blogposts}
        return render_response('singlepost.html', context)

    def render_POST(self, request):
        pass


class ReadResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.client = MongoClient('localhost', 27017)
        self.db = self.client.atlas

    def render_GET(self, request):
        blogposts = self.db.posts.find().sort('date', DESCENDING)
        context = {'posts': blogposts}
        return render_response('read.html', context)

    def getChild(self, path, request):
        return SinglePostResource(path)

    def render_POST(self, request):
        return render_response('nope.html')


RESOURCE_MAPPING = {
    'create': CreateResource(),
    'posts': ReadResource()
}


def build_resource():
    root = Resource()

    for key, val in RESOURCE_MAPPING.iteritems():
        root.putChild(key, val)

    return root
