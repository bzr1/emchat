# -*- coding: utf-8 -*-
import os
from os import path
import datetime

MAX_REINPUT_CNT = 3
API_ROOT = os.path.join(os.getcwd(), "..", "AIOpsAPI")
# openai 配置
OPENAI_KEY1 = "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"  #最新买的
OPENAI_KEY2 = "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"  #status0
OPENAI_KEY3 = "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"

OPENAI_API_KEY_X3 = "sk-HvgKIr96iGxCN3Py21A57a75377746818666392612310cD1"  #最新买status3
OPENAI_API_KEY_X2 = "sk-3Brw0t9tmLv7dJCW57077b1653244614B3376dF908Cf5521"  #最新买embed
OPENAI_API_KEY_X = "sk-LksFKgMrQ5xxv5O9316a486cD7E14653897d9306F715F51b"  #最新买加base status1
OPENAI_API_BASE_X = "https://d2.xiamoai.top/v1"

OPENAI_API_KEY = "sk-yQbK8TNEa2cnoSsd02F7948a50274bC8B95dAb09EcC3A4Bd"
OPENAI_API_BASE = "https://d2.xiamoai.top/v1"



# QW
OPENAI_API_BASE_QW = "http://localhost:8000/v1"
OPENAI_API_KEY_QW = "none"
# MODEL_NAME="chatglm3-6b"
MODEL_NAME="qianwen-14b"

THRE_DIS =  0.9
STATUS_SQL = ['0','5','8','11','33']
STATUS_API = [2,4,6,7]
ID_DOC_LIST = ['id15','id16','id17','id18','id19','id20','id21','id22']


# 退服预测api配置
OPS_PREDICT_API_URL = "http://127.0.0.1:9999/api/v1/networkintelligent/oosPred"
# DEFAULT_ALARM_FILE_FOLDER = "D:\\projects\\AIOps_pre_API\\data\\input\\liaoning\\alarm\\wuxian-default"
PREDICT_ALARM_FILE_FOLDER = os.path.join(API_ROOT, "data", "oosPred", "input/liaoning/alarm/wuxian")
# PREDICT_ALARM_FILE_FOLDER = r"/app/AIOps_API/data/AIOps_pre/input/liaoning/alarm/wuxian"
DEFAULT_TARGET_DATE = "2022-11-13"
DEFAULT_HISTORY_DAYS = 7
MAX_REINPUT_CNT = 3

# 根因分析api配置
OPS_RCA_API_URL = "http://127.0.0.1:9999/api/v1/networkintelligent/rcaPred"
RCA_ALARM_FILE_PATH = os.path.join(API_ROOT, "data", "rcaPred", "input/测试告警.csv")
RCA_ORDER_FILE_PATH = os.path.join(API_ROOT, "data", "rcaPred", "input/测试故障工单.csv")
# RCA_ALARM_FILE_PATH = r"/app/AIOps_API/data/rca/input/测试告警.csv"
# RCA_ORDER_FILE_PATH = r"/app/AIOps_API/data/AIOps_rca/input/测试故障工单.csv"

# 网络优化api配置
PERFORMANCE_OPTIM_API_URL = "http://127.0.0.1:9999/api/v1/networkintelligent/optimPred"

# 流量预测api配置
TRAFFIC_PREDICT_API_URL = "http://127.0.0.1:9999/api/v1/networkintelligent/trafficPred"
HISTORY_WINDOW = 3*24
FORECAST_WINDOW = 12
PREFIX = '!'

# sql 数据库配置
DATABASE_USER = ""
DATABASE_NAME = ""
DATABASE_USERNAME = ""
DATABASE_PASSWORD = ""
DATABASE_URL = f"postgresql+psycopg2://postgres:llm123456@localhost:5432/llm"
DATABASE_URL_X =  f"postgresql+psycopg2://llm:llm123456@127.0.0.1:5432/llm"
#DATABASE_URL = f"postgresql+psycopg2://llm2:llm123456@127.0.0.1:5433/llm2"
#DATABASE_URL_X =  f"postgresql+psycopg2://llm2:llm123456@127.0.0.1:5433/llm2"

# 日志配置
OUTPUT_PATH = path.join(path.curdir, 'logs', 'outputs')
