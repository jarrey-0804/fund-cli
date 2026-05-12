"""
数据脱敏工具.

提供敏感数据脱敏功能，保护用户隐私和敏感信息。
"""

import hashlib
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class DataMasker:
    """
    数据脱敏器.

    支持多种脱敏策略：掩码、哈希、截断等。
    """

    # 基金代码脱敏规则：显示前3位和后1位，中间用***代替
    FUND_CODE_MASK = r"^(\d{3})\d{2}(\d)$"

    # 身份证号脱敏规则
    ID_CARD_MASK = r"^(\d{4})\d{10}(\d{4})$"

    # 手机号脱敏规则
    PHONE_MASK = r"^(\d{3})\d{4}(\d{4})$"

    # 邮箱脱敏规则
    EMAIL_MASK = r"^(.{2}).*(@.*)$"

    def __init__(self, privacy_mode: bool = False):
        """
        初始化脱敏器.

        Args:
            privacy_mode: 是否启用隐私模式（完全脱敏）
        """
        self.privacy_mode = privacy_mode

    def mask_fund_code(self, fund_code: str) -> str:
        """
        脱敏基金代码.

        Args:
            fund_code: 基金代码

        Returns:
            脱敏后的基金代码
        """
        if not fund_code or len(fund_code) != 6:
            return fund_code

        if self.privacy_mode:
            return "******"

        # 显示前3位和后1位
        return f"{fund_code[:3]}**{fund_code[-1]}"

    def mask_id_card(self, id_card: str) -> str:
        """
        脱敏身份证号.

        Args:
            id_card: 身份证号

        Returns:
            脱敏后的身份证号
        """
        if not id_card or len(id_card) != 18:
            return id_card

        if self.privacy_mode:
            return "******************"

        return f"{id_card[:4]}**********{id_card[-4:]}"

    def mask_phone(self, phone: str) -> str:
        """
        脱敏手机号.

        Args:
            phone: 手机号

        Returns:
            脱敏后的手机号
        """
        if not phone or len(phone) != 11:
            return phone

        if self.privacy_mode:
            return "***********"

        return f"{phone[:3]}****{phone[-4:]}"

    def mask_email(self, email: str) -> str:
        """
        脱敏邮箱.

        Args:
            email: 邮箱地址

        Returns:
            脱敏后的邮箱
        """
        if not email or "@" not in email:
            return email

        if self.privacy_mode:
            local, domain = email.split("@")
            return f"{'*' * len(local)}@{domain}"

        local, domain = email.split("@")
        if len(local) <= 2:
            return f"{'*' * len(local)}@{domain}"

        return f"{local[:2]}{'*' * (len(local) - 2)}@{domain}"

    def mask_amount(self, amount: float | int, precision: int = 2) -> str:
        """
        脱敏金额.

        Args:
            amount: 金额
            precision: 小数精度

        Returns:
            脱敏后的金额字符串
        """
        if amount is None:
            return "***"

        if self.privacy_mode:
            return "***"

        # 保留数量级，隐藏具体数值
        if amount >= 1000000:
            return f"{amount / 1000000:.{precision}f}M+"
        elif amount >= 1000:
            return f"{amount / 1000:.{precision}f}K+"
        else:
            return f"{amount:.{precision}f}"

    def mask_string(self, s: str, visible_chars: int = 2) -> str:
        """
        通用字符串脱敏.

        Args:
            s: 字符串
            visible_chars: 前后保留的可见字符数

        Returns:
            脱敏后的字符串
        """
        if not s:
            return s

        if self.privacy_mode:
            return "*" * len(s)

        if len(s) <= visible_chars * 2:
            return "*" * len(s)

        return f"{s[:visible_chars]}{'*' * (len(s) - visible_chars * 2)}{s[-visible_chars:]}"

    def hash_value(self, value: str, salt: str = "") -> str:
        """
        哈希敏感值.

        Args:
            value: 原始值
            salt: 盐值

        Returns:
            哈希后的值
        """
        if not value:
            return value

        hash_input = f"{value}{salt}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def mask_dict(self, data: dict, sensitive_fields: list[str] | None = None) -> dict:
        """
        脱敏字典中的敏感字段.

        Args:
            data: 原始数据字典
            sensitive_fields: 敏感字段列表，None则使用默认列表

        Returns:
            脱敏后的字典
        """
        if sensitive_fields is None:
            sensitive_fields = [
                "fund_code", "id_card", "phone", "email",
                "name", "address", "amount", "balance"
            ]

        result = {}
        for key, value in data.items():
            if key in sensitive_fields:
                result[key] = self._mask_field(key, value)
            elif isinstance(value, dict):
                result[key] = self.mask_dict(value, sensitive_fields)
            elif isinstance(value, list):
                result[key] = [self.mask_dict(item, sensitive_fields) if isinstance(item, dict) else item for item in value]
            else:
                result[key] = value

        return result

    def _mask_field(self, field_name: str, value: Any) -> Any:
        """根据字段名选择脱敏方法."""
        if value is None:
            return None

        field_name_lower = field_name.lower()

        if "fund_code" in field_name_lower or "code" in field_name_lower:
            return self.mask_fund_code(str(value))
        elif "id_card" in field_name_lower or "idcard" in field_name_lower:
            return self.mask_id_card(str(value))
        elif "phone" in field_name_lower or "mobile" in field_name_lower:
            return self.mask_phone(str(value))
        elif "email" in field_name_lower or "mail" in field_name_lower:
            return self.mask_email(str(value))
        elif "amount" in field_name_lower or "balance" in field_name_lower or "money" in field_name_lower:
            if isinstance(value, (int, float)):
                return self.mask_amount(value)
            return self.mask_string(str(value))
        elif "name" in field_name_lower:
            return self.mask_string(str(value), visible_chars=1)
        else:
            return self.mask_string(str(value))


# 全局脱敏器实例
_masker: DataMasker | None = None


def get_data_masker(privacy_mode: bool = False) -> DataMasker:
    """获取全局数据脱敏器实例."""
    global _masker
    if _masker is None:
        _masker = DataMasker(privacy_mode=privacy_mode)
    return _masker


def mask_report_data(report_data: dict, privacy_mode: bool = False) -> dict:
    """
    脱敏报告数据.

    Args:
        report_data: 报告数据
        privacy_mode: 是否启用隐私模式

    Returns:
        脱敏后的报告数据
    """
    masker = get_data_masker(privacy_mode=privacy_mode)

    # 定义报告中的敏感字段
    sensitive_fields = [
        "fund_code", "fund_name", "manager_name",
        "holding", "holdings", "transaction", "transactions",
        "amount", "balance", "cost", "market_value"
    ]

    return masker.mask_dict(report_data, sensitive_fields)
