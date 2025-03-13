"""
:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

from .controller import api
from .model import Poem


def initial_data():
    from app import create_app
    from app.lin import db

    app = create_app()
    with app.app_context():
        data = Poem.query.limit(1).all()
        if data:
            return
        with db.auto_commit():
            # 添加诗歌
            img_url = "http://yanlan.oss-cn-shenzhen.aliyuncs.com/gqmgbmu06yO2zHD.png"
            poem1 = Poem()
            poem1.title = "生查子·元夕"
            poem1.author = "欧阳修"
            poem1.dynasty = "宋代"
            poem1._content = (
                """去年元夜时/花市灯如昼/月上柳梢头/人约黄昏后|今年元夜时/月与灯依旧/不见去年人/泪湿春衫袖"""
            )
            poem1.image = img_url
            db.session.add(poem1)

            poem2 = Poem()
            poem2.title = "临江仙·送钱穆父"
            poem2.author = "苏轼"
            poem2.dynasty = "宋代"
            poem2._content = """一别都门三改火/天涯踏尽红尘/依然一笑作春温/无波真古井/有节是秋筠|惆怅孤帆连夜发/送行淡月微云/尊前不用翠眉颦/人生如逆旅/我亦是行人"""
            poem2.image = img_url
            db.session.add(poem2)

            poem3 = Poem()
            poem3.title = "春望词四首"
            poem3.author = "薛涛"
            poem3.dynasty = "唐代"
            poem3._content = """花开不同赏/花落不同悲/欲问相思处/花开花落时/揽草结同心/将以遗知音/春愁正断绝/春鸟复哀吟/风花日将老/佳期犹渺渺/不结同心人/空结同心草/那堪花满枝/翻作两相思/玉箸垂朝镜/春风知不知"""
            poem3.image = img_url
            db.session.add(poem3)

            poem4 = Poem()
            poem4.title = "长相思"
            poem4.author = "纳兰性德"
            poem4.dynasty = "清代"
            poem4._content = """山一程/水一程/身向榆关那畔行/夜深千帐灯|风一更/雪一更/聒碎乡心梦不成/故园无此声"""
            poem4.image = img_url
            db.session.add(poem4)

            poem5 = Poem()
            poem5.title = "离思五首·其四"
            poem5.author = "元稹"
            poem5.dynasty = "唐代"
            poem5._content = """曾经沧海难为水/除却巫山不是云/取次花丛懒回顾/半缘修道半缘君"""
            poem5.image = img_url
            db.session.add(poem5)

            poem6 = Poem()
            poem6.title = "浣溪沙"
            poem6.author = "晏殊"
            poem6.dynasty = "宋代"
            poem6._content = (
                """一曲新词酒一杯/去年天气旧亭台/夕阳西下几时回|无可奈何花落去/似曾相识燕归来/小园香径独徘徊"""
            )
            poem6.image = img_url
            db.session.add(poem6)

            poem7 = Poem()
            poem7.title = "浣溪沙"
            poem7.author = "纳兰性德"
            poem7.dynasty = "清代"
            poem7._content = (
                """残雪凝辉冷画屏/落梅横笛已三更/更无人处月胧明|我是人间惆怅客/知君何事泪纵横/断肠声里忆平生"""
            )
            poem7.image = img_url
            db.session.add(poem7)

            poem8 = Poem()
            poem8.title = "蝶恋花·春景"
            poem8.author = "苏轼"
            poem8.dynasty = "宋代"
            poem8._content = """花褪残红青杏小/燕子飞时/绿水人家绕/枝上柳绵吹又少/天涯何处无芳草|墙里秋千墙外道/墙外行人/墙里佳人笑/笑渐不闻声渐悄/多情却被无情恼"""
            poem8.image = img_url
            db.session.add(poem8)

    return app
