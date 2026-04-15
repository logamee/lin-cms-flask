"""
:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

import pytest

from . import app, fixtureFunc, get_token


@pytest.mark.run(order=1)
def test_create(fixtureFunc):
    with app.test_client() as c:
        rv = c.post(
            "/v1/book",
            headers={"Authorization": "Bearer " + get_token()},
            json={
                "title": "create",
                "author": "pedro",
                "summary": "summary",
                "image": "https://img3.doubanio.com/lpic/s1470003.jpg",
            },
        )
        assert rv.status_code == 200 or rv.get_json().get("code") == 10030


@pytest.mark.run(order=2)
def test_get_books():
    with app.test_client() as c:
        rv = c.get("/v1/book", headers={"Authorization": "Bearer "})
        assert rv.status_code == 200


@pytest.mark.run(order=3)
def test_update(fixtureFunc):
    with app.test_client() as c:
        id = c.get("/v1/book", headers={"Authorization": "Bearer "}).get_json()[-1].get("id")
        rv = c.put(
            "/v1/book/{}".format(id),
            headers={"Authorization": "Bearer " + get_token()},
            json={
                "title": "update",
                "author": "pedro & erik",
                "summary": "summary",
                "image": "https://img3.doubanio.com/lpic/s1470003.jpg",
            },
        )
        assert rv.status_code == 200


@pytest.mark.run(order=4)
def test_delete():
    with app.test_client() as c:
        id = c.get("/v1/book", headers={"Authorization": "Bearer "}).get_json()[-1].get("id")
        rv = c.delete("/v1/book/{}".format(id), headers={"Authorization": "Bearer " + get_token()})
        assert rv.status_code == 200


@pytest.mark.run(order=5)
def test_get_books_openapi_response_schema():
    with app.test_client() as c:
        rv = c.get("/apidoc/openapi.json")
        assert rv.status_code == 200

        data = rv.get_json()
        schema_ref = data["paths"]["/v1/book"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
        schema_name = schema_ref.split("/")[-1]
        schema = data["components"]["schemas"][schema_name]

        assert schema["type"] == "array"
        assert "$ref" in schema["items"]


def test_create_book_openapi_message_schema():
    with app.test_client() as c:
        rv = c.get("/apidoc/openapi.json")
        assert rv.status_code == 200

        data = rv.get_json()
        schema_ref = data["paths"]["/v1/book"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
        schema_name = schema_ref.split("/")[-1]
        schema = data["components"]["schemas"][schema_name]

        assert schema_name.startswith("ApiMessageSchema")
        assert set(schema["properties"]) == {"code", "message", "request"}
