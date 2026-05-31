"""
内部文档质量评分 - 完整度评分
评估文档内容的覆盖完整性
"""

import re


class CompletenessScorer:
    """完整度评分器"""

    def __init__(self):
        self.results = {}

    def score(self, content: str, title: str = '') -> dict:
        """
        评估文档完整度

        Args:
            content: 文档内容
            title: 文档标题

        Returns:
            评分结果
        """
        if not content:
            return self._empty_result()

        coverage_score = self._score_coverage(content)
        example_score = self._score_examples(content)
        reference_score = self._score_references(content)
        navigation_score = self._score_navigation(content)

        total = coverage_score['score'] + example_score['score'] + reference_score['score'] + navigation_score['score']
        max_possible = 15 + 10 + 8 + 7
        normalized = round(total / max_possible * 100, 1)

        issues = []
        issues.extend(coverage_score.get('issues', []))
        issues.extend(example_score.get('issues', []))
        issues.extend(reference_score.get('issues', []))
        issues.extend(navigation_score.get('issues', []))

        suggestions = self._generate_suggestions(coverage_score, example_score, reference_score)

        return {
            'score': normalized,
            'max_score': 100,
            'weight': 0.40,
            'categories': {
                'coverage': coverage_score,
                'examples': example_score,
                'references': reference_score,
                'navigation': navigation_score
            },
            'issues': issues[:10],
            'suggestions': suggestions
        }

    def _empty_result(self) -> dict:
        return {
            'score': 0, 'max_score': 100, 'weight': 0.40,
            'categories': {}, 'issues': ['文档内容为空'], 'suggestions': ['请提供文档内容进行评估']
        }

    def _score_coverage(self, content: str) -> dict:
        """评估内容覆盖度"""
        score = 0
        issues = []

        lines = content.split('\n')
        words = re.findall(r'[\u4e00-\u9fff\w]+', content)

        # 字数检查
        char_count = len(re.sub(r'[\s#*\-`\[\]()|]', '', content))
        if char_count >= 2000:
            score += 6
        elif char_count >= 1000:
            score += 4
        elif char_count >= 500:
            score += 2
        else:
            issues.append(f'文档内容偏少（{char_count}字），建议补充详细说明')

        # 段落丰富度
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if len(paragraphs) >= 8:
            score += 4
        elif len(paragraphs) >= 4:
            score += 2
        else:
            issues.append(f'段落偏少（{len(paragraphs)}段），建议增加内容层次')

        # 关键要素检查
        key_elements = {
            '目的': ['目的', '目标', '概述', '简介', '背景'],
            '范围': ['范围', '适用', '场景'],
            '定义': ['定义', '概念', '术语', '说明'],
            '流程': ['流程', '步骤', '方法', '操作'],
            '规范': ['规范', '标准', '要求', '规则'],
        }

        found_elements = []
        for element, patterns in key_elements.items():
            for pattern in patterns:
                if pattern in content:
                    found_elements.append(element)
                    break

        coverage_ratio = len(found_elements) / len(key_elements)
        score += round(coverage_ratio * 5)

        missing = set(key_elements.keys()) - set(found_elements)
        for m in missing:
            issues.append(f'缺少"{m}"相关内容的说明')

        return {
            'score': min(score, 15),
            'max_score': 15,
            'details': {
                'char_count': char_count,
                'paragraph_count': len(paragraphs),
                'word_count': len(words),
                'elements_found': found_elements,
                'coverage_ratio': round(coverage_ratio, 2)
            },
            'issues': issues
        }

    def _score_examples(self, content: str) -> dict:
        """评估示例丰富度"""
        score = 0
        issues = []

        # 检查"例如"
        example_count = content.count('例如') + content.count('比如') + content.count('示例')

        # 检查代码块
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        code_count = len(code_blocks)

        # 检查案例
        case_count = content.count('案例') + content.count('实例')

        total_examples = example_count + code_count + case_count

        if total_examples >= 5:
            score += 8
        elif total_examples >= 3:
            score += 5
        elif total_examples >= 1:
            score += 2
        else:
            issues.append('缺少示例说明，建议补充实际案例帮助理解')

        # 检查示例标注
        if code_count > 0:
            score += 2

        return {
            'score': min(score, 10),
            'max_score': 10,
            'details': {
                'example_mentions': example_count,
                'code_blocks': code_count,
                'case_studies': case_count,
                'total_examples': total_examples
            },
            'issues': issues
        }

    def _score_references(self, content: str) -> dict:
        """评估引用完整性"""
        score = 0
        issues = []

        # 链接检查
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        link_count = len(links)

        # 检查是否外部引用
        external_links = 0
        for text, url in links:
            if url.startswith('http'):
                external_links += 1

        if link_count > 0:
            score += 3
            # 检查链接描述
            for text, url in links:
                if len(text) < 2:
                    score -= 1
                    issues.append('存在描述过短的链接（建议给链接添加有意义的描述文本）')

        # 检查参考文档
        ref_patterns = ['参考', '引用来源', '参考文献', '相关资料', 'See Also']
        ref_count = sum(content.count(p) for p in ref_patterns)

        if ref_count > 0:
            score += 3
        else:
            issues.append('建议添加"参考资料"部分')

        # 检查版本信息
        version_patterns = re.findall(r'v[\d.]+|版本[\d.]+', content)
        if version_patterns:
            score += 2
        else:
            issues.append('建议标注文档版本号')

        return {
            'score': min(score, 8),
            'max_score': 8,
            'details': {
                'link_count': link_count,
                'external_links': external_links,
                'reference_sections': ref_count,
                'version_markers': len(version_patterns)
            },
            'issues': issues
        }

    def _score_navigation(self, content: str) -> dict:
        """评估导航和索引"""
        score = 0
        issues = []

        # 目录检查
        if '# ' in content:
            if '目录' in content[:200]:
                score += 2

            # 标题层级丰富度
            h_levels = set()
            for line in content.split('\n'):
                if line.startswith('#'):
                    level = len(line.split(' ')[0])
                    h_levels.add(level)

            if len(h_levels) >= 3:
                score += 3
            elif len(h_levels) >= 2:
                score += 1
            else:
                issues.append('标题层级单一，建议增加子标题')

        # 交叉引用
        cross_refs = re.findall(r'参见|详见|参照|如上|如下', content)
        if cross_refs:
            score += 2

        return {
            'score': min(score, 7),
            'max_score': 7,
            'details': {
                'heading_levels': sorted(h_levels) if 'h_levels' in dir() else [],
                'cross_references': len(cross_refs) if 'cross_refs' in dir() else 0
            },
            'issues': issues
        }

    def _generate_suggestions(self, coverage: dict, examples: dict,
                               references: dict) -> list:
        suggestions = []
        if coverage.get('issues'):
            suggestions.append('补充文档的核心要素（目的、范围、定义、流程等）')
        if examples.get('score', 10) < 5:
            suggestions.append('为关键概念和操作步骤补充示例和案例')
        if references.get('score', 10) < 4:
            suggestions.append('添加参考资料部分和版本号标记')
        return suggestions[:5]


if __name__ == '__main__':
    scorer = CompletenessScorer()
    sample = """# API接口规范

## 概述
本文档定义了API接口的设计规范。

## 接口规范
所有接口使用RESTful风格。
请求和响应使用JSON格式。

### 请求格式
请求包含URL、Header和Body三个部分。
Header需要包含认证信息。

### 响应格式
响应包含status、data和message三个字段。
"""

    result = scorer.score(sample)
    print(f"完整度评分: {result['score']}/100")
    print(f"问题数: {len(result['issues'])}")
    for issue in result['issues'][:5]:
        print(f"  - {issue}")