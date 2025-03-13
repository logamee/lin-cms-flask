from sqlalchemy import Column, Index, Integer, String, func, text

from app.lin import InfoCrud, db


class File(InfoCrud):
    __tablename__ = "lin_file"
    __table_args__ = (Index("md5_del", "md5", "delete_time", unique=True),)

    id = Column(Integer(), primary_key=True)
    path = Column(String(500), nullable=False)
    type = Column(
        String(10),
        nullable=False,
        server_default=text("'LOCAL'"),
        comment="LOCAL 本地，REMOTE 远程",
    )
    name = Column(String(100), nullable=False)
    extension = Column(String(50))
    size = Column(Integer())
    md5 = Column(String(40), comment="md5值，防止上传重复文件")

    @classmethod
    def select_by_md5(cls, md5):
        result = cls.query.filter_by(soft=True, md5=md5)
        file = result.first()
        return file

    @classmethod
    def count_by_md5(cls, md5):
        result = db.session.query(func.count(cls.id)).filter(cls.is_deleted == False, cls.md5 == md5)
        count = result.scalar()
        return count

    @staticmethod
    def create_file(**kwargs):
        file = File()
        for key in kwargs.keys():
            if hasattr(file, key):
                setattr(file, key, kwargs[key])
        db.session.add(file)
        if kwargs.get("commit") is True:
            db.session.commit()
        return file
