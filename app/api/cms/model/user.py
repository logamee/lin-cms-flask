from sqlalchemy import func

from app.lin import User as LinUser
from app.lin import db, manager


class User(LinUser):
    def _set_fields(self):
        self._exclude = ["delete_time", "create_time", "is_deleted", "update_time"]

    @classmethod
    def count_by_username(cls, username) -> int:
        result = db.session.query(func.count(cls.id)).filter(cls.username == username, cls.is_deleted == False)
        count = result.scalar()
        return count

    @classmethod
    def count_by_email(cls, email) -> int:
        result = db.session.query(func.count(cls.id)).filter(cls.email == email, cls.is_deleted == False)
        count = result.scalar()
        return count

    @classmethod
    def select_page_by_group_id(cls, group_id, root_group_id) -> list:
        """通过分组id分页获取用户数据"""
        query = db.session.query(manager.user_group_model.user_id).filter(
            manager.user_group_model.group_id == group_id,
            manager.user_group_model.group_id != root_group_id,
        )
        result = cls.query.filter_by(soft=True).filter(cls.id.in_(query))
        users = result.all()
        return users

    def reset_password(self, new_password):
        self.password = new_password

    def change_password(self, old_password, new_password):
        if self.check_password(old_password):
            self.password = new_password
            return True
        return False
