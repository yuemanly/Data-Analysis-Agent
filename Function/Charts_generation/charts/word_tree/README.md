# 词树 Word Tree

## 基本信息

| 属性 | 内容 |
|------|------|
| 图表分类 | 定性 Qualitative |
| 书章节 | Ch10 |
| 感知排名 | ★★★（文本接龙） |

## 数据要求

**必需列**

| 参数 | 类型 | 说明 |
|------|------|------|
| text | str | 完整文本内容 |
| root_word | str | 起始词 |

## 硬性约束

1. 文本需要预先分词
2. 展示词的分支结构（宽度=频率）

## 适用场景

• 歌词/引文结构展示
• 文本接龙模式识别

## 不适用场景

• 精确词频→柱状图
• 长文本→词云

## 使用示例

```python
from charts.word_tree import generate
generate(text='歌词/引文全文', root_word='关键词')
```

## 输出

`matplotlib.pyplot.Figure` 对象，调用 `.savefig()` / `.show()`
