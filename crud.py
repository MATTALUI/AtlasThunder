from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.resource import Resource

from atlas.resources import CreateResource, SearchResource, ReadResource


root = Resource()
root.putChild("create", CreateResource())
root.putChild("search", SearchResource())
root.putChild("read", ReadResource())
factory = Site(root)
reactor.listenTCP(8080, factory)
reactor.run()
