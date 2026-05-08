# 茎叶图 Stem-and-Leaf Plot

## 基本信息

| 属性 | 内容 |
|------|------|
| 图表分类 | 分布 Distribution |
| 书章节 | Ch6 |
| 感知排名 | ★★★（文本输出） |

## 数据要求

**必需列**

| 列名 | 类型 | 说明 |
|------|------|------|
| values_col | Numeric | 连续变量观测值 |

## 硬性约束

1. 文本输出（非图形）
2. 适合小样本（<100）
3. 茎=高位，叶=低位数字

## 适用场景

• 小样本探索性分析
• 教学/手工计算场景

## 不适用场景

• 大样本（>100）→直方图

## 使用示例

```python
from charts.stem_leaf import generate
text = generate(df, values_col='成绩', stem_digits=1)
print(text)
```

## 输出

`matplotlib.pyplot.Figure` 对象，调用 `.savefig()` / `.show()`
