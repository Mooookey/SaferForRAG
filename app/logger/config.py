import logging
import logging.handlers
import os


LOG_DIR = "logs"

os.makedirs(LOG_DIR, exist_ok=True)


def setup_logger():

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )


    # 项目业务日志
    app_handler = logging.handlers.RotatingFileHandler(
        f"{LOG_DIR}/app.log",
        maxBytes=20*1024*1024,
        backupCount=3,
        encoding="utf-8"
    )

    app_handler.setFormatter(formatter)


    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)
    app_logger.addHandler(app_handler)


    # 第三方服务日志
    service_handler = logging.handlers.RotatingFileHandler(
        f"{LOG_DIR}/service.log",
        maxBytes=20*1024*1024,
        backupCount=3,
        encoding="utf-8"
    )

    service_handler.setFormatter(formatter)


    service_logger = logging.getLogger("service")
    service_logger.setLevel(logging.INFO)
    service_logger.addHandler(service_handler)


    return app_logger, service_logger