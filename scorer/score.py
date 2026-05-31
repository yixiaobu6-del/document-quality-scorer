"""
内部文档质量评分 - 综合评分
整合各维度评分生成综合评价
"""

import json
from pathlib import Path

from .clarity import ClarityScorer
from .completeness import CompletenessScorer
from .timeliness import TimelinessScorer


class DocumentScorer:
    """文档综合评分器"""

    def __init__(self):
        """初始化各维度评分器"""
        self.clarity_scorer = ClarityScorer()
        self.completeness_scorer = CompletenessScorer()
        self.timeliness_scorer = TimelinessScorer()

    def score(self, content: str, title: str = '',
              metadata: dict = None) -> dict:
        """
        对文档进行综合评分

        Args:
            content: 文档内容
            title: 文档标题
            metadata: 文档元数据

        Returns:
            综合评分结果
        """
        results = {
            'clarity': self.clarity_scorer.score(content, title),
            'completeness': self.completeness_scorer.score(content, title),
            'timeliness': self.timeliness_scorer.score(content, title, metadata)
        }

        # 计算加权总分
        total_weight = 0
        weighted_score = 0

        for key, result in results.items():
            weight = result.get('weight', 0.25)
            weighted_score += result['score'] * weight
            total_weight += weight

        overall = round(weighted_score / total_weight, 1) if total_weight > 0 else 0

        # 等级判定
        grade = self._determine_grade(overall)

        # 汇总所有问题
        all_issues = []
        for key, result in results.items():
            for issue in result.get('issues', []):
                all_issues.append({
                    'dimension': key,
                    'issue': issue
                })

        # 汇总所有建议
        all_suggestions = []
        for result in results.values():
            all_suggestions.extend(result.get('suggestions', []))

        return {
            'overall_score': overall,
            'max_score': 100,
            'grade': grade,
            'dimensions': results,
            'issues': all_issues[:15],
            'suggestions': list(set(all_suggestions))[:8]
        }

    def _determine_grade(self, score: float) -> str:
        """判定文档等级"""
        if score >= 90:
            return 'A - 优秀'
        elif score >= 75:
            return 'B - 良好'
        elif score >= 60:
            return 'C - 及格'
        elif score >= 40:
            return 'D - 需改进'
        else:
            return 'E - 不合格'

    def generate_report(self, result: dict) -> str:
        """生成可读报告"""
        report = []
        report.append("=" * 55)
        report.append("内部文档质量评分报告")
        report.append("=" * 55)
        report.append("")

        report.append(f"综合评分: {result['overall_score']}/100")
        report.append(f"等级: {result['grade']}")
        report.append("")

        # 各维度评分
        report.append("[各维度评分]")
        for key, dim in result['dimensions'].items():
            name_map = {
                'clarity': '清晰度 (30%)',
                'completeness': '完整度 (40%)',
                'timeliness': '时效性 (30%)'
            }
            report.append(f"  {name_map.get(key, key)}: {dim['score']}/100")
        report.append("")

        # 问题列表
        if result['issues']:
            report.append("[待改进问题]")
            for i, item in enumerate(result['issues'], 1):
                dim_name = {'clarity': '清晰度', 'completeness': '完整度', 'timeliness': '时效性'}
                report.append(f"  {i}. [{dim_name.get(item['dimension'], item['dimension'])}] {item['issue']}")
            report.append("")

        # 改进建议
        if result['suggestions']:
            report.append("[改进建议]")
            for i, s in enumerate(result['suggestions'], 1):
                report.append(f"  {i}. {s}")
            report.append("")

        report.append("=" * 55)
        return '\n'.join(report)


def batch_score(documents: list) -> list:
    """
    批量评分

    Args:
        documents: 文档列表，每项包含 'content', 'title', 'metadata'

    Returns:
        评分结果列表
    """
    scorer = DocumentScorer()
    results = []

    for doc in documents:
        result = scorer.score(
            content=doc.get('content', ''),
            title=doc.get('title', ''),
            metadata=doc.get('metadata', {})
        )
        results.append({
            'title': doc.get('title', ''),
            'score': result['overall_score'],
            'grade': result['grade'],
            'details': result
        })

    return results


if __name__ == '__main__':
    scorer = DocumentScorer()

    sample_doc = """# API接口规范 v2.0

## 概述
本文档定义了API接口的设计规范。
所有接口使用RESTful风格。

## 接口规范
请求和响应使用JSON格式。
Header需要包含认证信息。

### 请求格式
请求包含URL、Header和Body三个部分。

### 响应格式
响应包含status、data和message三个字段。

## 错误处理
系统会返回统一的错误响应格式。

## 更新记录
- 2024-01: 新增认证接口
"""

    result = scorer.score(sample_doc)
    report = scorer.generate_report(result)
    print(report)