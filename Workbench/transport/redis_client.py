import redis
import json
import logging
from Workbench.transport.BaseHandler import BaseHandler
SUBSCRIPTION_CONSTANT = '__keyspace@0__'

class RedisClient(BaseHandler):

    def __init__(self, host, port, password, db=0):
        super().__init__('RedisClient')
        self.client = redis.StrictRedis(host=host, port=port, password=password, db=db)

        self.logger = logging.getLogger("RedisClient")
        self.client.config_set('notify-keyspace-events', 'KEA')
        self.channel = self.client.pubsub()

    def get(self, key,field=None):
        # Retrieve the value based on the key type
        key_type = self.client.type(key).decode('utf-8')
        if key_type == 'string':
            return self.client.get(key).decode('utf-8')
        elif key_type == 'hash':
            if field:
                return self.client.hget(key, field).decode('utf-8')
            else:
                obj = self.client.hgetall(key)
                return {k.decode('utf-8'): v.decode('utf-8') for k, v in obj.items()}
        elif key_type == 'list':
            return self.client.lrange(key, 0, -1)
        elif key_type == 'set':
            return self.client.smembers(key)
        elif key_type == 'zset':
            return self.client.zrange(key, 0, -1, withscores=True)
        else:
            return None

    def get_all_keys(self):
        return self.client.keys()

    def set(self, key, value):
        return self.client.set(key, value)

    def set_json(self, key, value):
        return self.client.set(key, json.dumps(value))

    def hset (self, key, field, value):
        return self.client.hset(key, field, value)
    
    def get_json(self, key):
        return json.loads(self.client.get(key))

    def subscribe(self, channel_name: str):
        print(f'Subsccribing to {SUBSCRIPTION_CONSTANT}:{channel_name}')
        self.channel.subscribe(f'{SUBSCRIPTION_CONSTANT}:{channel_name}')


    def get_channel(self):
        return self.channel


