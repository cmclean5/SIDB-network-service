from __future__ import print_function
from __future__ import absolute_import

__version__ = '1.0'


import logging

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(filename)s][%(funcName)20s] %(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)