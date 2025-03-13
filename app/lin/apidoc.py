import typing as t
from functools import wraps
from typing import *

from flask import Flask, current_app, g, json, jsonify, make_response
from pydantic import BaseModel as _BaseModel
from pydantic import validate_model
from pydantic.main import object_setattr
from spectree import SpecTree as _SpecTree
from spectree._types import ModelType
from spectree.response import DEFAULT_CODE_DESC, Response

from .db import Record, RecordCollection
from .exception import ParameterError
from .utils import camel2line


class ValidationError(_BaseModel):
    message: str = "parameter validation error message"
    code: int = 10030


class BaseModel(_BaseModel):
    class Config:
        allow_population_by_field_name = True

    # Uses something other than `self` the first arg to allow "self" as a settable attribute
    def __init__(__pydantic_self__, **data: t.Any) -> None:  # type: ignore
        values, fields_set, validation_error = validate_model(__pydantic_self__.__class__, data)
        if validation_error:
            raise ParameterError(" and ".join([f'{i["loc"][0]} {i["msg"]}' for i in validation_error.errors()]))
        try:
            object_setattr(__pydantic_self__, "__dict__", values)
        except TypeError as e:
            raise TypeError(
                "Model values must be a dict; you may not have returned a dictionary from a root validator"
            ) from e
        object_setattr(__pydantic_self__, "__fields_set__", fields_set)
        __pydantic_self__._init_private_attributes()

    """
    Workaround for serializing properties with pydantic until
    https://github.com/samuelcolvin/pydantic/issues/935
    is solved
    """

    @classmethod
    def get_properties(cls):
        return [
            prop
            for prop in dir(cls)
            if isinstance(getattr(cls, prop), property) and prop not in ("__values__", "fields")
        ]

    def dict(
        self,
        *,
        include=None,
        exclude=None,
        by_alias: bool = False,
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ):
        attribs = super().dict(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
        props = self.get_properties()
        # Include and exclude properties
        if include:
            props = [prop for prop in props if prop in include]
        if exclude:
            props = [prop for prop in props if prop not in exclude]

        # Update the attribute dict with the properties
        if props:
            attribs.update({prop: getattr(self, prop) for prop in props})

        return attribs


class SpecTree(_SpecTree):
    def validate(  # noqa: PLR0913  [too-many-arguments]
        self,
        query: Optional[ModelType] = None,
        json: Optional[ModelType] = None,
        form: Optional[ModelType] = None,
        headers: Optional[ModelType] = None,
        cookies: Optional[ModelType] = None,
        resp: Optional[Response] = None,
        tags: Sequence = (),
        security: Any = None,
        deprecated: bool = False,
        before: Optional[Callable] = None,
        after: Optional[Callable] = None,
        validation_error_status: int = 0,
        path_parameter_descriptions: Optional[Mapping[str, str]] = None,
        skip_validation: bool = False,
        operation_id: Optional[str] = None,
    ) -> Callable:
        """
        - validate query, json, headers in request
        - validate response body and status code
        - add tags to this API route

        :param operation_id:
        :param skip_validation:
        :param query: query in uri like `?name=value`
        :param json:  JSON format request body
        :param headers: if you have specific headers
        :param cookies: if you have cookies for this route
        :param resp: DocResponse object
        :param tags: a tuple of strings or :class:`spectree.models.Tag`
        :param security: dict with security config for current route and method
        :param deprecated: bool if endpoint is marked as deprecated
        :param before: :meth:`spectree.utils.default_before_handler` for
            specific endpoint
        :param after: :meth:`spectree.utils.default_after_handler` for
            specific endpoint
        :param validation_error_status: The response status code to use for the
            specific endpoint, in the event of a validation error. If not specified,
            the global `validation_error_status` is used instead, defined
            in :meth:`spectree.spec.SpecTree`.
        :param path_parameter_descriptions: A dictionary of path parameter names and
            their description.
        """
        if not validation_error_status:
            validation_error_status = self.validation_error_status

        resp_schema = resp.r if resp else None

        def lin_before(req, resp, req_validation_error, instance):
            g._resp_schema = resp_schema
            if before:
                before(req, resp, req_validation_error, instance)
            schemas = ["headers", "cookies", "query", "json"]
            for schema in schemas:
                params = getattr(req.context, schema)
                if params:
                    for k, v in params:
                        # 检测参数命名是否存在冲突，冲突则抛出要求重新命名的ParameterError
                        if hasattr(g, k) or hasattr(g, camel2line(k)):
                            raise ParameterError(
                                {k: f"This parameter in { schema.capitalize() } needs to be renamed"}
                            )  # type: ignore
                        # 将参数设置到g中，以便后续使用
                        setattr(g, k, v)
                        # 将参数设置到g中，同时将参数名转换为下划线格式
                        setattr(g, camel2line(k), v)

        def lin_after(req, resp, resp_validation_error, instance):
            # global after handler here
            if after:
                after(req, resp, resp_validation_error, instance)
            elif self.after:
                self.after(req, resp, resp_validation_error, instance)

        def decorate_validation(func):
            @wraps(func)
            def validation(*args, **kwargs):
                return self.backend.validate(
                    func,
                    query,
                    json,
                    form,
                    headers,
                    cookies,
                    resp,
                    lin_before,
                    lin_after,
                    validation_error_status,
                    skip_validation,
                    *args,
                    **kwargs,
                )

            has_annotations = False
            if self.config.annotations:
                nonlocal query, json, form, headers, cookies
                annotations = get_type_hints(func)
                query = annotations.get("query", query)
                json = annotations.get("json", json)
                form = annotations.get("form", form)
                headers = annotations.get("headers", headers)
                cookies = annotations.get("cookies", cookies)
                if annotations:
                    has_annotations = True

            # register
            for name, model in zip(
                ("query", "json", "form", "headers", "cookies"),
                (query, json, form, headers, cookies),
            ):
                if model is not None:
                    model_key = self._add_model(model=model)
                    setattr(validation, name, model_key)

            if resp:
                # Make sure that the endpoint specific status code and data model for
                # validation errors shows up in the response spec.
                # resp.add_model(
                #     validation_error_status, self.validation_error_model, replace=False
                # )
                if has_annotations:
                    resp.add_model(validation_error_status, ValidationError, replace=False)
                for model in resp.models:
                    self._add_model(model=model)
                validation.resp = resp

            if tags:
                validation.tags = tags

            validation.security = security
            validation.deprecated = deprecated
            validation.path_parameter_descriptions = path_parameter_descriptions
            validation.operation_id = operation_id
            # register decorator
            validation._decorator = self
            return validation

        return decorate_validation


def schema_response(app: Flask):
    """
    根据apidoc中指定的r schema，重新生成对应类型的响应
    """

    @app.after_request
    def make_schema_response(response):
        res = response
        if hasattr(g, "_resp_schema") and g._resp_schema and response.status_code == 200:
            data, _code, _headers = response.get_json()
            res = make_response(jsonify(g._resp_schema.parse_obj(data)))
        return res


class DocResponse(Response):
    """
    response object

    :param args: subclass/object of APIException or obj/dict with code message_code message or None
    """

    def __init__(
        self,
        *args: Any,
        r=None,
    ) -> None:
        # 初始化 self
        self.codes = []  # 重写功能后此属性无用，只是防止报错
        self.code_models: Dict[str, ModelType] = {}
        self.code_descriptions: Dict[str, Optional[str]] = {}
        self.code_list_item_types: Dict[str, ModelType] = {}

        # 将 args 转换后存入code_models
        for arg in args:
            assert "HTTP_" + str(arg.code) in DEFAULT_CODE_DESC, "invalid HTTP status code"
            name = arg.__class__.__name__
            schema_name = "{class_name}_{message_code}_{hashmsg}Schema".format(
                class_name=name,
                message_code=arg.message_code,
                hashmsg=hash(arg.message),
            )
            # 通过 name, schema_name, arg(包含code:int, 和message:str 两个属性) 生成一个新的BaseModel子类, 并存入code_models
            self.code_models["HTTP_" + str(arg.code)] = type(
                schema_name,
                (BaseModel,),
                {"__annotations__": {"code": int, "message": str}, "code": arg.message_code, "message": arg.message},
            )
        # 将 r 转换后存入code_models
        if r:
            http_status = "HTTP_200"
            if r.__class__.__name__ == "ModelMetaclass":
                self.code_models[http_status] = r
            elif isinstance(r, dict):
                response_str = json.dumps(r, cls=current_app.json_encoder)
                r = type("Dict-{}Schema".format(hash(response_str)), (BaseModel,), r)
                self.code_models[http_status] = r
            elif isinstance(r, (RecordCollection, Record)) or (hasattr(r, "keys") and hasattr(r, "__getitem__")):
                r_str = json.dumps(r, cls=current_app.json_encoder)
                r = json.loads(r_str)
                r = type("Json{}Schema".format(hash(r_str)), (BaseModel,), r)
                self.code_models[http_status] = r
        self.r = r
