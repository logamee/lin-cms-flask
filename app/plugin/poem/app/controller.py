from flask import jsonify

from app.lin import Redprint
from app.plugin.poem.app.form import PoemListForm, PoemSearchForm

from .model import Poem

api = Redprint("poem")


@api.route("/all")
def get_list():
    form = PoemListForm().validate_for_api()
    poems = Poem().get_all(form)
    return jsonify(poems)


@api.route("/search")
def search():
    form = PoemSearchForm().validate_for_api()
    poems = Poem().search(form.q.data)
    return jsonify(poems)


@api.route("/authors")
def get_authors():
    authors = Poem.get_authors()
    return jsonify(authors)
