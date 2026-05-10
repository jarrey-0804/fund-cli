"""
审计日志模块.

记录数据质量检查、分析操作、报告生成等关键操作，用于合规留痕。
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    审计日志记录器.

    记录关键操作和数据质量检查结果，支持合规审计。
    """

    def __init__(self, log_dir: str | Path | None = None):
        """
        初始化审计日志记录器.

        Args:
            log_dir: 日志目录，默认 ~/.fund_cli/audit
        """
        if log_dir is None:
            self._log_dir = Path.home() / ".fund_cli" / "audit"
        else:
            self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)

        # 初始化日志文件
        self._log_file = self._log_dir / f"audit_{datetime.now().strftime('%Y%m')}.jsonl"

    def _generate_id(self) -> str:
        """生成操作ID."""
        return str(uuid.uuid4())[:16]

    def _write_log(self, record: dict[str, Any]) -> None:
        """写入日志记录."""
        record["timestamp"] = datetime.now().isoformat()
        record["log_id"] = self._generate_id()

        try:
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"审计日志写入失败: {e}")

    def log_quality_check(
        self,
        fund_code: str,
        quality_score: float,
        quality_level: str,
        blocked: bool,
        details: dict | None = None,
    ) -> str:
        """
        记录质量检查日志.

        Returns:
            日志记录ID
        """
        log_id = self._generate_id()
        record = {
            "operation": "quality_check",
            "log_id": log_id,
            "fund_code": fund_code,
            "quality_score": quality_score,
            "quality_level": quality_level,
            "blocked": blocked,
            "details": details or {},
        }
        self._write_log(record)
        return log_id

    def log_analysis(
        self, fund_code: str, analysis_type: str, metrics: dict, quality_check_id: str | None = None
    ) -> str:
        """记录分析操作日志."""
        log_id = self._generate_id()
        record = {
            "operation": "analysis",
            "log_id": log_id,
            "fund_code": fund_code,
            "analysis_type": analysis_type,
            "metrics_summary": {k: v for k, v in metrics.items() if v is not None},
            "quality_check_id": quality_check_id,
        }
        self._write_log(record)
        return log_id

    def log_report_generation(
        self,
        fund_code: str,
        report_type: str,
        output_path: str,
        validation_result: dict | None = None,
    ) -> str:
        """记录报告生成日志."""
        log_id = self._generate_id()
        record = {
            "operation": "report_generation",
            "log_id": log_id,
            "fund_code": fund_code,
            "report_type": report_type,
            "output_path": output_path,
            "validation": validation_result or {},
        }
        self._write_log(record)
        return log_id

    def get_logs(
        self,
        operation: str | None = None,
        fund_code: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        查询审计日志.

        Args:
            operation: 操作类型过滤
            fund_code: 基金代码过滤
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回记录数限制

        Returns:
            日志记录列表
        """
        logs = []

        try:
            with open(self._log_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)

                        # 过滤
                        if operation and record.get("operation") != operation:
                            continue
                        if fund_code and record.get("fund_code") != fund_code:
                            continue

                        # 日期过滤
                        if start_date or end_date:
                            ts = datetime.fromisoformat(record.get("timestamp", ""))
                            if start_date and ts < start_date:
                                continue
                            if end_date and ts > end_date:
                                continue

                        logs.append(record)

                        if len(logs) >= limit:
                            break
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass

        return logs


# 全局审计日志实例
_audit_logger: AuditLogger | None = None


def get_audit_logger(log_dir: str | None = None) -> AuditLogger:
    """获取审计日志记录器（单例）."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(log_dir)
    return _audit_logger
