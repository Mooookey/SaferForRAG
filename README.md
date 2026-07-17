使用Microsoft Presidio和Spacy zh_core_web_sm作为内置引擎
使用以下命令配置生产环境py3.10
'''bash
pip install presidio-analyzer presidio-anonymizer click fastapi uvicorn

# 对于llm guard有三种方案
pip install llm-guard 
pip install llm-guard[onnxruntime]
pip install llm-guard[onnxruntime-gpu]

# 下载presidio的底层模型
python -m spacy download zh_core_web_sm 
python -m spacy download zh_core_web_lg  
'''
其中，
- llm-guard使用普通 PyTorch/transformers 路线，首次加载和推理都会比较慢
- llm-guard[onnxruntime]，llm-guard[onnxruntime-gpu]会分别使用ONNX CPU/GPU Runtime(!--目前并未测试oonx环境)

冻结版本
```bash
python -m pip freeze > requirements.txt

```
启动FastAPI服务
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```