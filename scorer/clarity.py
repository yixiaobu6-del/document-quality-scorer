"""
内部文档质量评分 - 清晰度评分
评估文档结构、语言表达和格式规范
"""

import math
import re


class ClarityScorer:
    """清晰度评分器"""

    def __init__(self):
        self.results = {}

    def score(self, content: str, title: str = '') -> dict:
        """
        评估文档清晰度

        Args:
            content: 文档内容
            title: 文档标题

        Returns:
            {
                'score': 总分,
                'details': 各维度评分,
                'issues': 问题列表,
                'suggestions': 改进建议
            }
        """
        if not content:
            return self._empty_result()

        structure_score = self._score_structure(content)
        readability_score = self._score_readability(content)
        formatting_score = self._score_formatting(content)

        total = structure_score['score'] + readability_score['score'] + formatting_score['score']

        max_possible = 10 + 10 + 10
        normalized = round(total / max_possible * 100, 1)

        issues = []
        issues.extend(structure_score.get('issues', []))
        issues.extend(readability_score.get('issues', []))
        issues.extend(formatting_score.get('issues', []))

        suggestions = self._generate_suggestions(issues)

        return {
            'score': normalized,
            'max_score': 100,
            'weight': 0.30,
            'categories': {
                'structure': structure_score,
                'readability': readability_score,
                'formatting': formatting_score
            },
            'issues': issues[:10],
            'suggestions': suggestions
        }

    def _empty_result(self) -> dict:
        return {
            'score': 0,
            'max_score': 100,
            'weight': 0.30,
            'categories': {},
            'issues': ['文档内容为空'],
            'suggestions': ['请提供文档内容进行评估']
        }

    def _score_structure(self, content: str) -> dict:
        """评估结构清晰度"""
        score = 0
        issues = []

        # 检查标题
        h1_count = len(re.findall(r'^#\s+.+', content, re.MULTILINE))
        h2_count = len(re.findall(r'^##\s+.+', content, re.MULTILINE))
        h3_count = len(re.findall(r'^###\s+.+', content, re.MULTILINE))

        if h1_count == 0:
            issues.append('缺少一级标题')
        elif h1_count == 1:
            score += 3
        else:
            score += 2
            issues.append('建议只使用一个一级标题')

        if h2_count >= 2:
            score += min(h2_count * 2, 4)
        elif h2_count == 1:
            score += 1

        # 检查段落
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if len(paragraphs) >= 3:
            score += 3
        elif len(paragraphs) >= 1:
            score += 1
            issues.append('段落数量较少，建议增加内容划分')

        return {
            'score': min(score, 10),
            'max_score': 10,
            'details': {
                'heading_h1': h1_count,
                'heading_h2': h2_count,
                'heading_h3': h3_count,
                'paragraph_count': len(paragraphs)
            },
            'issues': issues
        }

    def _score_readability(self, content: str) -> dict:
        """评估语言可读性"""
        score = 10
        issues = []

        sentences = re.split(r'[。！？\n]', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]

        if not sentences:
            return {'score': 0, 'max_score': 10, 'details': {}, 'issues': ['无有效句子']}

        # 计算平均句长
        lengths = [len(s) for s in sentences]
        avg_length = sum(lengths) / len(lengths)

        if avg_length > 50:
            score -= 3
            issues.append(f'平均句长{avg_length:.0f}字，偏长，建议拆分长句')
        elif avg_length > 35:
            score -= 1
            issues.append(f'平均句长{avg_length:.0f}字，建议适当拆分')
        elif avg_length < 10:
            score -= 1
            issues.append('句子偏短，建议适当丰富句式')

        # 检查长句
        long_sentences = [s for s in sentences if len(s) > 60]
        long_ratio = len(long_sentences) / len(sentences)
        if long_ratio > 0.3:
            score -= 2
            issues.append(f'存在{len(long_sentences)}个超长句（>60字），建议拆分')
        elif long_ratio > 0.1:
            score -= 1

        # 检查标点多样性
        punctuations = set()
        for c in content:
            if c in '，。！？；：、""''（）':
                punctuations.add(c)
        if len(punctuations) < 5:
            score -= 2
            issues.append('标点符号使用单一，建议丰富标点类型')

        # 检查口语化表达
        informal = ['然后', '就是说', '反正', '那个', '这个']
        informal_count = sum(content.count(w) for w in informal)
        if informal_count > 3:
            score -= 2
            issues.append('存在较多口语化表达，建议使用书面语')

        return {
            'score': max(0, min(score, 10)),
            'max_score': 10,
            'details': {
                'sentence_count': len(sentences),
                'avg_length': round(avg_length, 1),
                'long_sentence_ratio': round(long_ratio, 2),
                'punctuation_types': len(punctuations)
            },
            'issues': issues
        }

    def _score_formatting(self, content: str) -> dict:
        """评估格式规范性"""
        score = 10
        issues = []

        # 检查列表
        ul_count = len(re.findall(r'^- .+', content, re.MULTILINE))
        ol_count = len(re.findall(r'^\d+\. .+', content, re.MULTILINE))

        if ul_count + ol_count == 0:
            score -= 2
            issues.append('建议使用列表来组织并列信息')

        # 检查代码块
        code_blocks = len(re.findall(r'```', content))
        if code_blocks > 0 and code_blocks % 2 != 0:
            score -= 2
            issues.append('代码块格式不正确，首尾未对称')

        # 检查加粗
        bold_count = len(re.findall(r'\*\*.+?\*\*', content))
        if bold_count == 0:
            score -= 1
            issues.append('建议对关键词使用加粗标记')

        # 检查空白行
        empty_lines = content.count('\n\n\n')
        if empty_lines > 3:
            score -= 2
            issues.append('存在过多连续空行，影响阅读体验')

        # 检查表格
        table_rows = len(re.findall(r'\|.+\|', content))
        if table_rows == 0:
            score -= 1

        return {
            'score': max(0, min(score, 10)),
            'max_score': 10,
            'details': {
                'unordered_lists': ul_count,
                'ordered_lists': ol_count,
                'code_blocks': code_blocks // 2,
                'bold_formatting': bold_count,
                'table_rows': table_rows
            },
            'issues': issues
        }

    def _generate_suggestions(self, issues: list) -> list:
        """生成改进建议"""
        suggestion_map = {
            '缺少一级标题': '添加一个文档标题（使用 # 标记），明确文档主题',
            '段落数量较少': '将内容划分为多个段落，每段聚焦一个要点',
            '平均句长': '长句改为短句组合，每句话只表达一个核心意思',
            '超长句': '将超过60字的句子拆分为2-3个短句，提高可读性',
            '标点符号使用单一': '丰富标点类型，善用分号、冒号、引号等',
            '口语化表达': '将"然后""就是说"等口语词改为书面化表达',
            '建议使用列表': '对于并列信息，使用无序列表(-)或有序列表(1.)组织',
            '代码块格式不正确': '确保代码块使用对称的 ``` 标记',
            '关键词使用加粗': '对重要术语和概念使用 **加粗** 标记',
            '存在过多连续空行': '控制段落间的空行数量，一般1-2行即可'
        }

        suggestions = []
        for issue in issues:
            for key, suggestion in suggestion_map.items():
                if key in issue:
                    suggestions.append(suggestion)
                    break
            else:
                suggestions.append(f'建议改进：{issue}')

        return list(set(suggestions))[:5]


if __name__ == '__main__':
    from .score import DocumentScorer

    scorer = ClarityScorer()
    sample = """# 内部文档质量标准

本文档定义了内部文档的质量评估标准。

## 文档结构

一篇好的文档应该具备清晰的层级结构。
标题应该准确反映内容。

## 语言表达

使用简洁明了的语言。
避免过长和复杂的句子。

### 注意事项
- 保持段落简洁
- 使用列表组织信息
- 适当使用加粗强调"""

    result = scorer.score(sample)
    print(f"清晰度评分: {result['score']}/100")
    print(f"问题数: {len(result['issues'])}")
    for s in result['suggestions']:
        print(f"  - {s}")