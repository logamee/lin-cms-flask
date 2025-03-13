FROM python:3.13
# 拷贝依赖
COPY requirements.txt .
# 安装依赖
# RUN pip install -r requirements-prod.txt >/dev/null 2>&1
RUN pip install -r requirements-prod.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com
# 拷贝项目
COPY . /app
