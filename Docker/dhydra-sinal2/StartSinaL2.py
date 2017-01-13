# coding: utf-8
from dHydra.main import start_worker

start_worker(
    worker_name="SinaL2",
    nickname="SinaL2",
    config="SinaL2.json"
)
# nickname="SinaL2"是指定一个全局唯一的名字，当已有一个nickname=="SinaL2"的进程开启时，dHydra不会允许第二个进程启动
# config这里如果不是绝对了路径，那么如果填写"SinaL2.json"对应的会是"/dHydra/config/SinaL2.json"
# 帐号文件的路径是在`SinaL2.json`中设置的