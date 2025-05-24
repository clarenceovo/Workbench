import logging
from Workbench.transport.websocket_client import websocket_client
from abc import ABC, abstractmethod

class BaseWSCollector(ABC):
    """
    Base class for WebSocket data collectors.
    """
    def __init__(self,name, url: str):
        self.logger = logging.getLogger(name)
        self.name = name
        self.url = url
        self.client = websocket_client(url)
        self.data = None
        self.logger.info("Initializing WebSocket client...{}".format(url))

    @abstractmethod
    def load_instrument(self):
        """
        Load the instrument for the data collector.
        """
        pass

    @abstractmethod
    def connect(self):
        """
        Connect to the WebSocket server.
        """
        pass

    @abstractmethod
    def disconnect(self):
        """
        Disconnect from the WebSocket server.
        """
        pass

    @abstractmethod
    def subscribe(self, topic: str):
        """
        Subscribe to a specific topic on the WebSocket server.
        """
        pass

    @abstractmethod
    def unsubscribe(self, topic: str):
        """
        Unsubscribe from a specific topic on the WebSocket server.
        """
        pass

    @abstractmethod
    def ping(self):
        """
        Send a ping message to the WebSocket server.
        """
        pass