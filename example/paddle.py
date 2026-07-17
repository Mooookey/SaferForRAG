import paddle
import paddlenlp
from paddlenlp import Taskflow
from typing import Dict,List
# print(paddle.__version__, paddlenlp.__version__)

schema_zh:List[str]={
    "电话号码",
    "传真号码",
    "邮政编码",
}
schema_lang="zh"
schema_en:List[str]={
    "PHONE_NUMBER":[],
    "FAX_NUMBER":[],
    "POSTAL_CODE":[],
}
schema_lang="en",
schema_medical:List[str]={
    "疾病",
    "症状",
    "药物",
    "检查项目",
    "治疗方法",
    "医生",
}





# 定义抽取Schema
my_schema:Dict[str,List[str]] = {
    "疾病": [],  # 疾病是一个独立的实体，没有在本次抽取中定义其子属性
    "症状": [],  # 症状也是一个独立实体
    "药物": ["用法"],  # 药物实体，并且我们希望同时找到它的"用法“属性
    "检查项目": []  # 我们还对检查项目感兴趣
}

# 1. 初始化信息抽取管道，传入我们设计好的Schema
# `model=‘uie-medical-base’`指定使用医疗专用模型
ie_pipeline = Taskflow("information_extraction", 
                       schema=my_schema, 
                       model="uie-medical-base")
 
# 2. 准备我们的病历文本
medical_text = "患者李某，男，65岁，因‘反复咳嗽、咳痰伴气促3年，加重1周’入院。既往有‘高血压’病史10年。查体：双肺可闻及湿性啰音。初步诊断：慢性阻塞性肺疾病急性加重。予以‘沙美特罗替卡松粉吸入剂’吸入治疗，并嘱其家庭氧疗。"


# 3. 执行抽取！
results = ie_pipeline(medical_text)
print(results)

schema = ['时间', '选手', '赛事名称'] # Define the schema for entity extraction
ie = Taskflow('information_extraction',
              schema= schema,
              schema_lang="zh",
              batch_size=1,
              model='uie-m-base',
              precision='float16')
print(ie("2月8日上午北京冬奥会自由式滑雪女子大跳台决赛中中国选手谷爱凌以188.25分获得金牌！"))