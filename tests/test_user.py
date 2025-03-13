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
