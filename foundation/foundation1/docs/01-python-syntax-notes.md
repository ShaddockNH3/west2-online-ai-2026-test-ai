# Python 语法与编程技巧笔记

> 这是学 Foundation 1 时整理的笔记，覆盖容器、函数、面向对象、正则、推导式、类型注释和生成器。
> 每节尽量只讲「为什么这样写」，语法本身查文档就能看到，笔记里多写的是踩过的坑。

## 一、基础容器

### 1.1 List 的高频操作

列表是最常用的容器，但真正天天用到的只有几个动作：增删、切片、排序、遍历。

```python
names: list[str] = ["长门", "娜比娅"]

names.append("陆奥")            # 尾部追加一个
names.extend(["加贺", "赤城"])  # 尾部追加一批
names.insert(0, "大和")         # 指定位置插入

print(names[1:3])   # 切片，左闭右开
print(names[-1])    # 负索引，取最后一个
print(names[::-1])  # 步长为 -1，整体倒序
```

切片不会修改原列表，它返回一个新列表。

这一点很容易记混：`names[0:2] = ["X"]` 是修改原列表的赋值写法，而 `names[0:2]` 单独出现时只是「看一眼」。

排序有两种：

```python
scores = [("长门", 92), ("娜比娅", 78), ("陆奥", 88)]

print(sorted(scores, key=lambda item: item[1], reverse=True))
scores.sort(key=lambda item: item[1])  # 原地排序，返回 None
```

`sorted()` 返回新列表，`list.sort()` 原地改，并且**永远返回 `None`**。
写成 `scores = scores.sort(...)` 是新手最常见的错误之一，`scores` 会直接变成 `None`。

### 1.2 可变对象与引用

Python 的变量是「贴标签」，不是「盒子」。

```python
a = [1, 2, 3]
b = a          # 同一个列表贴了两个标签
b.append(4)
print(a)       # [1, 2, 3, 4]

c = a.copy()   # 浅拷贝，新列表
c.append(5)
print(a)       # 还是 [1, 2, 3, 4]
```

浅拷贝只复制第一层。如果列表里套着列表，用 `copy.deepcopy()` 才彻底。

这个特性带来一个经典坑：

```python
def add_item(item: str, bucket: list[str] = []) -> list[str]:
    bucket.append(item)
    return bucket

print(add_item("a"))  # ['a']
print(add_item("b"))  # ['a', 'b'] —— 默认值被复用了
```

默认参数只在函数定义时求值一次，所以那个空列表是**所有调用共享的同一个对象**。
正确写法是默认值给 `None`，函数内部再判断：

```python
def add_item(item: str, bucket: list[str] | None = None) -> list[str]:
    if bucket is None:
        bucket = []
    bucket.append(item)
    return bucket
```

### 1.3 Dict 的用法

字典是「键 → 值」的映射，键必须是可哈希对象（`str`、`int`、`tuple` 可以，`list` 不行）。

```python
profile: dict[str, str] = {"name": "长门", "class": "战列舰"}

print(profile["name"])            # 键不存在会抛 KeyError
print(profile.get("level", "?"))  # 键不存在返回默认值

profile["level"] = "99"           # 新增或覆盖
for key, value in profile.items():
    print(key, value)
```

`get()` 是最该养成的习惯。用 `profile[key]` 去取一个可能不存在的键，一旦不存在整个程序就崩了，而 `get()` 会安静地返回 `None` 或你给的默认值。

统计词频时，`setdefault()` 和「字典 + 计数器」都能写：

```python
words = ["水", "火", "水", "草", "水"]
counter: dict[str, int] = {}

for word in words:
    counter[word] = counter.get(word, 0) + 1

print(counter)  # {'水': 3, '火': 1, '草': 1}
```

字典从 Python 3.7 起**保证插入顺序**，所以遍历 `keys()` 得到的是你放进去的顺序，不用额外排序就能稳定输出。

合并两个字典有专门的运算符：

```python
base = {"hp": 100}
extra = {"attack": 35}
merged = base | extra      # 3.9+
base |= extra              # 原地合并
```

## 二、函数式的小工具

### 2.1 lambda 匿名函数

`lambda` 只能写**一个表达式**，不能有语句、不能写 `return`，它的值就是表达式的结果。

```python
add = lambda x, y: x + y
print(add(1, 2))
```

真正有价值的场景是「临时给一个函数当参数」，而不是给它起名字：

```python
students = [
    {"name": "长门", "score": 92},
    {"name": "娜比娅", "score": 78},
]

best = max(students, key=lambda student: student["score"])
print(best["name"])  # 长门
```

什么时候不该用？当表达式长到需要换行、或者需要写注释的时候。
`lambda` 的可读性上限很低，超过一行就该换成 `def`，因为函数名本身就是一段免费的注释。

### 2.2 装饰器

装饰器的前提是：**函数也是对象**，可以当参数传、可以当返回值。

```python
def shout(func):
    def wrapper(*args, **kwargs):
        print("=== 开始 ===")
        result = func(*args, **kwargs)
        print("=== 结束 ===")
        return result
    return wrapper


@shout
def greet(name: str) -> None:
    print(f"你好，{name}")
```

`@shout` 等价于 `greet = shout(greet)`。
`wrapper` 里能拿到外层传进来的 `func`，是因为闭包记住了它。

装饰器最常见的用途是「在不改原函数的前提下加一层通用逻辑」：计时、记日志、重试、检查权限。

一个实用的计时器：

```python
import time
from functools import wraps
from collections.abc import Callable
from typing import Any


def timer(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            cost = (time.perf_counter() - start) * 1000
            print(f"{func.__name__} 耗时 {cost:.2f} ms")
    return wrapper
```

`@wraps` 不是装饰性的甜点，它把原函数的 `__name__`、`__doc__` 复制到 `wrapper` 上。
不加的话，`greet.__name__` 会变成 `wrapper`，调试和日志里全都看不出是谁。

带参数的装饰器需要再套一层：

```python
def retry(times: int):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if attempt == times:
                        raise
                    print(f"第 {attempt} 次失败，重试")
        return wrapper
    return decorator
```

三层看着绕，其实是「先收参数，再收函数，最后收调用参数」，一层对应一件事。

## 三、面向对象

### 3.1 类与实例

```python
class Character:
    kind = "ship"          # 类属性，所有实例共享

    def __init__(self, name: str, hp: int = 100) -> None:
        self.name = name   # 实例属性，各管各的
        self.hp = hp

    def is_alive(self) -> bool:
        return self.hp > 0
```

`self` 就是「当前这个实例」，不是关键字，只是约定俗成的名字。

类属性适合放常量，实例属性放状态。但要注意一个坑：**类属性如果是可变对象，会被所有实例共享**。

```python
class Bad:
    skills: list[str] = []   # 错误示范

    def add(self, name: str) -> None:
        self.skills.append(name)
```

两个 `Bad` 实例会共用同一个 `skills` 列表，`a.add("x")` 之后 `b.skills` 里也有 `x`。
可变状态一律放进 `__init__` 里。

### 3.2 魔法方法

魔法方法是「用双下划线包起来的方法」，它们让对象能接入 Python 的语法本身。

| 方法 | 触发时机 |
| --- | --- |
| `__init__` | 创建实例时 |
| `__str__` | `print(obj)`、`f"{obj}"` |
| `__repr__` | 交互式环境、列表里显示对象 |
| `__len__` | `len(obj)` |
| `__eq__` | `obj1 == obj2` |
| `__hash__` | 作为字典键、放进 `set` |
| `__getitem__` | `obj[key]` |
| `__iter__` | `for x in obj` |
| `__call__` | `obj()` |
| `__enter__` / `__exit__` | `with obj:` |

几个能立刻感受到价值的：

```python
class Deck:
    def __init__(self, cards: list[str]) -> None:
        self.cards = cards

    def __len__(self) -> int:
        return len(self.cards)

    def __getitem__(self, index: int) -> str:
        return self.cards[index]

    def __iter__(self):
        return iter(self.cards)

    def __str__(self) -> str:
        return f"牌堆（{len(self)} 张）"


deck = Deck(["水枪", "火花", "藤鞭"])
print(deck)        # 牌堆（3 张）
print(deck[0])     # 水枪
print(list(deck))  # ['水枪', '火花', '藤鞭']
```

写了 `__getitem__` 之后，切片、`in` 判断、`for` 循环全都能直接用，因为它们底层都会去调这个方法。

`__str__` 和 `__repr__` 的区别值得单独记：`__str__` 给人看，`__repr__` 给开发者看（理想状态是能直接 `eval` 回原对象）。
只写 `__str__`，在列表里打印对象时仍然是 `<Character object at 0x...>`。

### 3.3 继承、组合与多态

```python
class Pokemon:
    def attack(self) -> str:
        raise NotImplementedError


class Pikachu(Pokemon):
    def attack(self) -> str:
        return "十万伏特"


class Squirtle(Pokemon):
    def attack(self) -> str:
        return "水枪"


for pokemon in [Pikachu(), Squirtle()]:
    print(pokemon.attack())
```

同一个 `attack()` 调用，不同对象给出不同行为，这就是多态。
它的价值在于：调用方不需要知道对方到底是什么类，只要有这个方法就能用。

`super()` 用来调用父类实现，避免把公共逻辑复制一遍：

```python
class FirePokemon(Pokemon):
    def __init__(self, name: str, hp: int) -> None:
        super().__init__()
        self.name = name
        self.hp = hp
        self.fire_stack = 0
```

继承不是越多越好。判断标准很简单：**子类能不能替换父类而不改变程序正确性**（里氏替换）。
如果只是想复用几行代码、类之间并没有「是什么」的关系，用组合更合适：

```python
class Trainer:
    def __init__(self) -> None:
        self.team: list[Pokemon] = []   # 组合：Trainer 有一个队伍，而不是「是一个队伍」
```

面向对象的三个关键词，我的理解是：

- 封装：把数据和操作数据的方法放进同一个类，外部只关心接口，不关心内部怎么算的；
- 继承：把共性提到父类，减少重复；
- 多态：同一接口，不同实现，调用方不用写一堆 `if isinstance(...)`。

## 四、正则表达式

### 4.1 常用元字符

| 写法 | 含义 |
| --- | --- |
| `.` | 任意字符（默认不含换行） |
| `\d` / `\w` / `\s` | 数字 / 字母数字下划线 / 空白 |
| `*` `+` `?` | 0 次以上 / 1 次以上 / 0 或 1 次 |
| `{m,n}` | m 到 n 次 |
| `^` `$` | 字符串开头 / 结尾 |
| `[]` | 字符集合 |
| `\|` | 或 |
| `()` | 分组，同时可以取出来 |
| `(?P<name>...)` | 命名分组 |

### 4.2 四个常用函数

```python
import re

text = "2026-11-03 12:30:45 ERROR 连接超时"

print(re.search(r"\d{4}-\d{2}-\d{2}", text).group())   # 2026-11-03
print(re.findall(r"\d+", text))                        # 年、月、日、时间都会被拆出来
print(re.sub(r"\d", "*", text))                        # 数字全部替换
print(re.split(r"\s+", text))                          # 按空白切分
```

`match()` 只从开头匹配，`search()` 只要找到就返回，`fullmatch()` 要求整串匹配。
验证格式时用 `fullmatch()` 最省心，因为它不会出现「前半段匹配就算通过」的情况。

### 4.3 分组与命名分组

```python
pattern = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<level>[A-Z]+)\s+(?P<message>.+)"
)
match = pattern.search("2026-11-03 ERROR 连接超时")

if match:
    print(match.group("date"))     # 2026-11-03
    print(match.group("level"))    # ERROR
    print(match.group("message"))  # 连接超时
```

命名分组比 `group(1)`、`group(2)` 好维护，读代码时不用回头数括号。

几个必须记住的细节：

1. **正则字符串一定加 `r` 前缀。** `"\d"` 在普通字符串里会被当成转义字符处理，`r"\d"` 才是「反斜杠 + d」。
2. **贪婪匹配会吃掉太多。** `.*` 默认尽可能长，加个问号 `.*?` 变成非贪婪。
3. **`re.compile()` 值得缓存。** 同一个正则要在循环里用上千次时，预编译能省下重复解析的开销。
4. **用户输入里可能有正则元字符。** 要当普通字符串匹配时用 `re.escape()`。

### 4.4 一个实际例子：校验密码

要求：长度 6 到 18，只能是英文字母和数字。

```python
PASSWORD_PATTERN = re.compile(r"[A-Za-z0-9]{6,18}")

print(bool(PASSWORD_PATTERN.fullmatch("abc123")))    # True
print(bool(PASSWORD_PATTERN.fullmatch("abc12")))     # False，太短
print(bool(PASSWORD_PATTERN.fullmatch("abc 123")))   # False，有空格
```

必须用 `fullmatch`。用 `search` 的话，`"abc 123"` 会因为能匹配到 `abc` 而被判为通过。

## 五、推导式与类型注释

### 5.1 推导式

一行写完「遍历 + 筛选 + 变换」：

```python
numbers = [1, 2, 3, 4, 5, 6]

squares = [n * n for n in numbers]
evens = [n for n in numbers if n % 2 == 0]
pairs = {n: n * n for n in numbers}
unique = {n % 3 for n in numbers}
```

矩阵转置是经典例子：

```python
matrix = [[1] * 10 for _ in range(5)]                 # 5 行 10 列，全是 1
transposed = [[row[i] for row in matrix] for i in range(10)]  # 10 行 5 列
```

注意上面生成矩阵用的是 `[[1] * 10 for _ in range(5)]`，而不是 `[[1] * 10] * 5`。
后者 5 行指向同一个列表，改一行会「连锁」改掉所有行——本质还是可变对象的引用问题。

推导式的可读性有上限。嵌套两层以上、或者带多个条件时，老老实实写 `for` 循环更清楚。
代码是给人读的，短不是唯一目标。

### 5.2 类型注释

```python
def total(values: list[int], scale: float = 1.0) -> float:
    return sum(values) * scale
```

常用写法：

```python
from typing import Literal, TypedDict


def find(name: str) -> str | None: ...          # 可能没有结果
def parse(payload: dict[str, object]) -> None: ...

Role = Literal["admin", "user"]                 # 只能是这两个值之一


class Student(TypedDict):
    name: str
    score: int
```

关键认知：**类型注释在运行时不做任何检查**。

```python
def greet(name: str) -> str:
    return "hi " + name

print(greet(123))   # 运行时直接报 TypeError，不会因为注释写了 str 就拦住
```

它服务的是编辑器和静态检查工具（Pylance、pyright、mypy）。
写注释的收益出现在「调用别人函数」和「改自己三个月前的代码」这两个时刻。

循环引用时用 `from __future__ import annotations`，把注释延迟成字符串，避免真去导入类型：

```python
from __future__ import annotations

class Pokemon:
    def battle(self, other: Pokemon) -> None: ...   # 这里不用写 "Pokemon"
```

## 六、生成器

### 6.1 yield 做了什么

普通函数 `return` 一次就结束；带 `yield` 的函数每次 `yield` 暂停一次，下次从暂停处继续。

```python
def countdown(start: int):
    print("开始")
    while start > 0:
        yield start
        start -= 1
    print("结束")


for value in countdown(3):
    print(value)
```

输出顺序是「开始 → 3 → 2 → 1 → 结束」，而不是先把所有值算完再一个个给。
函数体在第一次取值时才开始执行，这叫惰性求值。

### 6.2 为什么值得用

**省内存。** 处理一百万行日志时，列表推导式会把一百万个字符串全部放进内存，生成器只保留当前这一行。

```python
def read_lines(path: str):
    with open(path, encoding="utf-8") as handle:
        for line in handle:      # 文件对象本身就是迭代器，逐行读
            yield line.rstrip("\n")
```

**能表达无限序列。**

```python
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b
```

**能拼成管道。**

```python
lines = ["2026-11-03 ERROR 超时", "2026-11-03 INFO 启动", "2026-11-03 ERROR 断线"]

errors = (line for line in lines if "ERROR" in line)
messages = (line.split(" ", 2)[2] for line in errors)
print(list(messages))   # ['超时', '断线']
```

每一段都只是「说明怎么算」，真正的计算要等到 `list()` 那一刻才开始。
这正是生成器表达式和列表推导式的区别：一个用 `()`，一个用 `[]`，前者不建列表。

### 6.3 几个容易踩的点

1. **生成器只能遍历一次。** 走完就空了，再 `for` 一遍什么也拿不到。需要重复使用就把它 `list()` 出来。
2. **`return` 的值拿不到。** 生成器里 `return x` 会触发 `StopIteration(x)`，正常 `for` 循环里看不到这个值。
3. **调试时看不到内容。** 打印生成器只会得到 `<generator object ...>`，要看到值就 `next()` 或转成列表。
4. **`yield from` 用来委托。** 把一个生成器的产出直接转交给另一个：

```python
def chain(*iterables):
    for iterable in iterables:
        yield from iterable
```

## 七、把这几样串起来

一个把上面大部分知识用上的小例子：读日志 → 正则筛选 → 生成器管道 → 统计。

```python
import re
from collections.abc import Iterator
from dataclasses import dataclass

LOG_PATTERN = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<level>INFO|WARN|ERROR)\s+(?P<msg>.+)"
)


@dataclass
class LogEntry:
    date: str
    level: str
    message: str

    def __str__(self) -> str:
        return f"[{self.level}] {self.date} {self.message}"


def parse(lines: list[str]) -> Iterator[LogEntry]:
    for line in lines:
        match = LOG_PATTERN.fullmatch(line.strip())
        if match:
            yield LogEntry(**match.groupdict())


def only(entries: Iterator[LogEntry], level: str) -> Iterator[LogEntry]:
    return (entry for entry in entries if entry.level == level)


raw = ["2026-11-03 ERROR 连接超时", "2026-11-03 INFO 启动完成", "非法日志行"]
errors = only(parse(raw), "ERROR")

for entry in errors:
    print(entry)
```

`parse()` 是生成器，`only()` 返回生成器表达式，两者都是「要一个给一个」。
如果日志有几十万行，这种写法占用的内存恒定在一个对象左右，而列表版本会随行数线性增长。

## 八、小结

这几块知识单独看都不难，难的是知道什么时候用哪一个：

- 数据要反复遍历、要索引 → `list`；按键查找 → `dict`；
- 只在一处用一次的小函数 → `lambda`；需要复用或带逻辑 → `def`；
- 想给现有函数加通用行为 → 装饰器，别去改函数本身；
- 对象需要参与 `len`、`for`、`==`、`with` 这些语法 → 实现对应魔法方法；
- 文本格式固定、需要抽取字段 → 正则 + 命名分组；
- 数据量大、只遍历一次 → 生成器；数据小要反复用 → 列表。
