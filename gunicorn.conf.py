import multiprocessing

# 注意：gevent worker 会自行执行 monkey.patch_all()，此处无需（也不应）手动 patch

bind = "0.0.0.0:5000"
worker_class = "gevent"
daemon = False
workers = min(multiprocessing.cpu_count() * 2 + 1, 9)

# 慢请求兜底：超时杀掉 worker，避免长连接/挂死请求耗尽进程
timeout = 30
graceful_timeout = 30
keepalive = 5

# worker 定期回收，缓解潜在内存泄漏
max_requests = 1000
max_requests_jitter = 100

# 日志走标准输出，容器/编排平台统一收集
accesslog = "-"
errorlog = "-"
