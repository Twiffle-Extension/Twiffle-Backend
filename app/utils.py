import os
from queue import Queue
import base64
from typing import Dict, Union


class GlobalState:

    ENVIRONMENT_VARIABLE_KEYS = [
        "EBAY_CLIENT_ID",
        "EBAY_CLIENT_SECRET",
        "EBAY_BASE_API_URL",
        "HOSTNAME"
    ]
    APP_QUEUES = [
        "EBAY_AUTH_TOKEN"
    ]

    def __init__(self):
        # Environment variables loading
        for env_var_key in self.ENVIRONMENT_VARIABLE_KEYS:
            if not os.getenv(env_var_key):
                raise ValueError("Environment Variable {var} not set!".format(
                    var=env_var_key
                ))
        self._environment_settings = {
            env_var_key: os.getenv(env_var_key)
            for env_var_key in self.ENVIRONMENT_VARIABLE_KEYS
        }

        # Application-level messaging queues
        self._queues: Dict[str, Queue] = {}
        for app_queue in self.APP_QUEUES:
            self.create_pubsub(app_queue)

        self.access_token = None

    def get_environment_settings(self):
        return self._environment_settings

    def create_pubsub(self, name, queue: Union[Queue, None]=None):
        if not queue:
            self._queues[name] = Queue()
        else:
            self._queues[name] = queue

        return self._queues[name]

    def get_pubsub_or_create(self, name) -> Union[Queue, None]:
        if not self._queues.get(name):
            return self.create_pubsub(name)

        return self._queues.get(name)


GLOBAL_STATE = GlobalState()


def string_to_base64(some_string: str) -> str:
    return base64.b64encode(some_string.encode()).decode()


def base64_to_string(some_string: str) -> str:
    return base64.b64decode(some_string.encode()).decode()
