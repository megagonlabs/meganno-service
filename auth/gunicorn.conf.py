import multiprocessing
import os

capture_output = True
accesslog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(p)s'
errorlog = "-"
# min 2 cores, cpu_count() = # of cores * 2
workers = min(multiprocessing.cpu_count(), 4) + 1
MEGANNO_AUTH_PORT = os.getenv("MEGANNO_AUTH_PORT", 5001)
bind = [f"0.0.0.0:{MEGANNO_AUTH_PORT}", "0.0.0.0:43259"]
preload_app = True
