from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.resource import Resource

from atlas.resources import CreateResource, ReadResource


root = Resource()
root.putChild("create", CreateResource())
root.putChild("posts", ReadResource())
factory = Site(root)
reactor.listenTCP(8080, factory)
reactor.run()
