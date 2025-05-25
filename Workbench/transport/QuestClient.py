import requests
import time
import threading
from dataclasses import dataclass
from datetime import datetime
from queue import Queue, Empty
from Workbench.transport.BaseHandler import BaseHandler  # adjust if file name is different
from questdb.ingress import Sender, TimestampNanos

@dataclass
class QuestBatch:
    topic: str
    symbol: dict
    columns: dict
    timestamp: datetime


class QuestDBClient(BaseHandler):
    def __init__(self, host, port, batch_size=100, flush_interval=0.5):
        super().__init__("QuestDBClient")
        self.is_active = True
        self.write_url = f"tcp::addr={host}:{port};"
        self.queue = Queue()
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def write(self, table, symbol, columns, timestamp=None):
        if timestamp is None:
            timestamp = TimestampNanos.now()
        with Sender.from_conf(self.write_url) as sender:
            sender.row(table,
                       symbols=symbol,
                       columns=columns,
                       at=timestamp)
            sender.flush()

    def batch_write(self, batch: QuestBatch):
        """
        Write a batch of data to QuestDB.
        :param batch: QuestBatch object containing the data to write.
        """

        self.queue.put_nowait(batch)


    def _run(self):
        """
        Send batch to QuestDB.
        """
        self.logger.info("QuestDBClient started batch writing loop...")
        flush_count = 0
        while self.is_active:
            try:
                with Sender.from_conf(self.write_url) as sender:
                    try:
                        while not self.queue.empty():
                            item = self.queue.get_nowait()
                            ts= TimestampNanos.from_datetime(item.timestamp)
                            sender.row(item.topic,
                                       symbols=item.symbol,
                                       columns=item.columns,
                                       at=ts)
                            sender.flush()
                    except Exception as e:
                        print(e)
                    sender.flush()
                    time.sleep(self.flush_interval)

            except Empty:
                continue

    def stop(self):
        """
        Graceful shutdown.
        """
        self._stop_event.set()
        self.thread.join()
        self.logger.info("QuestDBClient stopped.")
