"""已吊销令牌黑名单：logout 时按 jti 精确吊销单个令牌。"""

from datetime import datetime

from app.lin import InfoCrud, db


class TokenBlocklist(InfoCrud):
    __tablename__ = "lin_token_blocklist"

    id = db.Column(db.Integer(), primary_key=True)
    jti = db.Column(db.String(64), nullable=False, unique=True, index=True, comment="令牌唯一标识")
    user_id = db.Column(db.Integer(), nullable=True, comment="吊销发起用户，便于审计")
    expires_at = db.Column(db.DateTime(), nullable=False, comment="令牌自然过期时间，过期后可清理")

    @classmethod
    def revoke(cls, jti: str, expires_at: datetime, user_id: int = 0) -> None:
        """吊销令牌并顺带清理已过期的黑名单条目。"""
        if cls.query.filter_by(jti=jti).first() is not None:
            return
        entry = cls(jti=jti, expires_at=expires_at, user_id=user_id)
        db.session.add(entry)
        cls.prune_expired()
        db.session.commit()

    @classmethod
    def prune_expired(cls) -> int:
        now = datetime.now()
        return cls.query.filter(cls.expires_at < now).delete(synchronize_session=False)

    @classmethod
    def is_revoked(cls, jti: str) -> bool:
        return cls.query.filter_by(jti=jti).first() is not None
