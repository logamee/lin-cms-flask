"""
:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

from app import create_app
from app.api.cms.model.group import Group
from app.api.cms.model.group_permission import GroupPermission
from app.api.cms.model.permission import Permission
from app.api.cms.model.user import User
from app.api.cms.model.user_group import UserGroup
from app.api.cms.model.user_identity import UserIdentity
from app.api.v1.model.book import Book
from app.config.code_message import MESSAGE

app = create_app(
    group_model=Group,
    user_model=User,
    group_permission_model=GroupPermission,
    permission_model=Permission,
    identity_model=UserIdentity,
    user_group_model=UserGroup,
    config_MESSAGE=MESSAGE,
)


@app.route("/hello")
def hello():
    return Book.get(one=True)


if app.config.get("ENV") != "production":

    @app.route("/")
    def slogan():
        return """
        <style type="text/css">
            * {
                padding: 0;
                margin: 0;
            }

            div {
                padding: 4px 48px;
            }

            a {
                color: black;
                cursor: pointer;
                text-decoration: none
            }

            a:hover {
                text-decoration: None;
            }

            body {
                background: #fff;
                font-family:
                    "Century Gothic", "Microsoft yahei";
                color: #333;
                font-size: 18px;
            }

            h1 {
                font-size: 100px;
                font-weight: normal;
                margin-bottom: 12px;
            }

            p {
                line-height: 1.6em;
                font-size: 42px
            }
        </style>
        <div style="padding: 24px 48px;">
            <p>
                <a href="https://www.talelin.com" target="_Blank">Lin</a>
                <br />
                <span style="font-size:30px">
                    <a href="/apidoc/redoc">心上无垢</a>，<a href="/apidoc/swagger">林间有风</a>。
                </span>
            </p>
        </div>
        """


if __name__ == "__main__":
    app.logger.warning(
        """
        ----------------------------
        |  app.run() => flask run  |
        ----------------------------
        """
    )
    app.run()
