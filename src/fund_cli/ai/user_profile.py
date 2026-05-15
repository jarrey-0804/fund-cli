"""
用户画像模块

理解用户需求，提供个性化服务。
支持风险偏好评估、投资目标识别、投资风格分析等功能。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RiskTolerance(str, Enum):
    """风险承受能力"""

    CONSERVATIVE = "保守型"
    MODERATELY_CONSERVATIVE = "相对保守型"
    BALANCED = "平衡型"
    MODERATELY_AGGRESSIVE = "相对进取型"
    AGGRESSIVE = "进取型"


class InvestmentGoal(str, Enum):
    """投资目标"""

    WEALTH_PRESERVATION = "资产保值"
    STEADY_INCOME = "稳健增值"
    BALANCED_GROWTH = "均衡成长"
    AGGRESSIVE_GROWTH = "积极成长"
    SPECULATIVE = "投机获利"


class InvestmentHorizon(str, Enum):
    """投资期限"""

    SHORT_TERM = "短期（<1年）"
    MEDIUM_TERM = "中期（1-3年）"
    LONG_TERM = "长期（3-10年）"
    VERY_LONG_TERM = "超长期（>10年）"


class InvestmentStyle(str, Enum):
    """投资风格"""

    VALUE = "价值型"
    GROWTH = "成长型"
    BALANCED = "平衡型"
    INCOME = "收益型"
    MOMENTUM = "动量型"


@dataclass
class RiskAssessment:
    """风险评估结果"""

    score: int  # 风险评分 1-100
    tolerance: RiskTolerance
    max_drawdown_acceptable: float  # 可接受最大回撤 (%)
    volatility_preference: str  # 波动偏好
    risk_factors: dict[str, int] = field(default_factory=dict)


@dataclass
class InvestmentPreferences:
    """投资偏好"""

    preferred_fund_types: list[str]  # 偏好基金类型
    preferred_sectors: list[str]  # 偏好行业
    excluded_sectors: list[str]  # 排除行业
    min_fund_scale: float  # 最小基金规模（亿）
    max_fund_scale: float  # 最大基金规模（亿）
    preferred_managers: list[str]  # 偏好基金经理
    esg_preference: bool  # ESG偏好


@dataclass
class UserProfile:
    """用户画像"""

    user_id: str
    name: str
    # 风险评估
    risk_assessment: RiskAssessment
    # 投资目标
    investment_goal: InvestmentGoal
    # 投资期限
    investment_horizon: InvestmentHorizon
    # 投资风格
    investment_style: InvestmentStyle
    # 投资偏好
    preferences: InvestmentPreferences
    # 资产规模
    total_assets: float  # 总资产（万元）
    # 投资经验
    experience_years: int
    # 创建时间
    created_at: str
    # 更新时间
    updated_at: str
    # 额外信息
    metadata: dict[str, Any] = field(default_factory=dict)


class RiskQuestionnaire:
    """风险问卷评估器"""

    # 风险评估问题
    QUESTIONS = [
        {
            "id": "q1",
            "question": "您的年龄范围是？",
            "options": [
                {"text": "60岁以上", "score": 1},
                {"text": "50-60岁", "score": 2},
                {"text": "40-50岁", "score": 3},
                {"text": "30-40岁", "score": 4},
                {"text": "30岁以下", "score": 5},
            ],
        },
        {
            "id": "q2",
            "question": "您的投资经验如何？",
            "options": [
                {"text": "无投资经验", "score": 1},
                {"text": "少于1年", "score": 2},
                {"text": "1-3年", "score": 3},
                {"text": "3-5年", "score": 4},
                {"text": "5年以上", "score": 5},
            ],
        },
        {
            "id": "q3",
            "question": "您能接受的最大亏损是多少？",
            "options": [
                {"text": "不能接受亏损", "score": 1},
                {"text": "5%以内", "score": 2},
                {"text": "10%以内", "score": 3},
                {"text": "20%以内", "score": 4},
                {"text": "超过20%", "score": 5},
            ],
        },
        {
            "id": "q4",
            "question": "如果您的投资下跌20%，您会怎么做？",
            "options": [
                {"text": "全部卖出", "score": 1},
                {"text": "卖出部分", "score": 2},
                {"text": "持有不动", "score": 3},
                {"text": "逢低加仓", "score": 4},
                {"text": "大幅加仓", "score": 5},
            ],
        },
        {
            "id": "q5",
            "question": "您的投资目标是什么？",
            "options": [
                {"text": "资产保值", "score": 1},
                {"text": "稳健增值", "score": 2},
                {"text": "均衡成长", "score": 3},
                {"text": "积极成长", "score": 4},
                {"text": "追求高收益", "score": 5},
            ],
        },
    ]

    def assess(self, answers: dict[str, int]) -> RiskAssessment:
        """
        根据问卷答案评估风险承受能力

        Args:
            answers: 问题ID到选项索引的映射

        Returns:
            风险评估结果
        """
        total_score = 0
        risk_factors = {}

        for question in self.QUESTIONS:
            q_id = question["id"]
            option_idx = answers.get(q_id, 0)
            options = question["options"]

            if 0 <= option_idx < len(options):
                score = options[option_idx]["score"]
                total_score += score
                risk_factors[q_id] = score

        # 平均分转换为1-100
        avg_score = total_score / len(self.QUESTIONS)
        final_score = int(avg_score * 20)

        # 确定风险承受能力
        if final_score <= 20:
            tolerance = RiskTolerance.CONSERVATIVE
            max_dd = -5
            vol_pref = "低波动"
        elif final_score <= 40:
            tolerance = RiskTolerance.MODERATELY_CONSERVATIVE
            max_dd = -10
            vol_pref = "中低波动"
        elif final_score <= 60:
            tolerance = RiskTolerance.BALANCED
            max_dd = -15
            vol_pref = "中等波动"
        elif final_score <= 80:
            tolerance = RiskTolerance.MODERATELY_AGGRESSIVE
            max_dd = -25
            vol_pref = "中高波动"
        else:
            tolerance = RiskTolerance.AGGRESSIVE
            max_dd = -40
            vol_pref = "高波动"

        return RiskAssessment(
            score=final_score,
            tolerance=tolerance,
            max_drawdown_acceptable=max_dd,
            volatility_preference=vol_pref,
            risk_factors=risk_factors,
        )

    def get_questions(self) -> list[dict]:
        """获取问卷问题"""
        return [
            {
                "id": q["id"],
                "question": q["question"],
                "options": [opt["text"] for opt in q["options"]],
            }
            for q in self.QUESTIONS
        ]


class StyleAnalyzer:
    """投资风格分析器"""

    def analyze(
        self,
        holding_history: list[dict] | None = None,
        trading_behavior: dict[str, Any] | None = None,
    ) -> InvestmentStyle:
        """
        分析用户投资风格

        Args:
            holding_history: 持仓历史
            trading_behavior: 交易行为数据

        Returns:
            投资风格
        """
        # 如果没有数据，返回平衡型
        if not holding_history and not trading_behavior:
            return InvestmentStyle.BALANCED

        # 简化分析：基于交易频率和持仓类型
        if trading_behavior:
            avg_holding_days = trading_behavior.get("avg_holding_days", 90)
            turnover_rate = trading_behavior.get("turnover_rate", 0.5)

            if avg_holding_days < 30 or turnover_rate > 2:
                return InvestmentStyle.MOMENTUM
            elif avg_holding_days > 365:
                return InvestmentStyle.VALUE

        # 基于持仓类型判断
        if holding_history:
            fund_types = [h.get("fund_type", "") for h in holding_history]
            growth_count = sum(1 for t in fund_types if "成长" in t or "科技" in t)
            value_count = sum(1 for t in fund_types if "价值" in t or "红利" in t)
            income_count = sum(1 for t in fund_types if "债券" in t or "货币" in t)

            if income_count > len(fund_types) * 0.5:
                return InvestmentStyle.INCOME
            elif growth_count > value_count:
                return InvestmentStyle.GROWTH
            elif value_count > growth_count:
                return InvestmentStyle.VALUE

        return InvestmentStyle.BALANCED


class ProfileManager:
    """
    用户画像管理器

    整合风险评估、风格分析、偏好管理等功能。
    """

    def __init__(self, storage_path: str | Path | None = None):
        """
        初始化画像管理器

        Args:
            storage_path: 画像存储路径，默认为 ~/.fund_cli/profiles
        """
        if storage_path:
            self._storage_path = Path(storage_path)
        else:
            # 使用默认路径 ~/.fund_cli/profiles
            self._storage_path = Path.home() / ".fund_cli" / "profiles"

        # 确保目录存在
        self._storage_path.mkdir(parents=True, exist_ok=True)

        self._questionnaire = RiskQuestionnaire()
        self._style_analyzer = StyleAnalyzer()

    def create_profile(
        self,
        user_id: str,
        name: str,
        risk_answers: dict[str, int],
        investment_goal: InvestmentGoal,
        investment_horizon: InvestmentHorizon,
        total_assets: float = 100.0,
        experience_years: int = 1,
        preferences: InvestmentPreferences | None = None,
    ) -> UserProfile:
        """
        创建用户画像

        Args:
            user_id: 用户ID
            name: 用户名
            risk_answers: 风险问卷答案
            investment_goal: 投资目标
            investment_horizon: 投资期限
            total_assets: 总资产（万元）
            experience_years: 投资经验（年）
            preferences: 投资偏好

        Returns:
            用户画像
        """
        from datetime import datetime

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 风险评估
        risk_assessment = self._questionnaire.assess(risk_answers)

        # 投资风格
        investment_style = self._infer_style_from_goal(investment_goal)

        # 默认偏好
        if preferences is None:
            preferences = self._get_default_preferences(risk_assessment)

        profile = UserProfile(
            user_id=user_id,
            name=name,
            risk_assessment=risk_assessment,
            investment_goal=investment_goal,
            investment_horizon=investment_horizon,
            investment_style=investment_style,
            preferences=preferences,
            total_assets=total_assets,
            experience_years=experience_years,
            created_at=now,
            updated_at=now,
        )

        # 保存画像
        if self._storage_path:
            self._save_profile(profile)

        return profile

    def get_questionnaire(self) -> list[dict]:
        """获取风险问卷"""
        return self._questionnaire.get_questions()

    def assess_risk(self, answers: dict[str, int]) -> RiskAssessment:
        """评估风险承受能力"""
        return self._questionnaire.assess(answers)

    def analyze_style(
        self,
        holding_history: list[dict] | None = None,
        trading_behavior: dict[str, Any] | None = None,
    ) -> InvestmentStyle:
        """分析投资风格"""
        return self._style_analyzer.analyze(holding_history, trading_behavior)

    def get_current_profile(self) -> UserProfile | None:
        """获取当前用户画像（加载最近创建的画像）"""
        if not self._storage_path:
            return None

        try:
            # 查找所有画像文件
            profile_files = list(self._storage_path.glob("*.json"))
            if not profile_files:
                return None

            # 按修改时间排序，获取最新的
            profile_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest_file = profile_files[0]

            with open(latest_file, encoding="utf-8") as f:
                data = json.load(f)

            return self._dict_to_profile(data)
        except Exception as e:
            logger.error(f"加载当前用户画像失败: {e}")
            return None

    def load_profile(self, user_id: str) -> UserProfile | None:
        """加载用户画像"""
        if not self._storage_path:
            return None

        profile_file = self._storage_path / f"{user_id}.json"
        if not profile_file.exists():
            return None

        try:
            with open(profile_file, encoding="utf-8") as f:
                data = json.load(f)

            return self._dict_to_profile(data)
        except Exception as e:
            logger.error(f"加载用户画像失败: {e}")
            return None

    def update_profile(self, profile: UserProfile) -> None:
        """更新用户画像"""
        from datetime import datetime

        profile.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if self._storage_path:
            self._save_profile(profile)

    def _infer_style_from_goal(self, goal: InvestmentGoal) -> InvestmentStyle:
        """从投资目标推断风格"""
        mapping = {
            InvestmentGoal.WEALTH_PRESERVATION: InvestmentStyle.INCOME,
            InvestmentGoal.STEADY_INCOME: InvestmentStyle.VALUE,
            InvestmentGoal.BALANCED_GROWTH: InvestmentStyle.BALANCED,
            InvestmentGoal.AGGRESSIVE_GROWTH: InvestmentStyle.GROWTH,
            InvestmentGoal.SPECULATIVE: InvestmentStyle.MOMENTUM,
        }
        return mapping.get(goal, InvestmentStyle.BALANCED)

    def _get_default_preferences(self, risk: RiskAssessment) -> InvestmentPreferences:
        """获取默认偏好"""
        if risk.tolerance == RiskTolerance.CONSERVATIVE:
            return InvestmentPreferences(
                preferred_fund_types=["债券型", "货币型"],
                preferred_sectors=["银行", "公用事业"],
                excluded_sectors=["科技", "新能源"],
                min_fund_scale=10,
                max_fund_scale=500,
                preferred_managers=[],
                esg_preference=False,
            )
        elif risk.tolerance == RiskTolerance.AGGRESSIVE:
            return InvestmentPreferences(
                preferred_fund_types=["股票型", "指数型"],
                preferred_sectors=["科技", "新能源", "医药"],
                excluded_sectors=[],
                min_fund_scale=5,
                max_fund_scale=1000,
                preferred_managers=[],
                esg_preference=False,
            )
        else:
            return InvestmentPreferences(
                preferred_fund_types=["混合型", "股票型", "债券型"],
                preferred_sectors=["消费", "医药", "金融"],
                excluded_sectors=[],
                min_fund_scale=10,
                max_fund_scale=500,
                preferred_managers=[],
                esg_preference=False,
            )

    def _save_profile(self, profile: UserProfile) -> None:
        """保存用户画像"""
        if not self._storage_path:
            return

        self._storage_path.mkdir(parents=True, exist_ok=True)
        profile_file = self._storage_path / f"{profile.user_id}.json"

        data = self._profile_to_dict(profile)
        with open(profile_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _profile_to_dict(self, profile: UserProfile) -> dict:
        """画像转字典"""
        return {
            "user_id": profile.user_id,
            "name": profile.name,
            "risk_assessment": {
                "score": profile.risk_assessment.score,
                "tolerance": profile.risk_assessment.tolerance.value,
                "max_drawdown_acceptable": profile.risk_assessment.max_drawdown_acceptable,
                "volatility_preference": profile.risk_assessment.volatility_preference,
                "risk_factors": profile.risk_assessment.risk_factors,
            },
            "investment_goal": profile.investment_goal.value,
            "investment_horizon": profile.investment_horizon.value,
            "investment_style": profile.investment_style.value,
            "preferences": {
                "preferred_fund_types": profile.preferences.preferred_fund_types,
                "preferred_sectors": profile.preferences.preferred_sectors,
                "excluded_sectors": profile.preferences.excluded_sectors,
                "min_fund_scale": profile.preferences.min_fund_scale,
                "max_fund_scale": profile.preferences.max_fund_scale,
                "preferred_managers": profile.preferences.preferred_managers,
                "esg_preference": profile.preferences.esg_preference,
            },
            "total_assets": profile.total_assets,
            "experience_years": profile.experience_years,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at,
            "metadata": profile.metadata,
        }

    def _dict_to_profile(self, data: dict) -> UserProfile:
        """字典转画像"""
        risk_data = data.get("risk_assessment", {})
        pref_data = data.get("preferences", {})

        return UserProfile(
            user_id=data["user_id"],
            name=data["name"],
            risk_assessment=RiskAssessment(
                score=risk_data.get("score", 50),
                tolerance=RiskTolerance(risk_data.get("tolerance", "平衡型")),
                max_drawdown_acceptable=risk_data.get("max_drawdown_acceptable", -15),
                volatility_preference=risk_data.get("volatility_preference", "中等波动"),
                risk_factors=risk_data.get("risk_factors", {}),
            ),
            investment_goal=InvestmentGoal(data.get("investment_goal", "均衡成长")),
            investment_horizon=InvestmentHorizon(data.get("investment_horizon", "中期（1-3年）")),
            investment_style=InvestmentStyle(data.get("investment_style", "平衡型")),
            preferences=InvestmentPreferences(
                preferred_fund_types=pref_data.get("preferred_fund_types", []),
                preferred_sectors=pref_data.get("preferred_sectors", []),
                excluded_sectors=pref_data.get("excluded_sectors", []),
                min_fund_scale=pref_data.get("min_fund_scale", 10),
                max_fund_scale=pref_data.get("max_fund_scale", 500),
                preferred_managers=pref_data.get("preferred_managers", []),
                esg_preference=pref_data.get("esg_preference", False),
            ),
            total_assets=data.get("total_assets", 100),
            experience_years=data.get("experience_years", 1),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            metadata=data.get("metadata", {}),
        )

    def format_profile(self, profile: UserProfile) -> str:
        """格式化用户画像"""
        lines = ["# 用户画像\n"]

        lines.append("## 基本信息")
        lines.append(f"- 用户ID: {profile.user_id}")
        lines.append(f"- 用户名: {profile.name}")
        lines.append(f"- 总资产: {profile.total_assets:.2f}万元")
        lines.append(f"- 投资经验: {profile.experience_years}年")
        lines.append("")

        lines.append("## 风险评估")
        lines.append(f"- 风险评分: {profile.risk_assessment.score}/100")
        lines.append(f"- 风险类型: {profile.risk_assessment.tolerance.value}")
        lines.append(f"- 可接受最大回撤: {abs(profile.risk_assessment.max_drawdown_acceptable):.0f}%")
        lines.append(f"- 波动偏好: {profile.risk_assessment.volatility_preference}")
        lines.append("")

        lines.append("## 投资特征")
        lines.append(f"- 投资目标: {profile.investment_goal.value}")
        lines.append(f"- 投资期限: {profile.investment_horizon.value}")
        lines.append(f"- 投资风格: {profile.investment_style.value}")
        lines.append("")

        lines.append("## 投资偏好")
        lines.append(f"- 偏好基金类型: {', '.join(profile.preferences.preferred_fund_types) or '无'}")
        lines.append(f"- 偏好行业: {', '.join(profile.preferences.preferred_sectors) or '无'}")
        lines.append(f"- 排除行业: {', '.join(profile.preferences.excluded_sectors) or '无'}")
        lines.append(f"- 基金规模范围: {profile.preferences.min_fund_scale}-{profile.preferences.max_fund_scale}亿")

        return "\n".join(lines)


def create_user_profile(
    user_id: str,
    name: str,
    risk_answers: dict[str, int],
    investment_goal: str = "均衡成长",
    investment_horizon: str = "中期（1-3年）",
) -> UserProfile:
    """创建用户画像便捷函数"""
    manager = ProfileManager()
    return manager.create_profile(
        user_id=user_id,
        name=name,
        risk_answers=risk_answers,
        investment_goal=InvestmentGoal(investment_goal),
        investment_horizon=InvestmentHorizon(investment_horizon),
    )
