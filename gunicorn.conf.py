import multiprocessing

from gevent import monkey

monkey.patch_all()


bind = "0.0.0.0:5000"
worker_class = "gevent"
daemon = False
workers = multiprocessing.cpu_count() * 2 + 1
debug = False
# pidfile = "/var/run/gunicorn.pid"
# accesslog = "/var/log/gunicorn.log"
