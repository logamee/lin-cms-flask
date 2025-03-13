import os

from flask import current_app
from werkzeug.utils import secure_filename

from app.lin import Uploader

from .file import File


class LocalUploader(Uploader):
    def upload(self):
        ret = []
        self.mkdir_if_not_exists()
        site_domain = current_app.config.get(
            "SITE_DOMAIN",
            "http://{host}:{port}".format(
                host=current_app.config.get("FLASK_RUN_HOST", "127.0.0.1"),
                port=current_app.config.get("FLASK_RUN_PORT", "5000"),
            ),
        )
        for single in self._file_storage:
            file_md5 = self._generate_md5(single.read())
            single.seek(0)
            exists = File.select_by_md5(file_md5)
            if exists:
                ret.append(
                    {
                        "key": single.name,
                        "id": exists.id,
                        "path": exists.path,
                        "url": site_domain + os.path.join(current_app.static_url_path, exists.path),
                    }
                )
            else:
                absolute_path, relative_path, real_name = self._get_store_path(single.filename)
                secure_filename(single.filename)
                single.save(absolute_path)
                file = File.create_file(
                    name=real_name,
                    path=relative_path,
                    extension=self._get_ext(single.filename),
                    size=self._get_size(single),
                    md5=file_md5,
                    commit=True,
                )
                ret.append(
                    {
                        "key": single.name,
                        "id": file.id,
                        "path": file.path,
                        "url": site_domain + os.path.join(current_app.static_url_path, file.path),
                    }
                )
        return ret
