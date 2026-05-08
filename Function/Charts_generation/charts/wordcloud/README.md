# 词云 Word Cloud

## 基本信息

| 属性 | 内容 |
|------|------|
| 图表分类 | 定性 Qualitative |
| 书章节 | Ch10 |
| 感知排名 | ★★（探索展示） |

## 数据要求

**必需列**

| 列名 | 类型 | 说明 |
|------|------|------|
| text_col | Text | 评论/文章内容列 |
| （或直接传文本）| str | 纯文本字符串 |

## 硬性约束

1. 停用词（the/a/的）需预先去除
2. 颜色辅助分组，非维度编码
3. 需要wordcloud库
4. 感知精度低，不适合精确分析

## 适用场景

• 快速探索性文本可视化
• 演示/报告（非严肃分析）

## 不适用场景

• 精确词频分析→表格
• 严肃报告→柱状图

## 使用示例

```python
from charts.wordcloud import generate
generate(df, text_col='评论内容')
generate('纯文本字符串内容')
```

## 输出

`matplotlib.pyplot.Figure` 对象，调用 `.savefig()` / `.show()`
