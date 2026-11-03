# 锁定测试验证器 verify_ok.py

ok 的锁定测试采用「先答题再解锁」机制：每道题的期望答案用
`hmac_md5(作业名, 答案文本)` 加密存放在 `tests/*.py` 里。

本脚本反过来用它做**自动验证**：把每条锁定用例的代码在自己的实现上执行，
拿实际输出计算同样的 hmac 并与官方哈希比对——全部一致，说明实现和课程
的期望输出完全一致，效果等同于逐条解锁。

## 用法

```zsh
cd <作业目录>          # 例如 cats/、hog/、lab02/
python3 ../verify_ok.py .
```

输出形如 `===== cats: 66/66 =====`，列出所有与官方期望不一致的用例。

## 实现要点

1. **密钥**：`hash_key = assignment.name`，即 `.ok` 配置里的作业名（如 `Project 2: Cats`）；
2. **doctest 套件**：答案 = 有打印输出时只算打印内容，否则算返回值的 repr；
3. **wwpp（What Would Python Print?）套件**：每一行输出单独一个哈希，按顺序对应；
4. **课程约定的作答文本**：异常答 `Error`（`StopIteration` 例外，答 `StopIteration`），
   函数对象答 `Function`，缺失的 repr 行（返回 `None`）答 `Nothing`；
5. 上一份作业的套件带 setup/teardown，teardown（如恢复被替换的函数）必须执行，
   否则会污染后续套件（hog 的 Question 4 就靠这个才发现对齐问题）。

## 已验证结果

| 作业 | 结果 |
| --- | --- |
| cats | 66/66 |
| hog | 66/66 |
| lab00 | 4/4 |
| lab01 | 28/28 |
| lab02 | 35/35 |
| lab03 | 17/17 |
| lab04 | 8/8 |
| lab05 | 30/30 |
| lab06 | 5/5 |
| lab07 | 20/20（需临时借用 lab08.py，课程包自带的跨作业导入） |
| lab08 | 8/8 |
| ants | 80/80 |

hw01-06 与 lab10 的测试本身没有锁定用例（直接 doctest / SQL），
用 `python3 ok --local --score` 即可验证。
