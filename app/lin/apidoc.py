import hashlib
from functools import wraps
from json import dumps
from typing import *

from pydantic import BaseModel as _BaseModel
from pydantic import ConfigDict
from spectree import SpecTree as _SpecTree
from spectree._types import ModelType
from spectree.response import DEFAULT_CODE_DESC, Response

from .db import Record, RecordCollection


class ValidationError(_BaseModel):
    message: str = "parameter validation error message"
    code: int = 10030


class BaseModel(_BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ApiMessageSchema(BaseModel):
    code: int
    message: Any
    request: str

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
        force_resp_serialize: bool = True,
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

        def lin_before(req, resp, req_validation_error, instance):
            if before:
                before(req, resp, req_validation_error, instance)

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
                    force_resp_serialize,
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


def _json_default(value: Any) -> Any:
    if isinstance(value, _BaseModel):
        return value.model_dump()
    if isinstance(value, (RecordCollection, Record)):
        return value.as_dict()
    if isinstance(value, (set, tuple)):
        return list(value)
    if hasattr(value, "keys") and hasattr(value, "__getitem__"):
        return dict(value)
    return str(value)


def _fingerprint(value: Any) -> str:
    payload = dumps(value, default=_json_default, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


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
            http_status = "HTTP_" + str(arg.code)
            self.code_models[http_status] = ApiMessageSchema
            if isinstance(arg.message, str):
                self.code_descriptions[http_status] = arg.message
        # 将 r 转换后存入code_models
        if r:
            http_status = "HTTP_200"
            if isinstance(r, type) and issubclass(r, _BaseModel):
                self.code_models[http_status] = r
            elif isinstance(r, dict):
                r = type(f"Dict_{_fingerprint(r)}Schema", (BaseModel,), r)
                self.code_models[http_status] = r
            elif isinstance(r, (RecordCollection, Record)) or (hasattr(r, "keys") and hasattr(r, "__getitem__")):
                payload = _json_default(r)
                r = type(f"Json_{_fingerprint(payload)}Schema", (BaseModel,), payload)
                self.code_models[http_status] = r
        self.r = r
