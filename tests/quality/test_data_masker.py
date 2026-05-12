"""
数据脱敏工具测试.

验证敏感数据脱敏功能。
"""

import unittest

from fund_cli.utils.data_masker import (
    DataMasker,
    get_data_masker,
    mask_report_data,
)


class TestDataMasker(unittest.TestCase):
    """测试数据脱敏器."""

    def setUp(self):
        """设置测试环境."""
        self.masker = DataMasker(privacy_mode=False)
        self.privacy_masker = DataMasker(privacy_mode=True)

    def test_mask_fund_code_normal(self):
        """测试基金代码脱敏（普通模式）."""
        result = self.masker.mask_fund_code("000001")
        self.assertEqual(result, "000**1")

    def test_mask_fund_code_privacy(self):
        """测试基金代码脱敏（隐私模式）."""
        result = self.privacy_masker.mask_fund_code("000001")
        self.assertEqual(result, "******")

    def test_mask_fund_code_invalid(self):
        """测试无效基金代码."""
        self.assertEqual(self.masker.mask_fund_code("12345"), "12345")
        self.assertEqual(self.masker.mask_fund_code(""), "")
        self.assertEqual(self.masker.mask_fund_code(None), None)

    def test_mask_id_card_normal(self):
        """测试身份证号脱敏（普通模式）."""
        result = self.masker.mask_id_card("110101199001011234")
        self.assertEqual(result, "1101**********1234")

    def test_mask_id_card_privacy(self):
        """测试身份证号脱敏（隐私模式）."""
        result = self.privacy_masker.mask_id_card("110101199001011234")
        self.assertEqual(result, "******************")

    def test_mask_id_card_invalid(self):
        """测试无效身份证号."""
        self.assertEqual(self.masker.mask_id_card("123456"), "123456")

    def test_mask_phone_normal(self):
        """测试手机号脱敏（普通模式）."""
        result = self.masker.mask_phone("13812345678")
        self.assertEqual(result, "138****5678")

    def test_mask_phone_privacy(self):
        """测试手机号脱敏（隐私模式）."""
        result = self.privacy_masker.mask_phone("13812345678")
        self.assertEqual(result, "***********")

    def test_mask_phone_invalid(self):
        """测试无效手机号."""
        self.assertEqual(self.masker.mask_phone("12345"), "12345")

    def test_mask_email_normal(self):
        """测试邮箱脱敏（普通模式）."""
        result = self.masker.mask_email("user@example.com")
        self.assertEqual(result, "us**@example.com")

    def test_mask_email_short(self):
        """测试短邮箱脱敏."""
        result = self.masker.mask_email("ab@example.com")
        self.assertEqual(result, "**@example.com")

    def test_mask_email_privacy(self):
        """测试邮箱脱敏（隐私模式）."""
        result = self.privacy_masker.mask_email("user@example.com")
        self.assertEqual(result, "****@example.com")

    def test_mask_email_invalid(self):
        """测试无效邮箱."""
        self.assertEqual(self.masker.mask_email("invalid"), "invalid")

    def test_mask_amount_million(self):
        """测试百万级金额脱敏."""
        result = self.masker.mask_amount(1500000)
        self.assertEqual(result, "1.50M+")

    def test_mask_amount_thousand(self):
        """测试千级金额脱敏."""
        result = self.masker.mask_amount(1500)
        self.assertEqual(result, "1.50K+")

    def test_mask_amount_small(self):
        """测试小额金额脱敏."""
        result = self.masker.mask_amount(150)
        self.assertEqual(result, "150.00")

    def test_mask_amount_privacy(self):
        """测试金额脱敏（隐私模式）."""
        result = self.privacy_masker.mask_amount(1500000)
        self.assertEqual(result, "***")

    def test_mask_amount_none(self):
        """测试None金额脱敏."""
        self.assertEqual(self.masker.mask_amount(None), "***")

    def test_mask_string(self):
        """测试通用字符串脱敏."""
        result = self.masker.mask_string("sensitive_data", visible_chars=2)
        self.assertEqual(result, "se**********ta")

    def test_mask_string_short(self):
        """测试短字符串脱敏."""
        result = self.masker.mask_string("ab", visible_chars=2)
        self.assertEqual(result, "**")

    def test_mask_string_privacy(self):
        """测试字符串脱敏（隐私模式）."""
        result = self.privacy_masker.mask_string("test")
        self.assertEqual(result, "****")

    def test_hash_value(self):
        """测试哈希值."""
        result = self.masker.hash_value("sensitive")
        self.assertEqual(len(result), 16)

        # 相同输入应产生相同输出
        result2 = self.masker.hash_value("sensitive")
        self.assertEqual(result, result2)

        # 不同输入应产生不同输出
        result3 = self.masker.hash_value("different")
        self.assertNotEqual(result, result3)

    def test_hash_with_salt(self):
        """测试带盐的哈希."""
        result1 = self.masker.hash_value("sensitive", salt="salt1")
        result2 = self.masker.hash_value("sensitive", salt="salt2")
        self.assertNotEqual(result1, result2)

    def test_mask_dict(self):
        """测试字典脱敏."""
        data = {
            "fund_code": "000001",
            "name": "张三",
            "amount": 1000000,
            "email": "user@example.com",
            "phone": "13812345678",
            "normal_field": "正常数据",
        }

        result = self.masker.mask_dict(data)

        self.assertEqual(result["fund_code"], "000**1")
        self.assertEqual(result["name"], "**")  # 2字符名字全部脱敏
        self.assertEqual(result["amount"], "1.00M+")
        self.assertEqual(result["email"], "us**@example.com")
        self.assertEqual(result["phone"], "138****5678")
        self.assertEqual(result["normal_field"], "正常数据")

    def test_mask_dict_nested(self):
        """测试嵌套字典脱敏."""
        data = {
            "user": {
                "name": "张三",
                "email": "user@example.com",
            },
            "items": [
                {"fund_code": "000001", "amount": 1000},
                {"fund_code": "000002", "amount": 2000},
            ],
        }

        result = self.masker.mask_dict(data)

        self.assertEqual(result["user"]["name"], "**")  # 2字符名字全部脱敏
        self.assertEqual(result["user"]["email"], "us**@example.com")
        self.assertEqual(result["items"][0]["fund_code"], "000**1")
        self.assertEqual(result["items"][1]["fund_code"], "000**2")

    def test_mask_field_by_name(self):
        """测试根据字段名脱敏."""
        self.assertEqual(self.masker._mask_field("fund_code", "000001"), "000**1")
        self.assertEqual(self.masker._mask_field("id_card", "110101199001011234"), "1101**********1234")
        self.assertEqual(self.masker._mask_field("phone", "13812345678"), "138****5678")
        self.assertEqual(self.masker._mask_field("email", "user@example.com"), "us**@example.com")
        self.assertEqual(self.masker._mask_field("amount", 1000), "1.00K+")
        self.assertEqual(self.masker._mask_field("name", "张三"), "**")  # 2字符名字全部脱敏
        self.assertEqual(self.masker._mask_field("other", "test"), "****")  # 4字符全部脱敏


class TestGetDataMasker(unittest.TestCase):
    """测试全局脱敏器获取."""

    def test_get_masker_singleton(self):
        """测试全局单例."""
        masker1 = get_data_masker()
        masker2 = get_data_masker()
        self.assertIs(masker1, masker2)

    def test_get_masker_privacy_mode(self):
        """测试隐私模式."""
        masker = get_data_masker(privacy_mode=True)
        self.assertTrue(masker.privacy_mode)


class TestMaskReportData(unittest.TestCase):
    """测试报告数据脱敏."""

    def test_mask_report(self):
        """测试报告脱敏."""
        # 使用独立的masker避免单例污染
        from fund_cli.utils.data_masker import DataMasker
        masker = DataMasker(privacy_mode=False)

        report_data = {
            "fund_code": "000001",
            "fund_name": "测试基金",
            "manager_name": "张三",
            "holdings": [
                {"code": "000001", "amount": 1000000},
            ],
            "total_amount": 5000000,
        }

        sensitive_fields = [
            "fund_code", "fund_name", "manager_name",
            "holding", "holdings", "transaction", "transactions",
            "amount", "balance", "cost", "market_value"
        ]
        result = masker.mask_dict(report_data, sensitive_fields)

        self.assertEqual(result["fund_code"], "000**1")
        self.assertEqual(result["fund_name"], "测**金")  # 4字符脱敏后保留首尾各1个
        self.assertEqual(result["manager_name"], "**")  # 2字符名字全部脱敏
        # total_amount 不在敏感字段列表中，保持原值
        self.assertEqual(result["total_amount"], 5000000)


if __name__ == "__main__":
    unittest.main()
