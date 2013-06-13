'''Template processing functions.'''
from jinja2 import Environment, FileSystemLoader

from atlas.config import config

_env = Environment(loader=FileSystemLoader(config['template_directory']))


def render_response(name, context={}):
    '''A shortcut for rendering templates.'''
    template = _env.get_template(name)

    return template.render(context).encode('utf-8')
