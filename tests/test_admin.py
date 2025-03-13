"""
:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

from . import app, fixtureFunc, get_token


def test_permission(fixtureFunc):
    with app.test_client() as c:
        rv = c.get(
            "/cms/admin/permission",
            headers={"Authorization": "Bearer " + get_token()},
        )
        assert rv.status_code == 200


def test_get_root_users(fixtureFunc):
    with app.test_client() as c:
        rv = c.get("/cms/admin/users", headers={"Authorization": "Bearer " + get_token()})
        assert rv.status_code == 200
