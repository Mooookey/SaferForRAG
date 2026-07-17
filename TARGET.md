# 依赖
请你先查看AGENTS.md重点查看链接中的文档。
# 背景
我目前需要利用PaddleNLP对本系统能识别的实体进行扩充，补全presidio传统NER模型不足的短板。
我打算使用信息抽取information_extraction，并使用uie-medical-base作为医疗实体识别，使用uie-m-base作为通用实体识别。具体例子已经在example/paddle中给出。我目前对识别规则做了以下更改：
1.建立了统一实体规则ENTITY_CATALOG: dict[str, EntityDefinition]，之后脱敏用该字典的键作为唯一实体识别符

2.这里需要分别提取中文实体抽取、英文实体抽取和医疗实体抽取，分别给uie-m-base、uie-m-base、uie-medical-base，从而得到paddle_calls


# 要求

@app.post("/extract")
async def extract(text: str, schema: dict):
    taskflow = await factory.get_pipeline(schema)
    try:
        return taskflow(text)
    finally:
        await factory.return_pipeline(taskflow)  # 无论如何都要归还