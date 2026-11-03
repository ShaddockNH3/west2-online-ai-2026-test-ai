# 作业 4 - OI 五题

五道题都用 Python 3.12 实现，统一从标准输入读取、向标准输出写出，入口统一包在 `main()` 里，方便在 oj 上交或者本地直接跑。

| 文件 | 题目 | 思路 |
| --- | --- | --- |
| [`p1001_a_plus_b.py`](p1001_a_plus_b.py) | 洛谷 P1001 A+B Problem | 读完两个整数直接相加 |
| [`p1046_apple_picking.py`](p1046_apple_picking.py) | 洛谷 P1046 陶陶摘苹果 | 能碰到的高度 = 身高 + 30，统计不超过该值的苹果 |
| [`p5737_leap_year.py`](p5737_leap_year.py) | 洛谷 P5737 闰年展示 | 闰年判定：能被 400 整除，或能被 4 整除但不能被 100 整除 |
| [`arc017_a_prime.py`](arc017_a_prime.py) | AtCoder ARC017 A 素数判定 | 试除到 `sqrt(n)`，因数成对出现所以够用 |
| [`love_names.py`](love_names.py) | 学长改名（I_love_ 拼接） | 按顺序模拟，每次读取的是对方「当前」的名字 |

## 本地验证

```zsh
python p1001_a_plus_b.py
python p1046_apple_picking.py
python p5737_leap_year.py
python arc017_a_prime.py
python love_names.py
```

几组样例的实际运行结果：

```text
$ printf '1 2\n' | python p1001_a_plus_b.py
3

$ printf '100 200 150 140 129 134 167 198 200 111\n110\n' | python p1046_apple_picking.py
5

$ printf '1980 2000\n' | python p5737_leap_year.py
6
1980 1984 1988 1992 1996 2000

$ printf '5\nanonymous\nnatalia\nLeBron\nTanya_Romanova\nMikeMirzayanov\n6\n1 2\n3 4\n2 1\n4 3\n1 4\n3 2\n' | python love_names.py
I_love_I_love_I_love_Tanya_Romanova
```

## 关于第五题的两个坑

1. **顺序不能重排。** `u` 改名字时读取的是 `v` 此刻的名字，如果先把所有记录按某种顺序排序再统一处理，结果就会错。样例 1 里 1 号学长先后被 2 号和 4 号改写过，必须逐条按输入顺序执行。
2. **字符串会指数级变长。** 最坏情况下名字长度会以 `1 + len(v)` 的方式不断套娃，题目限制下还在可接受范围，但如果 `m` 很大、又形成长链，就应该考虑只在最后按依赖链回溯拼接，而不是每步都真的生成新字符串。
