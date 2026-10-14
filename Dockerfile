FROM python:3.14

WORKDIR /app

# 先拷贝项目（requirements.txt 含 `-e .`，需要包源码在场才能安装）
COPY pyproject.toml README.md LICENSE ./
COPY app ./app
COPY starter.py ./
COPY migrations ./migrations
COPY requirements.txt ./
COPY docker-deploy.sh ./
COPY gunicorn.conf.py ./

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 生产环境标识由 docker-deploy.sh 在启动时写入 .flaskenv
ENV FLASK_ENV=production

# 非 root 运行
RUN useradd -m -u 1000 lincms && mkdir -p /app/logs /app/assets && chown -R lincms:lincms /app
USER lincms

EXPOSE 5000

CMD ["sh", "docker-deploy.sh"]
