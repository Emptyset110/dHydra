# -*- coding: utf-8 -*-
"""
# Created on
# @author:
# @contact:
"""
# 以下是自动生成的 #
# --- 导入系统配置
import dHydra.core.util as util
from dHydra.core.Vendor import Vendor
# --- 导入自定义配置
# 以上是自动生成的 #
from datetime import datetime, timedelta
from pymongo import MongoClient
from dHydra.core.Functions import get_vendor
import copy


class WorkerManager(Vendor):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.redis = get_vendor("DB").get_redis()
        self.worker_names = list()
        self.worker_info = dict()
        self.updating = False
        if "auto_remove_terminated" in kwargs:
            self.auto_remove_terminated = kwargs["auto_remove_terminated"]
        else:
            self.auto_remove_terminated = -1
        # -1: never;
        # otherwise: auto remove terminated workers
        # after (self.auto_remove_terminated) seconds

    def get_worker_names(self):
        worker_names = util.get_worker_names(logger=self.logger)
        return worker_names

    def get_workers_from_redis(self):
        keys = self.redis.keys("dHydra.Worker.*.*.Info")
        workers = dict()
        for i in range(0, len(keys)):
            channel = keys[i]
            parsed_channel = channel.split('.')
            if (len(parsed_channel) == 5) and (parsed_channel[4] == "Info") \
                    and (parsed_channel[0] == 'dHydra') \
                    and (parsed_channel[1] == 'Worker'):
                if parsed_channel[2] not in workers:
                    workers[parsed_channel[2]] = dict()
                worker = self.redis.hgetall(keys[i])
                workers[parsed_channel[2]][parsed_channel[3]] = worker
        return workers

    def update_workers(self):
        """
        更新Worker信息
        :return:
        """
        self.updating = True
        # 根据文件目录检索
        self.worker_names = self.get_worker_names()

        # 从redis中获取worker信息并更新
        worker_info = self.get_workers_from_redis()

        # 去除掉过期信息
        for worker_name, workers in worker_info.items():
            if worker_name not in self.worker_info:
                self.worker_info[worker_name] = dict()
            for nickname, worker_info in workers.items():
                heart_beat_interval = 1
                if "heart_beat_interval" in worker_info:
                    heart_beat_interval = int(worker_info["heart_beat_interval"])
                difference = datetime.now() -\
                    datetime.strptime(
                        worker_info["heart_beat"],
                        '%Y-%m-%d %H:%M:%S.%f'
                    )
                if difference > timedelta(seconds=heart_beat_interval+1):
                    # 已经停止
                    if worker_info["status"] == "started":
                        worker_info["status"] = "disappeared"
                        self.logger.warning(
                            "发现一个没有正常关闭的Worker:\n"
                            "\tworker_name: {}\n"
                            "\tnickname: {}"
                            .format(worker_name, nickname)
                        )
                    self.worker_info[worker_name][nickname] = copy.deepcopy(worker_info)
                if self.auto_remove_terminated > -1 and\
                        difference>timedelta(seconds=self.auto_remove_terminated+1):
                    if "token" in worker_info:
                        token = worker_info["token"]
                    else:
                        token = None
                    removed = self.remove_worker(
                        worker_name=worker_name,
                        nickname=nickname,
                        token=token
                    )
                    if removed == 1:
                        self.logger.info(
                            "从redis中自动移除过期Worker:\n"
                            "\tworker_name:{}\n"
                            "\tnickname:{}\n"
                            "\ttoken:{}\n"
                            .format(worker_name,nickname,token)
                        )
                    else:
                        self.logger.warning(
                            "从redis中自动移除过期Worker:{}\n"
                            "\tworker_name:{}\n"
                            "\tnickname:{}\n"
                            "\ttoken:{}\n"
                            .format(
                                removed,
                                worker_name,
                                nickname,
                                token
                            )
                        )

        self.updating = False

    def remove_worker(
        self,
        worker_name,
        nickname,
        token
    ):
        key = "dHydra.Worker."+worker_name+"."+nickname+"."+"Info"
        worker_info = self.redis.hgetall(key)
        if "token" in worker_info:
            if worker_info["token"] == token:
                return self.redis.delete(key)
        else:
            if token is None:
                return self.redis.delete(key)
        return 0