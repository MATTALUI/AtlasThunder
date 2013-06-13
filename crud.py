from twisted.internet import reactor
from twisted.web.server import Site

from atlas.resources import build_resource


factory = Site(build_resource())
reactor.listenTCP(8080, factory)
reactor.run()
