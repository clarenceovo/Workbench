from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import os
import threading
import time
from queue import Queue, Empty
from Workbench.transport.BaseHandler import BaseHandler

class InfluxClient(BaseHandler):

    def __init__(self, url, org, token=None, batch_size=100, flush_interval=1.0):
        super().__init__("InfluxClient")
        token = token or os.getenv('INFLUX_TOKEN')
        if not token:
            raise ValueError("INFLUX_TOKEN must be set in environment or passed as argument")

        self.org = org
        self.url = url
        self.client = InfluxDBClient(url=url, token=token, org=self.org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.read_api = self.client.query_api()

        self.queue = Queue()
        self.batch_size = batch_size
        self.flush_interval = flush_interval

        self._stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def read_df(self, query):
        return self.read_api.query_data_frame(query, org=self.org)

    def read(self, query):
        return self.read_api.query(query, org=self.org)

    def write(self, bucket, point:Point):
        self.write_api.write(bucket=bucket,org=self.org, record=point)

    def _flush_batch(self, batch):
        try:
            buckets = set(bucket for bucket, _ in batch)
            if len(buckets) != 1:
                self.logger.error("All points in a batch must target the same bucket")
                return
            bucket = buckets.pop()
            points = [point for _, point in batch]
            self.write_api.write(bucket=bucket, org=self.org, record=points)
            self.logger.info(f"Flushed {len(points)} points to bucket '{bucket}'")
        except Exception as e:
            self.logger.exception(f"InfluxDB batch write failed: {e}")

    def _run(self):
        buffer = []
        last_flush = time.time()
        while not self._stop_event.is_set():
            try:
                item = self.queue.get(timeout=self.flush_interval)
                buffer.append(item)
            except Empty:
                pass

            if buffer and (len(buffer) >= self.batch_size or time.time() - last_flush >= self.flush_interval):
                self._flush_batch(buffer)
                buffer.clear()
                last_flush = time.time()

    def stop(self):
        self._stop_event.set()
        self.thread.join()


