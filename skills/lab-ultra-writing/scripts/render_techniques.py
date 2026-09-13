"""Maintain the human-readable view of the single conditional-technique store."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'references/exposition-cards.json'
OUTPUT = ROOT / 'references/writing-techniques.md'
GROUPS = ['任务与组织', '对象与推导', '定义与口径', '选择与取舍', '计算与执行', '图表与叙述', '结果与边界', '归属与修订']


def render(data):
    cards = data['cards']
    lines = ['# 统一写作技巧', '',
             '从当前读者的理解困难选用，直接写成所需段落。已经清楚的内容保留；没有适合的卡可以自行组织。',
             '这些技巧说明如何表达，不选择算法，不规定章节、图表或句子数量，也不补造研究结果。', '',
             '## 先处理真正影响表达的分歧', '',
             '局部保真润色保留科学承诺，遇到实质矛盾单独指出；实质修订可按确定的任务事实修正受影响表达。',
             '不同结论先核对对象、分母、条件、信息时点和来源角色。条件不同则分别保留；同一命题确有矛盾且无法裁决时，保持未决，不以多数票、最新日期或流畅程度决定真伪。',
             '直观解释不能取代证明，内部一致性不能改称外部验证；验证活动可以描述，但要说清检查对象、参照和实际范围。',
             '何时先给结论、推导写多长、是否加图，按读者是否已具备必要定义和证据选择。详细裁决见[冲突与采用边界](conflict-decisions.md)。', '',
             '具体条件与来源归并见[条件细分检索](technique-variants.md)，按需检索，不全量加载。', '', '## 按解释任务选择', '', '| 任务 | 技巧 ID 与读者困难 |', '| --- | --- |']
    for group in GROUPS:
        items = [c for c in cards if c['group'] == group]
        for c in items:
            lines.append('| ' + group + ' | [' + c['id'] + '](#' + c['id'] + ')：' + c['reader_gap'].replace('|', '／') + ' |')
    lines += ['', '下面是同一JSON生成的可读视图；按需读取有关条目，不默认全量加载。原件来源、复核位置与已知弱点在[结构化技巧库](exposition-cards.json)的sources/underlying_evidence/source_weakness中。例子均为表达示例，不是当前题目的计算结果。', '']
    for group in GROUPS:
        lines += ['## ' + group, '']
        for c in cards:
            if c['group'] != group:
                continue
            lines += ['<a id="' + c['id'] + '"></a>', '### ' + c.get('title', c['id']), '',
                      '**读者困难：**' + c['reader_gap'], '', '**写作动作：**' + c['move'], '',
                      '**适用条件：**' + c['conditions'], '', '**先有这些依据：**' + '；'.join(c['evidence_needed']) + '。', '',
                      '**不要据此推出：**' + c['misuse'], '']
    return '\n'.join(lines).rstrip() + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='update the derived Markdown view; otherwise check only')
    args = parser.parse_args()
    data = json.loads(DATA.read_text(encoding='utf-8'))
    result = render(data)
    if args.write:
        OUTPUT.write_text(result, encoding='utf-8')
    equal = OUTPUT.is_file() and OUTPUT.read_text(encoding='utf-8') == result
    print(json.dumps({'matches_canonical': equal, 'cards': len(data['cards']),
                      'canonical_sha256': hashlib.sha256(DATA.read_bytes()).hexdigest(),
                      'scope': 'View consistency only, not semantic or scientific acceptance'}))
    raise SystemExit(0 if equal else 1)


if __name__ == '__main__':
    main()
