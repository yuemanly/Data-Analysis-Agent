# 比例符号地图 Proportional Symbol

## 基本信息

| 属性 | 内容 |
|------|------|
| 图表分类 | 地理 Geospatial |
| 书章节 | Ch7 |
| 感知排名 | ★★★★（精确位置） |

## 数据要求

**必需列**

| 列名 | 类型 | 说明 |
|------|------|------|
| lon | Numeric | 经度 |
| lat | Numeric | 纬度 |
| value | Numeric | 符号大小权重 |

## 硬性约束

1. 符号面积（√r）而非半径编码数值（避免感知扭曲）
2. 适合点数据（城市/站点）
3. 颜色可编码第三变量

## 适用场景

• 城市/站点级别精确位置数据
• 多指标地理分布

## 不适用场景

• 面数据→等值区域图
• 大量重叠点→热力图

## 使用示例

```python
from charts.proportional_symbol import generate
generate(df, lon_col='经度', lat_col='纬度', value_col='销售额', color_col='产品类别')
```

## 输出

`matplotlib.pyplot.Figure` 对象，调用 `.savefig()` / `.show()`
