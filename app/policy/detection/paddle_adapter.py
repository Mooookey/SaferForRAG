from asyncio import Lock
import asyncio
import paddle
import paddlenlp
from paddlenlp import Taskflow

from dataclasses import dataclass
from typing import Any

from app.policy.detection.plan import PaddleCall

# 实例池版本，实现简单
class PaddlePipelinePoolFactory:
    def __init__(self, pool_size=5):
        self.pool = asyncio.Queue(maxsize=pool_size)
        for _ in range(pool_size):
            self.pool.put_nowait(Taskflow("information_extraction"))

    async def get_pipeline(self, schema):
        # 如果池为空，自动阻塞等待归还
        taskflow = await self.pool.get()
        taskflow.set_schema(schema)
        return taskflow

    async def return_pipeline(self, taskflow):
        # 自动唤醒等待的 get() 协程
        await self.pool.put(taskflow)


@dataclass
class PipelineHandle:
    pipeline: Any | None
    current_schema: tuple[str, ...] | None
    lock: Lock


class PaddlePipelineFactory:
    # 细颗粒度
    def __init__(self) -> None:
        self._handles: dict[tuple[str, str | None], PipelineHandle] = {}
        self._global_lock = Lock()

    async def _get_handle(self, model: str, schema_lang: str | None) -> PipelineHandle:
        key = (model, schema_lang)
        if key not in self._handles:
            async with self._global_lock:
                if key not in self._handles:
                    self._handles[key] = PipelineHandle(
                        pipeline=None,
                        current_schema=None,
                        lock=Lock(),
                    )
        return self._handles[key]

    async def predict(
        self,
        text: str,
        call: PaddleCall,
    ) -> list[dict]:
        handle = await self._get_handle(call.model, call.schema_lang)

        async with handle.lock:

            # 不同场景实例复用
            if handle.pipeline is None:
                kwargs = {
                    "model": call.model,
                    "schema": list(call.schema),
                }

                # 只给多语言模型传 schema_lang
                if call.schema_lang is not None:
                    kwargs["schema_lang"] = call.schema_lang

                handle.pipeline = Taskflow(
                    "information_extraction",
                    **kwargs,
                )
                handle.current_schema = call.schema

            elif handle.current_schema != call.schema:
                handle.pipeline.set_schema(list(call.schema))
                handle.current_schema = call.schema

            return handle.pipeline(text)
