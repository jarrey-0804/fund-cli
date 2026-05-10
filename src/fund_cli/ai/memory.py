"""
ChromaDB 长期记忆封装 - 语义向量记忆检索

本模块基于 ChromaDB 实现面向 AI Agent 的长期语义记忆系统，
支持将对话历史、分析结论、用户偏好等信息以向量形式持久化存储，
并在后续交互中通过语义相似度检索相关记忆。

主要功能:
    - 将文本记忆转化为向量嵌入并存储
    - 基于语义相似度检索相关记忆
    - 支持按类别/标签组织记忆
    - 自动管理记忆元数据（时间戳、来源等）

依赖:
    - chromadb (可选): 需要安装 ``pip install chromadb``，未安装时
      :class:`VectorMemory` 的实例化会抛出 :exc:`ImportError`

使用示例:
    >>> memory = VectorMemory(collection_name="fund_analysis")
    >>> memory.add_memory("用户偏好低风险债券型基金", category="preference")
    >>> results = memory.search_memory("适合保守型投资者的基金", n_results=3)
    >>> for doc, meta in results:
    ...     print(doc, meta)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

try:
    import chromadb
except ImportError as exc:
    raise ImportError("chromadb 包未安装，请执行: pip install chromadb") from exc

logger = logging.getLogger(__name__)


class VectorMemory:
    """基于 ChromaDB 的语义向量记忆管理器。

    提供 add_memory、search_memory、get_relevant_memories 三个核心方法，
    用于存储、检索和管理 AI Agent 的长期记忆。

    记忆以 ``{id, document, embedding, metadata}`` 四元组的形式存储在
    ChromaDB Collection 中，其中 metadata 包含时间戳、类别、来源等辅助信息。

    Args:
        collection_name: ChromaDB 集合名称，用于隔离不同场景的记忆
        persist_directory: 持久化存储目录路径。
            为 ``None`` 时使用内存模式（数据不持久化），
            传入路径时数据会保存到磁盘
        embedding_function: 自定义嵌入函数。
            为 ``None`` 时使用 ChromaDB 默认嵌入模型

    Raises:
        ImportError: 当 chromadb 包未安装时

    使用示例:
        >>> memory = VectorMemory(
        ...     collection_name="fund_agent",
        ...     persist_directory="~/.fund_cli/memory",
        ... )
        >>> memory.add_memory(
        ...     content="用户倾向于配置沪深300指数基金作为底仓",
        ...     category="preference",
        ...     source="conversation",
        ... )
        >>> results = memory.search_memory("指数基金配置建议", n_results=5)
    """

    # 默认嵌入模型维度（ChromaDB 默认 all-MiniLM-L6-v2 为 384 维）
    _DEFAULT_EMBEDDING_DIM: int = 384

    def __init__(
        self,
        collection_name: str = "fund_cli_memory",
        persist_directory: str | None = None,
        embedding_function: Any | None = None,
    ) -> None:
        """初始化向量记忆管理器。

        Args:
            collection_name: ChromaDB 集合名称
            persist_directory: 持久化存储目录，为 None 时使用内存模式
            embedding_function: 自定义嵌入函数，为 None 时使用默认模型
        """
        self._collection_name = collection_name
        self._persist_directory = persist_directory

        # 初始化 ChromaDB 客户端
        if persist_directory:
            self._client = chromadb.PersistentClient(path=persist_directory)
        else:
            self._client = chromadb.Client()

        # 获取或创建集合
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function,
            metadata={"hnsw:space": "cosine"},
        )

        logger.info(
            "VectorMemory 初始化完成: collection=%s, persist=%s, count=%d",
            collection_name,
            persist_directory or "内存模式",
            self._collection.count(),
        )

    @property
    def collection(self) -> Any:
        """获取底层 ChromaDB Collection 对象。

        Returns:
            chromadb.Collection: ChromaDB 集合实例
        """
        return self._collection

    @property
    def count(self) -> int:
        """获取当前记忆条目总数。

        Returns:
            int: 记忆条目数量
        """
        return self._collection.count()

    def add_memory(
        self,
        content: str,
        category: str = "general",
        source: str = "unknown",
        metadata: dict[str, Any] | None = None,
        memory_id: str | None = None,
    ) -> str:
        """添加一条新的语义记忆。

        将文本内容转化为向量嵌入并持久化存储到 ChromaDB 集合中，
        同时记录时间戳、类别、来源等元数据。

        Args:
            content: 记忆文本内容，如对话摘要、分析结论、用户偏好等
            category: 记忆类别标签，用于分类管理。
                常用值: ``"preference"``（用户偏好）、``"analysis"``（分析结论）、
                ``"conversation"``（对话摘要）、``"market"``（市场观察）、
                ``"general"``（通用）
            source: 记忆来源标识，如 ``"conversation"``、``"report"``、``"system"``
            metadata: 额外的自定义元数据字典，会与自动生成的元数据合并
            memory_id: 自定义记忆 ID。为 ``None`` 时自动生成 UUID

        Returns:
            str: 记忆的唯一标识 ID

        Raises:
            ValueError: 当 content 为空字符串时

        使用示例:
            >>> memory_id = memory.add_memory(
            ...     content="该用户偏好低波动率基金，风险承受能力较低",
            ...     category="preference",
            ...     source="conversation",
            ... )
            >>> print(memory_id)
            'a1b2c3d4-...'
        """
        if not content or not content.strip():
            raise ValueError("记忆内容不能为空")

        # 生成唯一 ID
        doc_id = memory_id or str(uuid.uuid4())

        # 构建元数据
        now = datetime.now(timezone.utc).isoformat()
        base_metadata: dict[str, Any] = {
            "category": category,
            "source": source,
            "created_at": now,
            "updated_at": now,
        }

        # 合并自定义元数据
        if metadata:
            base_metadata.update(metadata)

        # 写入 ChromaDB
        self._collection.upsert(
            ids=[doc_id],
            documents=[content.strip()],
            metadatas=[base_metadata],
        )

        logger.debug(
            "添加记忆: id=%s, category=%s, content_len=%d",
            doc_id,
            category,
            len(content),
        )

        return doc_id

    def search_memory(
        self,
        query: str,
        n_results: int = 5,
        category: str | None = None,
        where: dict[str, Any] | None = None,
    ) -> list[tuple[str, dict[str, Any]]]:
        """基于语义相似度搜索记忆。

        将查询文本转化为向量嵌入，在 ChromaDB 集合中检索语义最相似的
        记忆条目，返回按相似度排序的结果列表。

        Args:
            query: 查询文本，如 "适合保守型投资者的配置方案"
            n_results: 返回结果数量上限，默认 5
            category: 按类别过滤，为 ``None`` 时不过滤
            where: ChromaDB where 过滤条件字典。
                与 category 同时使用时会取交集。
                参考: https://docs.trychroma.com/guides#filtering-by-metadata

        Returns:
            list[tuple[str, dict[str, Any]]]: 搜索结果列表，
                每个元素为 ``(document, metadata)`` 元组，
                按语义相似度从高到低排序

        Raises:
            ValueError: 当 query 为空字符串时

        使用示例:
            >>> results = memory.search_memory(
            ...     query="债券基金推荐",
            ...     category="analysis",
            ...     n_results=3,
            ... )
            >>> for doc, meta in results:
            ...     print(f"[{meta['category']}] {doc}")
        """
        if not query or not query.strip():
            raise ValueError("查询文本不能为空")

        # 构建过滤条件
        where_conditions: dict[str, Any] = {}
        if category:
            where_conditions["category"] = category
        if where:
            where_conditions.update(where)

        # 执行查询
        query_params: dict[str, Any] = {
            "query_texts": [query.strip()],
            "n_results": min(n_results, max(1, self._collection.count())),
        }
        if where_conditions:
            query_params["where"] = where_conditions

        # 空集合时直接返回
        if self._collection.count() == 0:
            return []

        results = self._collection.query(**query_params)

        # 解析结果
        output: list[tuple[str, dict[str, Any]]] = []
        if results and results.get("documents"):
            documents = results["documents"][0]
            metadatas = results.get("metadatas", [[]])[0]

            for doc, meta in zip(documents, metadatas, strict=True):
                output.append((doc, meta or {}))

        logger.debug(
            "搜索记忆: query='%s', category=%s, results=%d",
            query[:50],
            category,
            len(output),
        )

        return output

    def get_relevant_memories(
        self,
        query: str,
        n_results: int = 5,
        category: str | None = None,
        score_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """获取与查询相关的记忆（带距离分数）。

        与 :meth:`search_memory` 类似，但返回更丰富的结果结构，
        包含记忆 ID、文档内容、元数据和距离分数，便于上层逻辑
        根据相关性阈值进行二次过滤。

        Args:
            query: 查询文本
            n_results: 返回结果数量上限，默认 5
            category: 按类别过滤
            score_threshold: 距离分数阈值（0~1，越小越相似）。
                仅返回距离分数低于此阈值的结果。
                为 ``None`` 时不过滤

        Returns:
            list[dict[str, Any]]: 相关记忆列表，每个元素为字典:
                ``{
                    "id": str,
                    "content": str,
                    "metadata": dict,
                    "distance": float,
                }``
                按距离从小到大排序（最相似的在前）

        使用示例:
            >>> memories = memory.get_relevant_memories(
            ...     query="用户之前关注过哪些基金",
            ...     n_results=5,
            ...     score_threshold=0.5,
            ... )
            >>> relevant = [m for m in memories if m["distance"] < 0.3]
            >>> for m in relevant:
            ...     print(f"[距离={m['distance']:.3f}] {m['content']}")
        """
        if not query or not query.strip():
            raise ValueError("查询文本不能为空")

        # 空集合时直接返回
        if self._collection.count() == 0:
            return []

        # 构建过滤条件
        where_conditions: dict[str, Any] = {}
        if category:
            where_conditions["category"] = category

        # 执行查询（包含距离分数）
        query_params: dict[str, Any] = {
            "query_texts": [query.strip()],
            "n_results": min(n_results, max(1, self._collection.count())),
        }
        if where_conditions:
            query_params["where"] = where_conditions

        results = self._collection.query(**query_params)

        # 解析结果
        output: list[dict[str, Any]] = []
        if results and results.get("documents"):
            documents = results["documents"][0]
            ids = results.get("ids", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            for doc_id, doc, meta, distance in zip(
                ids, documents, metadatas, distances, strict=True
            ):
                # 距离阈值过滤
                if score_threshold is not None and distance > score_threshold:
                    continue

                output.append(
                    {
                        "id": doc_id,
                        "content": doc,
                        "metadata": meta or {},
                        "distance": distance,
                    }
                )

        logger.debug(
            "获取相关记忆: query='%s', threshold=%s, results=%d",
            query[:50],
            score_threshold,
            len(output),
        )

        return output

    def delete_memory(self, memory_id: str) -> bool:
        """删除指定 ID 的记忆条目。

        Args:
            memory_id: 记忆的唯一标识 ID

        Returns:
            bool: 删除是否成功（True 表示成功）
        """
        try:
            self._collection.delete(ids=[memory_id])
            logger.debug("删除记忆: id=%s", memory_id)
            return True
        except Exception as e:
            logger.warning("删除记忆失败: id=%s, error=%s", memory_id, e)
            return False

    def delete_by_category(self, category: str) -> int:
        """删除指定类别的所有记忆。

        Args:
            category: 要删除的记忆类别

        Returns:
            int: 删除的记忆条目数量
        """
        try:
            # 先查询该类别下的所有 ID
            results = self._collection.get(
                where={"category": category},
            )
            ids = results.get("ids", [])
            if ids:
                self._collection.delete(ids=ids)
                logger.info("按类别删除记忆: category=%s, count=%d", category, len(ids))
            return len(ids)
        except Exception as e:
            logger.warning("按类别删除记忆失败: category=%s, error=%s", category, e)
            return 0

    def update_memory(
        self,
        memory_id: str,
        content: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """更新已有记忆的内容或元数据。

        Args:
            memory_id: 记忆的唯一标识 ID
            content: 新的记忆内容，为 ``None`` 时仅更新元数据
            metadata: 要更新的元数据字典，会与现有元数据合并

        Returns:
            bool: 更新是否成功
        """
        try:
            update_params: dict[str, Any] = {"ids": [memory_id]}

            if content:
                update_params["documents"] = [content.strip()]

            if metadata:
                # 获取现有元数据并合并
                existing = self._collection.get(ids=[memory_id])
                existing_metas = existing.get("metadatas", [{}])
                if existing_metas:
                    merged = {**existing_metas[0], **metadata}
                    merged["updated_at"] = datetime.now(timezone.utc).isoformat()
                    update_params["metadatas"] = [merged]

            self._collection.update(**update_params)
            logger.debug("更新记忆: id=%s", memory_id)
            return True
        except Exception as e:
            logger.warning("更新记忆失败: id=%s, error=%s", memory_id, e)
            return False

    def get_all_categories(self) -> list[str]:
        """获取所有已存在的记忆类别。

        Returns:
            list[str]: 去重后的类别列表
        """
        try:
            all_data = self._collection.get()
            metadatas = all_data.get("metadatas", [])
            categories = set()
            for meta in metadatas:
                if meta and "category" in meta:
                    categories.add(meta["category"])
            return sorted(categories)
        except Exception as e:
            logger.warning("获取类别列表失败: error=%s", e)
            return []

    def reset(self) -> None:
        """清空当前集合中的所有记忆。

        .. warning::
            此操作不可逆，请谨慎使用。
        """
        # 删除并重新创建集合
        self._client.delete_collection(name=self._collection_name)
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("记忆集合已重置: collection=%s", self._collection_name)

    def __repr__(self) -> str:
        return (
            f"VectorMemory("
            f"collection={self._collection_name!r}, "
            f"count={self.count}, "
            f"persist={self._persist_directory or '内存模式'})"
        )
