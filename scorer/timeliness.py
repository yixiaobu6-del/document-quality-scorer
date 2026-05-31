"""
内部文档质量评分 - 时效性评分
评估文档信息的新旧程度
"""

import re
from datetime import datetime


class TimelinessScorer:
    """时效性评分器"""

    def __init__(self):
        pass

    def score(self, content: str, title: str = '', metadata: dict = None) -> dict:
        """
        评估文档时效性

        Args:
            content: 文档内容
            title: 文档标题
            metadata: 元数据（创建时间、最后修改时间等）

        Returns:
            评分结果
        """
        if not content:
            return self._empty_result()

        metadata = metadata or {}

        version_score = self._score_version(content)
        accuracy_score = self._score_accuracy(content)
        maintenance_score = self._score_maintenance(content, metadata)

        total = version_score['score'] + accuracy_score['score'] + maintenance_score['score']
        max_possible = 12 + 10 + 8
        normalized = round(total / max_possible * 100, 1)

        issues = []
        issues.extend(version_score.get('issues', []))
        issues.extend(accuracy_score.get('issues', []))
        issues.extend(maintenance_score.get('issues', []))

        suggestions = self._generate_suggestions(issues)

        return {
            'score': normalized,
            'max_score': 100,
            'weight': 0.30,
            'categories': {
                'version': version_score,
                'accuracy': accuracy_score,
                'maintenance': maintenance_score
            },
            'issues': issues[:10],
            'suggestions': suggestions
        }

    def _empty_result(self) -> dict:
        return {
            'score': 0, 'max_score': 100, 'weight': 0.30,
            'categories': {}, 'issues': ['文档内容为空'],
            'suggestions': ['请提供文档内容进行评估']
        }

    def _score_version(self, content: str) -> dict:
        """评估版本最新程度"""
        score = 8
        issues = []

        # 检查版本号
        version_patterns = re.findall(r'v(\d+)\.(\d+)\.?(\d+)?', content)
        if version_patterns:
            major, minor, *_ = version_patterns[-1]
            major = int(major)
            if major > 0:
                score += 4
            if major == 0:
                score += 1
                issues.append('文档版本仍为0.x，可能还在早期阶段')
        else:
            score -= 2
            issues.append('未标注文档版本号')

        # 检查年份标记
        current_year = datetime.now().year
        year_mentions = re.findall(r'(\d{4})年', content)
        if year_mentions:
            latest_year = max(int(y) for y in year_mentions)
            if latest_year < current_year - 2:
                score -= 3
                issues.append(f'文档中引用的数据年份为{latest_year}年，建议更新')
            elif latest_year < current_year - 1:
                score -= 1
                issues.append(f'文档主要参考{latest_year}年的数据')

        # 检查过时表述
        outdated_patterns = [
            r'目前[^，。]{0,10}(暂未|尚未|还在)',
            r'即将(上线|发布|推出)',
            r'(预计|计划)(将于|在)\d{4}年',
        ]
        for pattern in outdated_patterns:
            matches = re.findall(pattern, content)
            if matches:
                score -= 2

        return {
            'score': max(0, min(score, 12)),
            'max_score': 12,
            'details': {
                'version_info': version_patterns[-1] if version_patterns else None,
                'latest_year_ref': latest_year if 'latest_year' in dir() else None
            },
            'issues': issues
        }

    def _score_accuracy(self, content: str) -> dict:
        """评估信息准确性"""
        score = 8
        issues = []

        # 检查数据引用
        data_patterns = re.findall(r'(\d+[.%]?)', content)
        if len(data_patterns) > 5:
            score += 2
            issues.append('有较多数据引用，请确保数据来源可靠且最新')

        # 检查绝对化表述
        absolute_words = ['永远', '绝对', '必然', '不可能', '完全']
        absolute_count = sum(content.count(w) for w in absolute_words)
        if absolute_count > 3:
            score -= 2
            issues.append('存在过度绝对化的表述，建议使用更谨慎的措辞')

        # 检查模糊表述
        vague_words = ['可能', '也许', '大概', '基本上', '一般来说']
        vague_count = sum(content.count(w) for w in vague_words)
        if vague_count > 5:
            score -= 2
            issues.append('存在较多模糊表述，建议补充具体信息')

        # 检查主观性表述
        subjective_words = ['我认为', '我觉得', '在我看来', '显然', '毫无疑问']
        subjective_count = sum(content.count(w) for w in subjective_words)
        if subjective_count > 2:
            score -= 2
            issues.append('主观性表述较多，建议保持客观中立')

        return {
            'score': max(0, min(score, 10)),
            'max_score': 10,
            'details': {
                'data_points': len(data_patterns) if 'data_patterns' in dir() else 0,
                'absolute_expr': absolute_count,
                'vague_expr': vague_count,
                'subjective_expr': subjective_count
            },
            'issues': issues
        }

    def _score_maintenance(self, content: str, metadata: dict) -> dict:
        """评估维护记录"""
        score = 5
        issues = []

        # 检查更新记录
        if '更新记录' in content or '变更记录' in content or 'Changelog' in content:
            score += 2
        else:
            issues.append('缺少更新/变更记录')

        # 检查最后修改时间
        last_modified = metadata.get('last_modified', '')
        if last_modified:
            try:
                modified_date = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
                days_since = (datetime.now() - modified_date).days
                if days_since < 30:
                    score += 1
                elif days_since > 365:
                    score -= 3
                    issues.append(f'文档已{days_since}天未更新，建议审查内容是否过时')
                elif days_since > 180:
                    score -= 1
                    issues.append(f'文档已{days_since}天未更新')
            except Exception:
                pass

        # 检查TODO/FIXME标记
        todo_count = content.count('TODO') + content.count('FIXME') + content.count('待补充')
        if todo_count > 0:
            score -= 1
            issues.append(f'文档中存在{todo_count}个待办标记（TODO/FIXME），需要处理')

        return {
            'score': max(0, min(score, 8)),
            'max_score': 8,
            'details': {
                'has_changelog': '更新记录' in content,
                'todo_markers': todo_count if 'todo_count' in dir() else 0
            },
            'issues': issues
        }

    def _generate_suggestions(self, issues: list) -> list:
        suggestions = []
        for issue in issues:
            if '版本' in issue:
                suggestions.append('为文档标注正式版本号（如v2.0.0）')
            if '数据' in issue and '年' in issue:
                suggestions.append('检查并更新文档中引用的数据年份')
            if '更新' in issue or '未更新' in issue:
                suggestions.append('审查文档内容的时效性，更新过时的信息')
            if '更新记录' in issue:
                suggestions.append('添加更新记录（Changelog）部分，记录每次变更')
            if '绝对化' in issue:
                suggestions.append('将绝对化表述改为更准确的表述方式')
            if '主观性' in issue:
                suggestions.append('减少主观判断，增加事实和数据支撑')
            if 'TODO' in issue:
                suggestions.append('完成文档中标记的待办事项（TODO）')

        return list(set(suggestions))[:5]


if __name__ == '__main__':
    scorer = TimelinessScorer()
    sample = """# API接口规范 v2.0

## 概述
本文档于2023年首次发布。

目前API接口规范已经基本完善。
必将持续优化接口设计。

## 更新记录
- 2024-01: 新增认证接口
- 2023-12: 修复分页参数描述
"""

    result = scorer.score(sample)
    print(f"时效性评分: {result['score']}/100")
    print(f"问题数: {len(result['issues'])}")
    for s in result['suggestions']:
        print(f"  - {s}")