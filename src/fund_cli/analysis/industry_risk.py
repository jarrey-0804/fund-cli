"""
行业集中度风险分析器

检测行业配置集中度风险并生成预警提示。
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class IndustryRiskAnalyzer:
    """
    行业集中度风险分析器

    功能：
    - 计算行业 HHI 指数
    - 识别高集中度行业
    - 生成风险提示
    - 行业景气度判断
    """

    # 默认阈值
    DEFAULT_THRESHOLD_HIGH = 0.40
    DEFAULT_THRESHOLD_MEDIUM = 0.30

    # 行业景气度关键词（正面）
    BOOM_KEYWORDS = ["新能源", "半导体", "人工智能", "AI", "医药", "消费"]

    def analyze_concentration_risk(
        self,
        industry_exposure: dict[str, float],
        threshold_high: float | None = None,
        threshold_medium: float | None = None,
    ) -> dict[str, Any]:
        """
        行业集中度风险提示

        Args:
            industry_exposure: {行业名称: 占比}
            threshold_high: 高风险阈值，默认 0.40
            threshold_medium: 中风险阈值，默认 0.30

        Returns:
            {高集中度行业, 风险提示列表, HHI指数, 集中度评价}
        """
        if threshold_high is None:
            threshold_high = self.DEFAULT_THRESHOLD_HIGH
        if threshold_medium is None:
            threshold_medium = self.DEFAULT_THRESHOLD_MEDIUM

        # 计算 HHI
        hhi = sum(v ** 2 for v in industry_exposure.values())

        # 识别高集中度行业
        high_concentration = {
            k: v for k, v in industry_exposure.items() if v > threshold_medium
        }

        # 生成风险提示
        alerts = []
        for industry, ratio in sorted(high_concentration.items(), key=lambda x: x[1], reverse=True):
            risk_level = "高" if ratio > threshold_high else "中"
            alerts.append({
                "行业": industry,
                "占比": f"{ratio:.2%}",
                "风险等级": risk_level,
                "提示": self._generate_risk_message(industry, ratio, risk_level),
            })

        # 集中度评价
        if hhi < 0.10:
            concentration_verdict = "分散度良好"
        elif hhi < 0.15:
            concentration_verdict = "适度集中"
        elif hhi < 0.25:
            concentration_verdict = "集中度偏高"
        else:
            concentration_verdict = "高度集中"

        return {
            "高集中度行业": high_concentration,
            "风险提示": alerts,
            "HHI指数": round(hhi, 4),
            "集中度评价": concentration_verdict,
        }

    def analyze_boom_bust(
        self,
        industry_exposure: dict[str, float],
    ) -> dict[str, Any]:
        """
        行业景气度分析

        Args:
            industry_exposure: {行业名称: 占比}

        Returns:
            {景气行业, 风险行业, 景气度评价}
        """
        boom_industries = []
        for industry, ratio in industry_exposure.items():
            if any(kw in industry for kw in self.BOOM_KEYWORDS):
                boom_industries.append({"行业": industry, "占比": f"{ratio:.2%}"})

        return {
            "景气行业": boom_industries,
            "风险行业": [],  # 可扩展
            "景气度评价": self._generate_boom_evaluation(boom_industries),
        }

    def _generate_risk_message(
        self,
        industry: str,
        ratio: float,
        risk_level: str,
    ) -> str:
        """生成风险提示消息"""
        if risk_level == "高":
            return f"在{industry}行业的集中度偏高（{ratio:.2%}），可能导致组合波动增大，建议适当分散"
        else:
            return f"在{industry}行业有一定集中度（{ratio:.2%}），需关注行业轮动风险"

    def _generate_boom_evaluation(
        self,
        boom_industries: list[dict[str, str]],
    ) -> str:
        """生成景气度评价"""
        if not boom_industries:
            return "持仓行业分布均衡，无明显景气集中"

        names = "、".join(item["行业"] for item in boom_industries[:3])
        return f"持仓偏向{names}等景气行业，需关注估值水平和轮动风险"

    # =========================================================
    # 行业景气度评分（增强版）
    # =========================================================

    # 内置行业景气度评分（基于当前市场环境，可定期更新）
    BUILTIN_PROSPERITY_SCORES = {
        # 高景气行业（80-100分）
        "有色金属": 85, "人工智能": 90, "半导体": 88, "芯片": 88,
        "新能源": 82, "电力设备": 80, "电网设备": 85, "算力": 88,
        "云计算": 85, "通信": 75, "电子": 78,

        # 中景气行业（50-79分）
        "医药": 65, "医疗保健": 65, "消费": 60, "食品饮料": 62,
        "传媒": 58, "信息技术": 68, "可选消费": 58,
        "汽车": 70, "机械": 65, "军工": 72,

        # 低景气行业（0-49分）
        "房地产": 25, "建筑": 30, "银行": 45, "煤炭": 35,
        "钢铁": 30, "建材": 35,
    }

    def evaluate_industry_prosperity(
        self,
        industry_exposure: dict[str, float],
        use_ai: bool = False,
    ) -> dict[str, Any]:
        """
        行业景气度评分（增强版）

        Args:
            industry_exposure: {行业名称: 占比}
            use_ai: 是否使用LLM进行深度分析

        Returns:
            {
                "行业景气度评分": {
                    "高景气": [{"行业": x, "占比": x, "评分": x}],
                    "中景气": [...],
                    "低景气": [...],
                },
                "整体评价": str,
                "风险提示": str,
            }
        """
        result = {
            "行业景气度评分": {"高景气": [], "中景气": [], "低景气": []},
            "整体评价": "",
            "风险提示": "",
        }

        # 获取内置评分
        industry_scores = self._get_builtin_industry_scores(industry_exposure)

        # 如果使用AI，调用LLM进行深度分析
        if use_ai:
            try:
                ai_analysis = self._ai_industry_analysis(industry_exposure)
                # 合并AI分析结果
                industry_scores = self._merge_scores(industry_scores, ai_analysis)
            except Exception as e:
                logger.warning(f"AI行业分析失败: {e}")

        # 分类
        for industry, data in industry_scores.items():
            score = data.get("score", 50)
            ratio = data.get("ratio", 0)

            item = {
                "行业": industry,
                "占比": f"{ratio:.2%}",
                "评分": score,
                "理由": data.get("reason", ""),
            }

            if score >= 70:
                result["行业景气度评分"]["高景气"].append(item)
            elif score >= 40:
                result["行业景气度评分"]["中景气"].append(item)
            else:
                result["行业景气度评分"]["低景气"].append(item)

        # 生成整体评价
        result["整体评价"] = self._generate_prosperity_summary(result["行业景气度评分"])
        result["风险提示"] = self._generate_prosperity_risk_alert(
            result["行业景气度评分"],
            industry_exposure
        )

        return result

    def _get_builtin_industry_scores(
        self,
        industry_exposure: dict[str, float]
    ) -> dict[str, dict[str, Any]]:
        """获取内置行业评分"""
        result = {}

        for industry, ratio in industry_exposure.items():
            # 匹配行业名称
            score = 50  # 默认中等
            reason = "行业景气度一般"

            # 尝试匹配内置评分
            for key, val in self.BUILTIN_PROSPERITY_SCORES.items():
                if key in industry or industry in key:
                    score = val
                    if val >= 70:
                        reason = "行业处于高景气周期"
                    elif val >= 40:
                        reason = "行业景气度平稳"
                    else:
                        reason = "行业面临一定压力"
                    break

            result[industry] = {
                "score": score,
                "ratio": ratio,
                "reason": reason,
            }

        return result

    def _ai_industry_analysis(
        self,
        industry_exposure: dict[str, float]
    ) -> dict[str, dict[str, Any]]:
        """使用AI进行行业分析"""
        try:
            from fund_cli.ai.analyzer import AIAnalyzer

            analyzer = AIAnalyzer()

            # 构建提示词
            industries_text = "\n".join([
                f"- {industry}: {ratio:.2%}"
                for industry, ratio in industry_exposure.items()
            ])

            prompt = f"""请分析以下持仓行业的景气度（0-100分），并给出理由：

持仓行业分布：
{industries_text}

请以JSON格式返回：
{{
    "行业名称": {{"score": 分数, "reason": "理由"}},
    ...
}}

注意：
1. 考虑当前宏观经济环境
2. 考虑行业政策影响
3. 考虑行业周期位置
4. 评分标准：80-100高景气，50-79中景气，0-49低景气"""

            response = analyzer.provider.generate(prompt)
            # 解析JSON响应
            import json
            import re

            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"AI行业分析失败: {e}")

        return {}

    def _merge_scores(
        self,
        builtin: dict[str, dict[str, Any]],
        ai: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """合并内置评分和AI评分"""
        result = builtin.copy()

        for industry, data in ai.items():
            if industry in result:
                # 加权平均（AI评分权重0.6，内置评分权重0.4）
                ai_score = data.get("score", 50)
                builtin_score = result[industry].get("score", 50)
                merged_score = ai_score * 0.6 + builtin_score * 0.4

                result[industry]["score"] = round(merged_score, 1)
                if "reason" in data:
                    result[industry]["reason"] = data["reason"]
            else:
                result[industry] = {
                    "score": data.get("score", 50),
                    "ratio": 0,
                    "reason": data.get("reason", ""),
                }

        return result

    def _generate_prosperity_summary(
        self,
        scores: dict[str, list]
    ) -> str:
        """生成景气度总结"""
        high_count = len(scores["高景气"])
        mid_count = len(scores["中景气"])
        low_count = len(scores["低景气"])

        # 计算高景气行业占比
        high_weight = sum(
            float(item["占比"].replace("%", ""))
            for item in scores["高景气"]
        )

        if high_count > mid_count + low_count:
            return f"持仓主要集中在高景气行业，成长性强（高景气行业占比{high_weight:.1f}%）"
        elif high_count > 0:
            return f"持仓包含部分高景气行业，兼具成长与稳健（高景气行业占比{high_weight:.1f}%）"
        elif low_count > mid_count:
            return "持仓行业景气度偏低，需关注行业轮动机会"
        else:
            return "持仓行业景气度分布较为均衡"

    def _generate_prosperity_risk_alert(
        self,
        scores: dict[str, list],
        exposure: dict[str, float]
    ) -> str:
        """生成景气度风险提示"""
        alerts = []

        # 检查高集中度的高景气行业
        high_prosperity_weight = sum(
            float(item["占比"].replace("%", ""))
            for item in scores["高景气"]
        )

        if high_prosperity_weight > 40:
            alerts.append(f"高景气行业占比{high_prosperity_weight:.1f}%，需关注估值水平和景气持续性")

        # 检查低景气行业
        if scores["低景气"]:
            low_names = "、".join([item["行业"] for item in scores["低景气"][:3]])
            alerts.append(f"{low_names}等行业景气度较低，关注行业改善信号")

        return "；".join(alerts) if alerts else "行业景气度整体健康"

    def generate_prosperity_report(
        self,
        industry_exposure: dict[str, float],
        use_ai: bool = False,
    ) -> str:
        """
        生成行业景气度报告（Markdown格式）

        Args:
            industry_exposure: {行业名称: 占比}
            use_ai: 是否使用AI分析

        Returns:
            Markdown格式的报告
        """
        result = self.evaluate_industry_prosperity(industry_exposure, use_ai)

        lines = ["### 行业景气度评分\n"]

        # 高景气行业
        if result["行业景气度评分"]["高景气"]:
            lines.append("**高景气行业**（评分≥70）:\n")
            lines.append("| 行业 | 占比 | 评分 | 理由 |")
            lines.append("| --- | --- | --- | --- |")
            for item in result["行业景气度评分"]["高景气"]:
                lines.append(
                    f"| {item['行业']} | {item['占比']} | {item['评分']} | {item['理由']} |"
                )
            lines.append("")

        # 中景气行业
        if result["行业景气度评分"]["中景气"]:
            lines.append("**中景气行业**（评分40-69）:\n")
            lines.append("| 行业 | 占比 | 评分 | 理由 |")
            lines.append("| --- | --- | --- | --- |")
            for item in result["行业景气度评分"]["中景气"][:5]:  # 只显示前5个
                lines.append(
                    f"| {item['行业']} | {item['占比']} | {item['评分']} | {item['理由']} |"
                )
            lines.append("")

        # 低景气行业
        if result["行业景气度评分"]["低景气"]:
            lines.append("**低景气行业**（评分<40）:\n")
            for item in result["行业景气度评分"]["低景气"]:
                lines.append(f"- {item['行业']}（{item['占比']}，评分{item['评分']}）")
            lines.append("")

        # 整体评价
        lines.append(f"**整体评价**: {result['整体评价']}")
        lines.append("")

        if result['风险提示']:
            lines.append(f"**风险提示**: {result['风险提示']}")

        return "\n".join(lines)
