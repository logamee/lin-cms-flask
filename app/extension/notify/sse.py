"""
sse of Lin
~~~~~~~~~

sse 实现类

:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

import json
from collections import deque


class Sse(object):
    messages = deque()
    _retry = None

    def __init__(self, default_retry=2000):
        self._buffer = []
        self._default_id = 1
        self.set_retry(default_retry)

    def set_retry(self, num):
        self._retry = num
        self._buffer.append("retry: {0}\n".format(self._retry))

    def set_event_id(self, event_id=None):
        if event_id:
            self._default_id = event_id
            self._buffer.append("id: {0}\n".format(event_id))
        else:
            self._buffer.append("id: {0}\n".format(self._default_id))

    def reset_event_id(self):
        self.set_event_id(1)

    def increase_id(self):
        self._default_id += 1

    def add_message(self, event, obj, flush=True):
        self.set_event_id()
        self._buffer.append("event: {0}\n".format(event))
        line = json.dumps(obj, ensure_ascii=False)
        self._buffer.append("data: {0}\n".format(line))
        self._buffer.append("\n")
        if flush:
            self.flush()

    def flush(self):
        self.messages.append(self.join_buffer())
        self._buffer.clear()
        self.increase_id()

    def pop(self):
        return self.messages.popleft()

    def heartbeat(self, comment=None):
        # 发送注释 : this is a test stream\n\n 告诉客户端，服务器还活着
        if comment and type(comment) == "str":
            self._buffer.append(comment)
        else:
            self._buffer.append(": sse sever is still alive \n\n")
        tmp = self.join_buffer()
        self._buffer.clear()
        return tmp

    def join_buffer(self):
        string = ""
        for it in self._buffer:
            string += it
        return string

    def exit_message(self):
        return len(self.messages) > 0


sser = Sse()
