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


请你给出logger/config.py的代码实现，但不写进代码，要求分为多个主要函数或者由一个类分别管理，或者你有更规范的编写方式的话更好，分别为：
1. 对内部库的日志进行重定向，拦截并输出到service.log中：
    - 采用点名拦截+清掉handler+阻止传递到root，级别设置为INFO
    - 除了拦截并重定向presidio/paddlenlp，要求能拦截llm guard配置的structlog日志
2. 外部请求响应记录到app.log
    - 设置.propagate = False
    - 同时给出@app.middleware("http")的中间件的代码实现，记录method / path / status_code / 耗时 / 响应的sha_256
3. 当设置环境变量DEBUG_LOG_ENABLED==True时，开启调试日志，将请求体和响应体完整记录到logs/debug.log
    - 采用RotatingFileHandler
    - 在2.中的中间件增加开关，并且写到该中间件中
4. 所有日志，需要同时输出到控制台，并且共享一个实例
5. 需要幂等，开头对目标 logger 先 handlers.clear()