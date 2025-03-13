"""
notify of Lin
~~~~~~~~~

notify 扩展，消息推送

:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

import re
from datetime import datetime
from functools import wraps

from flask import Response, request
from flask_jwt_extended import get_current_user

from .sse import sser

REG_XP = r"[{](.*?)[}]"
OBJECTS = ["user", "response", "request"]
SUCCESS_STATUS = [200, 201]
MESSAGE_EVENTS = set()


class Notify(object):
    def __init__(self, template=None, event=None, **kwargs):
        """
        Notify a message or create a log
        :param template:  message template
        {user.username}查看自己是否为激活状态 ，状态码为{response.status_code} -> pedro查看自己是否为激活状态 ，状态码为200
        :param write: write to db or not
        :param push: push to front_end or not
        """
        if event:
            self.event = event
        elif self.event is None:
            raise Exception("event must not be None!")
        if template:
            self.template: str = template
        elif self.template is None:
            raise Exception("template must not be None!")
        # 加入所有types中
        MESSAGE_EVENTS.add(event)
        self.message = ""
        self.response = None
        self.user = None
        self.extra = kwargs

    def __call__(self, func):
        @wraps(func)
        def wrap(*args, **kwargs):
            response: Response = func(*args, **kwargs)
            self.response = response
            self.user = get_current_user()
            self.message = self._parse_template()
            self.push_message()
            return response

        return wrap

    def push_message(self):
        # status = '操作成功' if self.response.status_code in SUCCESS_STATUS else '操作失败'
        sser.add_message(
            self.event,
            {
                "message": self.message,
                "time": int(datetime.now().timestamp()),
                **self.extra,
            },
        )

    # 解析自定义消息的模板
    def _parse_template(self):
        message = self.template
        total = re.findall(REG_XP, message)
        for it in total:
            assert "." in it, "%s中必须包含 . ,且为一个" % it
            i = it.rindex(".")
            obj = it[:i]
            assert obj in OBJECTS, "%s只能为user,response,request中的一个" % obj
            prop = it[i + 1 :]
            if obj == "user":
                item = getattr(self.user, prop, "")
            elif obj == "response":
                item = getattr(self.response, prop, "")
            else:
                item = getattr(request, prop, "")
            message = message.replace("{%s}" % it, str(item))
        return message

    def _check_can_push(self):
        # 超级管理员不可push，暂时测试可push
        if self.user.is_admin:
            return False
        return True
