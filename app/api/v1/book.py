"""
a standard CRUD template of book
通过 图书 来实现一套标准的 CRUD 功能，供学习
:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

from flask import Blueprint

from app.api import AuthorizationBearerSecurity, api
from app.api.v1.exception import BookNotFound
from app.api.v1.model.book import Book
from app.api.v1.schema import BookInSchema, BookOutSchema, BookQuerySearchSchema, BookSchemaList
from app.lin import DocResponse, Success, group_required, login_required, permission_meta

book_api = Blueprint("book", __name__)


@book_api.route("/<int:id>")
@api.validate(
    resp=DocResponse(BookNotFound, r=BookOutSchema),
    tags=["图书"],
)
def get_book(id):
    """
    获取id指定图书的信息
    """
    book = Book.get(id=id)
    if book:
        return book
    raise BookNotFound


@book_api.route("")
@api.validate(
    resp=DocResponse(r=BookSchemaList),
    tags=["图书"],
)
def get_books():
    """
    获取图书列表
    """
    return Book.get(one=False)


@book_api.route("/search")
@api.validate(
    resp=DocResponse(r=BookSchemaList),
    tags=["图书"],
)
def search(query: BookQuerySearchSchema):
    """
    关键字搜索图书
    """
    return Book.query.filter(Book.title.like("%" + query.q + "%"), Book.is_deleted == False).all()


@book_api.route("", methods=["POST"])
@login_required
@api.validate(
    resp=DocResponse(Success(12)),
    security=[AuthorizationBearerSecurity],
    tags=["图书"],
)
def create_book(json: BookInSchema):
    """
    创建图书
    """
    Book.create(**json.model_dump(), commit=True)
    raise Success(12)


@book_api.route("/<int:id>", methods=["PUT"])
@login_required
@api.validate(
    resp=DocResponse(Success(13)),
    security=[AuthorizationBearerSecurity],
    tags=["图书"],
)
def update_book(id, json: BookInSchema):
    """
    更新图书信息
    """
    book = Book.get(id=id)
    if book:
        book.update(
            id=id,
            **json.model_dump(),
            commit=True,
        )
        raise Success(13)
    raise BookNotFound


@book_api.route("/<int:id>", methods=["DELETE"])
@permission_meta(name="删除图书", module="图书")
@group_required
@api.validate(
    resp=DocResponse(BookNotFound, Success(14)),
    security=[AuthorizationBearerSecurity],
    tags=["图书"],
)
def delete_book(id):
    """
    传入id删除对应图书
    """
    book = Book.get(id=id)
    if book:
        # 删除图书，软删除
        book.delete(commit=True)
        raise Success(14)
    raise BookNotFound
