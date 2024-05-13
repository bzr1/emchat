# -*- coding: utf-8 -*-
from os import path
import datetime
# openai 配置
OPENAI_API_KEY = "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"
OPENAI_API_BASE = "https://api-hk.88api.top/v1"

# 退服预测api配置
OPS_PREDICT_API_URL = "http://127.0.0.1:8888/api/v1/networkintelligent/oosPred"
DEFAULT_ALARM_FILE_FOLDER = "D:\\projects\\AIOps_pre_API\\data\\input\\liaoning\\alarm\\wuxian-default"
PREDICT_ALARM_FILE_FOLDER = "D:\\projects\\AIOps_pre_API\\data\\input\\liaoning\\alarm\\wuxian"
DEFAULT_TARGET_DATE = datetime.datetime.now().strftime("%Y-%m-%d")
# print("default target date is", DEFAULT_TARGET_DATE)
DEFAULT_HISTORY_DAYS = 7
MAX_REINPUT_CNT = 3

# 根因分析api配置
OPS_RCA_API_URL = "http://127.0.0.1:9999/api/v1/networkintelligent/rcaPred"
RCA_ALARM_FILE_PATH = "D:\projects\AIOps_API\data\AIOps_rca\input\测试告警.csv"
RCA_ORDER_FILE_PATH = "D:\projects\AIOps_API\data\AIOps_rca\input\测试故障工单.csv"

# sql 数据库配置
DATABASE_USER = ""
DATABASE_NAME = ""
DATABASE_USERNAME = ""
DATABASE_PASSWORD = ""
DATABASE_URL = f"postgresql+psycopg2://postgres:123456@localhost:5432/llm"

# 日志配置
OUTPUT_PATH = path.join(path.curdir, 'logs', 'outputs')