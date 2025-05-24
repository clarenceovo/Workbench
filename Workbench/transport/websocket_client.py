import logging
import threading
import json
import os
import sys
import ssl
from queue import Queue as queue
import websocket as ws
import schedule

try:
    import thread
except ImportError:
    import _thread as thread
import zlib

import time
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
class websocket_client(threading.Thread):

    def __init__(self,url,callback=None,header=None):
        self.is_running = True
        super(websocket_client, self).__init__()
        self.incoming_queue = queue()
        self.outgoing_queue = queue()
        self.transportType = "websocket"
        self.header = header
        self.wsUrl = url
        self.callback = callback
        self.webSocket = None
        self.is_start = False
        self.main_thread = None

    def on_message(self,ws,message):
        try:
            self.callback(message)
        except:
            pass

    def on_error(self,ws,message):
        logger.error(message)

    def on_open(self,ws):
        def run(*args):
            while self.is_running:
                try:
                    while not self.outgoing_queue.empty():
                        if not self.is_start:
                            time.sleep(0.5)
                            self.is_start = True
                        else:
                            time.sleep(0.00001)
                        msg = self.outgoing_queue.get(block=True)
                        if msg == "ping":
                            ws.send("ping")
                            continue
                        ws.send(self.messsagePraser(msg))
                        self.outgoing_queue.task_done()
                    time.sleep(0.0001)
                except Exception as e:
                    logger.error(e)
                    logger.error(self.wsUrl)
                    self.is_running =False


        self.main_thread = thread.start_new_thread(run, ())

    def on_close(self,ws,close_status_code, close_msg):
        logger.error(close_msg)
        logger.error("websocket is closed.")



    def stop(self):
        logger.info("Stopping Websocket Client...")
        self.is_running = False
        self.webChannel.keep_running=False
        self.stop()

    def run(self):
        self.webChannel = ws.WebSocketApp(self.wsUrl,
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close,
                                    on_open=self.on_open,
                                    header=self.header if self.header is not None else None)
        self.webChannel.on_open = self.on_open(self.webChannel)
        self.webChannel.run_forever()


    def messsagePraser(self,msg):
        return json.dumps(msg)

    def messageLoader(self,msg):
        return json.loads(msg)