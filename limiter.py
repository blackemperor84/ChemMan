import os

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Magazyn licznikow limitow. Domyslnie "memory://", ktore dziala tylko w obrebie
# jednego procesu — przy kilku workerach gunicorna kazdy ma wlasne liczniki,
# wiec faktyczny limit jest wielokrotnoscia zadeklarowanego. W produkcji ustaw
# RATELIMIT_STORAGE_URL na wspoldzielony backend, np. redis://localhost:6379.
RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL') or 'memory://'

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri=RATELIMIT_STORAGE_URL
)
