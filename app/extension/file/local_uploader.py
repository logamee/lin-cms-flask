import os
from typing import Any, Dict, List

from flask import current_app, request

from app.lin import Uploader

from .file import File


class LocalUploader(Uploader):
    def upload(self, **kwargs: Any) -> List[Dict[str, Any]]:
        ret: List[Dict[str, Any]] = []
        self.mkdir_if_not_exists()
        static_url_path = current_app.static_url_path or ""
        # 优先显式配置 SITE_DOMAIN；未配置时用当前请求主机，避免反代后拼出错误 URL
        site_domain = current_app.config.get("SITE_DOMAIN") or request.host_url.rstrip("/")
        for single in self._file_storage:
            filename = single.filename or ""
            file_md5 = self._generate_md5(single.read())
            single.seek(0)
            exists = File.select_by_md5(file_md5)
            if exists:
                ret.append(
                    {
                        "key": single.name,
                        "id": exists.id,
                        "path": exists.path,
                        "url": site_domain + os.path.join(static_url_path, exists.path),
                    }
                )
            else:
                absolute_path, relative_path, real_name = self._get_store_path(filename)
                single.save(absolute_path)
                file = File.create_file(
                    name=real_name,
                    path=relative_path,
                    extension=self._get_ext(filename),
                    size=self._get_size(single),
                    md5=file_md5,
                    commit=True,
                )
                ret.append(
                    {
                        "key": single.name,
                        "id": file.id,
                        "path": file.path,
                        "url": site_domain + os.path.join(static_url_path, file.path),
                    }
                )
        return ret
