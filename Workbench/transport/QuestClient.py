import requests
import time
import threading
from queue import Queue, Empty
from Workbench.transport.BaseHandler import BaseHandler  # adjust if file name is different
from questdb.ingress import Sender, TimestampNanos
class QuestDBClient(BaseHandler):
    def __init__(self, host, port,batch_size=100, flush_interval=1.0):
        super().__init__("QuestDBClient")
        self.write_url = f"tcp::addr={host}:{port};"
        self.queue = Queue()
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()


    def write(self,table,symbol, columns,timestamp=None):
        if timestamp is None:
            timestamp = TimestampNanos.now()
        with Sender.from_conf(self.write_url) as sender:
            sender.row(table,
                       symbols=symbol,
                       columns=columns,
                       at= timestamp)
            sender.flush()
    def _flush_batch(self, batch):
        """
        Send batch to QuestDB.
        """
        data = "\n".join(batch)
        try:
            response = requests.post(self.write_url, data=data)
            if response.status_code != 204:
                self.logger.error(f"Failed batch write: {response.text}")
            else:
                self.logger.info(f"Flushed {len(batch)} records")
        except Exception as e:
            self.logger.exception(f"Flush error: {e}")

    def _run(self):
        """
        Background daemon thread: batch + flush data to QuestDB.
        """
        buffer = []
        last_flush = time.time()

        while not self._stop_event.is_set():
            try:
                line = self.queue.get(timeout=self.flush_interval)
                buffer.append(line)
            except Empty:
                pass  # just time-based flush

            if buffer and (len(buffer) >= self.batch_size or time.time() - last_flush >= self.flush_interval):
                self._flush_batch(buffer)
                buffer.clear()
                last_flush = time.time()

    def stop(self):
        """
        Graceful shutdown.
        """
        self._stop_event.set()
        self.thread.join()
        self.logger.info("QuestDBClient stopped.")