from twisted.internet import reactor
from twisted.web.server import Site

from atlas.config import config
from atlas.resources import build_resource


factory = Site(build_resource())
reactor.listenTCP(config['port'], factory)
reactor.run()
