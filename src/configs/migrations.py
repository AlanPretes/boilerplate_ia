import os

from flask_migrate import Migrate


migrate = Migrate(directory=os.path.join(os.path.dirname(__file__), 'migrations'))