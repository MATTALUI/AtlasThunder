import os

import jsonfig


_filename = os.path.join(os.path.dirname(__file__), 'config.json')

config = jsonfig.from_path(_filename)
