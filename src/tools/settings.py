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
        'database': os.environ['DATABASE_NAME'],
        'host': os.environ['DATABASE_HOST'],
        'user': os.environ['DATABASE_USER'],
        'password': os.environ['DATABASE_PSW'],
        'adapter': os.environ.get('DATABASE_ENGINE', 'postgresql'),
        'port': os.environ.get('DATABASE_PORT', '5432')
    }
}

ADVERSARY = os.environ.get('ADVERSARY', 'hacker')
CAMPAIGN = os.environ.get('CAMPAIGN', 'default')

DEFENDERS_NETWORK = os.environ['DEFENDERS_NETWORK']
