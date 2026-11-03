# Foundation 0 Bonus - 13 个 Python 小程序

题目要求见考核文档的 Bonus 部分。所有程序都可以直接 `python xxx.py` 运行，
交互式程序会读标准输入，演示型程序会直接打印结果。

## 基础 8 题

| 文件 | 题目 | 说明 |
| --- | --- | --- |
| [`basic1_sort_three.py`](basic1_sort_three.py) | 三个数由大到小输出 | 三种方式：`sorted`、纯条件判断、逐个取最大 |
| [`basic2_multiplication_table.py`](basic2_multiplication_table.py) | 九九乘法表 | 双层循环，`end="\t"` 对齐 |
| [`basic3_ol_replace.py`](basic3_ol_replace.py) | 判断并替换 "ol" → "fzu" | `str.replace` + 切片倒序 |
| [`basic4_filter_list.py`](basic4_filter_list.py) | 列表去字符串并升序 | `isinstance` 过滤，注意 `bool` 是 `int` 子类要排除 |
| [`basic5_student_dict.py`](basic5_student_dict.py) | 删除学号尾号为偶数的元素 | 字典推导式 |
| [`basic6_count_numbers.py`](basic6_count_numbers.py) | 统计数字出现次数 | `dict.get(key, 0) + 1` 计数模板 |
| [`basic7_product.py`](basic7_product.py) | 商品类 | 私有属性 `__xxx`、`display` / `income` / `setdata` |
| [`basic8_landlords_deal.py`](basic8_landlords_deal.py) | 斗地主发牌（无序） | `random.shuffle` + 切片，写四个 txt |

## 进阶 5 题

| 文件 | 题目 | 说明 |
| --- | --- | --- |
| [`adv1_timing_decorator.py`](adv1_timing_decorator.py) | 计时装饰器 | `functools.wraps` 保留元信息，`finally` 保证异常也打印结束时间 |
| [`adv2_landlords_deal_sorted.py`](adv2_landlords_deal_sorted.py) | 斗地主发牌（有序） | 以固定点数顺序表作为 `sorted` 的 key |
| [`adv3_matrix_comprehension.py`](adv3_matrix_comprehension.py) | 5x10 矩阵与转置 | 双层推导式；注意不能用 `[[1]*10]*5`（共享引用） |
| [`adv4_my_zoo.py`](adv4_my_zoo.py) | MyZoo 魔法方法 | `__eq__` 只看种类、`__len__` 求总数、无参构造 |
| [`adv5_password_regex.py`](adv5_password_regex.py) | 密码正则 | 6-18 位字母数字，必须用 `fullmatch` |

## 本地验证

```zsh
cd foundation/foundation0/bonus

# 交互式
python basic1_sort_three.py 3 1 2
python basic3_ol_replace.py

# 直接输出
python basic2_multiplication_table.py
python basic7_product.py
python basic8_landlords_deal.py
python adv4_my_zoo.py
python adv5_password_regex.py
```
