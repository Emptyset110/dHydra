# coding: utf-8
from dHydra.main import start_worker

start_worker(
    worker_name="CtpMd",
    nickname="CtpMd",
    config="CtpMd.json"
)
# nickname="CtpMd"是指定一个全局唯一的名字，当已有一个nickname=="CtpMd"的进程开启时，dHydra不会允许第二个进程启动
# config这里如果不是绝对了路径，那么如果填写"CtpMd.json"对应的会是"/dHydra/config/CtpMd.json"