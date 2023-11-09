from abc import ABC, abstractmethod
import redis
import json


class Cache(ABC):

    @abstractmethod
    def get(self, key):
        pass

    @abstractmethod
    def set(self, key, value):
        pass


class SimpleCache(Cache):

    def __init__(self):
        self.cache = {}

    def get(self, key):
        if cached_key := self.cache.get(key):
            return cached_key
        return None

    def set(self, key, value):
        self.cache[key] = value


class RedisCache(Cache):

    def __init__(self, host='localhost', port=6379, db=0):
        self.cache = redis.StrictRedis(host=host, port=port, db=db)

    def get(self, key):
        if cached_key := self.cache.get(key):
            return json.loads(cached_key)
        return None

    def set(self, key, value):
        formatted_value = json.dumps(value)
        self.cache.set(key, formatted_value)

