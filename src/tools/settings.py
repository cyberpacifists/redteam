import os

# base directory. Use this path to generate application paths.
# this referenced directory points to the upper folder from this file i.e. the app folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TTP = os.path.join(BASE_DIR, 'ttp')

ABILITIES_FILE = 'abilities'
ABILITIES_EXTENSION = 'yml'

INSTALLED_TTP = [
    'reconnaissance',
]

DEFAULT_SEPARATOR = '|'

DATABASES = {
    'default': {
        'database': os.environ.get('DATABASE_NAME', 'db'),
        'host': os.environ.get('DATABASE_HOST', 'localhost'),
        'user': os.environ.get('DATABASE_USER', 'username'),
        'password': os.environ.get('DATABASE_PSW', 'password'),
        'adapter': os.environ.get('DATABASE_ENGINE', 'postgresql'),
        'port': os.environ.get('DATABASE_PORT', '5432')
    }
}
