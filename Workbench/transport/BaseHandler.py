import logging
from abc import ABC, abstractmethod

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
class BaseHandler(ABC):
    def __init__(self,name):
        self.logger = logging.getLogger(name)