# 启动项目

使用Microsoft Presidio和Spacy zh_core_web_sm作为内置引擎
使用以下命令配置生产环境py3.10，在虚拟环境中执行`pip install .`即可

**<过时>**
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
**</过时>**

## 直接启动FastAPI服务
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```
进行本地测试：
```bash
node tests/api_test.js
```

## 直接启动Docker服务
```bash
docker compose build
docker compose up
## 关闭Docker
docker compose down
```

## 在Linux上，使用虚拟环境启动中间件
样例在`fastapi.service.example`中给出
```bash
# 配置.service和log/
sudo vim /etc/systemd/system/fastapi.service
sudo mkdir -p /var/log/fastapi
sudo chown <your_username>:<your_group> /var/log/fastapi

# 每次修改 .service 文件后，必须执行：
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start fastapi

# 停止服务
sudo systemctl stop fastapi

# 重启服务（修改配置后常用）
sudo systemctl restart fastapi

# 重新加载配置（不中断服务，仅对支持热加载的应用有效）
sudo systemctl reload fastapi

# 查看运行状态
sudo systemctl status fastapi

# 查看实时日志（类似 tail -f）
sudo journalctl -u fastapi -f

# 查看最近100行日志
sudo journalctl -u fastapi -n 100

# 查看今天的全部日志
sudo journalctl -u fastapi --since today

# 启用开机自启
sudo systemctl enable fastapi

# 禁用开机自启
sudo systemctl disable fastapi

# 检查是否已启用
sudo systemctl is-enabled fastapi
```