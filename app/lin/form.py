"""
forms of Lin
~~~~~~~~~

forms check the incoming params and data

:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

from typing import Any, List, Optional, Union

from flask import request
from wtforms import Field
from wtforms import Form as WTForm
from wtforms import IntegerField
from wtforms.validators import StopValidation

from .exception import ParameterError


class Form(WTForm):
    def __init__(self) -> None:
        data = request.get_json(silent=True)
        args = request.args.to_dict()
        illegal_params = set(args.keys()) & {
            "formdata",
            "obj",
            "prefix",
            "data",
            "meta",
        }
        if illegal_params:
            raise ParameterError("非法参数: {}".format(illegal_params))
        super(Form, self).__init__(data=data, **args)

    def validate_for_api(self) -> "Form":
        valid = super(Form, self).validate()
        if not valid:
            raise ParameterError(self.errors)
        return self


def integer_check(form: Form, field: Field) -> None:
    if field.data is None:
        raise StopValidation("输入字段不可为空")
    try:
        field.data = int(field.data)
    except ValueError:
        raise StopValidation("不是一个有效整数")


class LinIntegerField(IntegerField):
    """
    校验一个字段是否为正整数
    """

    def __init__(self, label: Optional[str] = None, validators: Optional[List[Any]] = None, **kwargs: Any) -> None:
        if validators is not None and type(validators) == list:
            validators.insert(0, integer_check)
        else:
            validators = [integer_check]
        super(LinIntegerField, self).__init__(label, validators, **kwargs)
