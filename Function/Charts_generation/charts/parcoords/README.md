# 平行坐标图 Parallel Coordinates

## 基本信息

| 属性 | 内容 |
|------|------|
| 图表分类 | 关系 Relationships |
| 书章节 | Ch8 |
| 感知排名 | ★★★（多维关系发现） |

## 数据要求

**必需列**

| 列名 | 类型 | 说明 |
|------|------|------|
| columns | list[Numeric] | 各维度轴（≥3列）|
| color_col(可选) | Category | 颜色分组 |

## 硬性约束

1. 各维度数值范围需标准化（Min-Max或Z-score）
2. 维度数≥3
3. 交叉线表示相关性：平行=正相关，交叉=负相关

## 适用场景

• 多维数据关系发现（≥4维）
• 分组模式识别
• 异常实体发现

## 不适用场景

• 维度<3→散点图
• 精确相关强度→相关系数矩阵

## 使用示例

```python
from charts.parcoords import generate
generate(df, columns=['身高','体重','血压','血糖'], color_col='性别')
```

## 输出

`matplotlib.pyplot.Figure` 对象，调用 `.savefig()` / `.show()`
