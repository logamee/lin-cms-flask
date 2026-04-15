FROM python:3.14

WORKDIR /app

# 拷贝依赖
COPY requirements.txt /app/requirements.txt

# 安装依赖
RUN pip install --no-cache-dir -r /app/requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com

# 拷贝项目
COPY . /app
