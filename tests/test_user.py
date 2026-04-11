"""
:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

from . import app, fixtureFunc, get_token  # type: ignore


def test_change_nickname(fixtureFunc):
    with app.test_client() as c:
        rv = c.put(
            "/cms/user",
            headers={"Authorization": "Bearer " + get_token()},
            json={"nickname": "tester"},
        )
        assert rv.status_code == 200


def test_refresh_token(fixtureFunc):
    with app.test_client() as c:
        rv = c.get(
            "/cms/user/refresh",
            headers={"Authorization": "Bearer " + get_token('refresh_token')},
        )
        json_data = rv.get_json()
        assert rv.status_code == 200
        assert json_data.get("access_token") is not None
        assert json_data.get("refresh_token") is not None
