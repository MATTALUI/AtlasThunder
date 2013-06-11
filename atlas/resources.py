from twisted.web.resource import Resource
import cgi
from pymongo import MongoClient
import datetime
from twisted.web.util import redirectTo
from jinja2 import Environment, FileSystemLoader
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
                    'date': datetime.datetime.utcnow()}
        posts = self.db.posts
        posts.insert(blogpost)
        return redirectTo('read', request)


class SearchResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.client = MongoClient('localhost', 27017)
        self.db = self.client.atlas

    def render_GET(self, request):
        return env.get_template('search.html').render().encode('utf-8')

    def render_POST(self, request):
        pass


class ReadResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.client = MongoClient('localhost', 27017)
        self.db = self.client.atlas

    def render_GET(self, request):
        return env.get_template('read.html').render().encode('utf-8')

    def render_POST(self, request):
        pass
