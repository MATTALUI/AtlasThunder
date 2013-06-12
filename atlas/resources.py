from twisted.web.resource import Resource
import cgi
from pymongo import MongoClient, DESCENDING
import datetime
from twisted.web.util import redirectTo
from jinja2 import Environment, FileSystemLoader
from bson.objectid import ObjectId
env = Environment(loader=FileSystemLoader('templates'))


class CreateResource(Resource):

    def __init__(self):
        Resource.__init__(self)
        self.client = MongoClient('localhost', 27017)
        self.db = self.client.atlas

    def render_GET(self, request):

        return env.get_template('create.html').render().encode('utf-8')

    def render_POST(self, request):
        blogpost = {'author': cgi.escape(request.args['author'][0]),
                    'text': cgi.escape(request.args['text'][0]),
                    'tags': cgi.escape(request.args['tags'][0]),
                    'date': datetime.datetime.utcnow(), }
        posts = self.db.posts
        posts.insert(blogpost)
        return redirectTo('read', request)


class SinglePostResource(Resource):
    def __init__(self, post_id):
        Resource.__init__(self)
        self.client = MongoClient('localhost', 27017)
        self.db = self.client.atlas
        self.post_id = post_id

    def render_GET(self, request):
        blogposts = self.db.posts.find({'_id': ObjectId(self.post_id)})
        template = env.get_template('singlepost.html')
        context = {'posts': blogposts}
        return template.render(context).encode('utf-8')

    def render_POST(self, request):
        pass


class ReadResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.client = MongoClient('localhost', 27017)
        self.db = self.client.atlas

    def render_GET(self, request):
        blogposts = self.db.posts.find().sort('date', DESCENDING)

        template = env.get_template('read.html')
        context = {'posts': blogposts}
        return template.render(context).encode('utf-8')

    def getChild(self, path, request):
        return SinglePostResource(path)

    def render_POST(self, request):
        return env.get_template('nope.html').render().encode('utf-8')
