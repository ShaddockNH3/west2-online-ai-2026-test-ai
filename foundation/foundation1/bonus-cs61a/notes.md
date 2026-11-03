# CS61A 全量笔记

> 覆盖 hw01-10、lab00-12、hog 项目里出现的每一个主题。
> 每节先讲概念，再摘录本仓库解答里的关键代码，最后列易错点。
> 配合 [`setup-guide.md`](setup-guide.md) 食用。

## 目录

1. [函数、控制与调试](#一函数控制与调试)
2. [高阶函数与 lambda](#二高阶函数与-lambda)
3. [递归与树递归](#三递归与树递归)
4. [数据抽象](#四数据抽象)
5. [树](#五树)
6. [可变数据与链表](#六可变数据与链表)
7. [迭代器与生成器](#七迭代器与生成器)
8. [面向对象与继承](#八面向对象与继承)
9. [Scheme 基础](#九scheme-基础)
10. [Scheme 高阶函数与宏](#十scheme-高阶函数与宏)
11. [解释器是怎么工作的](#十一解释器是怎么工作的)
12. [SQL](#十二sql)
13. [Hog 项目复盘](#十三hog-项目复盘)

## 一、函数、控制与调试

涉及：hw01、lab01、lab03。

这一阶段的主题是「把问题翻译成控制流」。

**hw01 的 `a_plus_abs_b`** 要求不调用 `abs`，做法是选择运算符而不是分支返回：

```python
if b < 0:
    f = sub
else:
    f = add
return f(a, b)
```

要点是：分支里选的是**函数**，最后只有一条 `return f(a, b)`。
这也是后来所有高阶函数写法的雏形——把「变化的动作」提成值。

**lab01 的 `double_eights`** 是状态机式循环：记住上一位数字，遇到连续两个 8 就返回。
写的时候最容易犯的错是把「上一个数字」和「当前数字」的更新顺序写反。

**lab03 的 `make_onion`** 是「能否用不超过 limit 次 f、g 把 x 变成 y」，
二叉搜索式的递归：

```python
if limit < 0:
    return False
elif x == y:
    return True
else:
    return can_reach(f(x), y, limit - 1) or can_reach(g(x), y, limit - 1)
```

`or` 的短路特性让搜索树被剪枝：左边能到达就不会再算右边。

**易错点：**

1. `largest_factor` 从 `n - 1` 往下找，素数会一路找到 1，终止条件必须写对；
2. doctest 里 `>>> a = hailstone(10)` 这种语句要求函数有返回值，
   忘写 `return` 时 doctest 不会报错但下一行 `>>> a` 会输出 `None`；
3. 循环变量在 `while` 体内忘了推进是最常见的死循环来源，
   ok 的 `TimeoutException` 基本都是它。

## 二、高阶函数与 lambda

涉及：hw02、lab02。

高阶函数 = 接收函数或返回函数的函数。

**hw02 的 `accumulate`** 是求和/求积的泛化：

```python
result = start
for i in range(1, n + 1):
    result = fuse(result, term(i))
return result
```

`summation` 和 `product` 都只是它的特例：

```python
return accumulate(add, 0, n, term)
return accumulate(mul, 1, n, term)
```

这就是「先写通用的，再写特例」的抽象方向，和「先写特例再找共性」相反，
但省掉两次重复劳动。

**hw02 的 `make_repeater(f, n)`** 返回「把 f 应用 n 次」的函数：

```python
def repeat(x):
    for _ in range(n):
        x = f(x)
    return x
return repeat
```

注意闭包记住了 `f` 和 `n`，这是内层函数能引用外层参数的原因。

**lab02 的 `count_cond`** 把「统计满足条件的数的个数」参数化：

```python
def counter(n):
    count = 0
    for i in range(1, n + 1):
        if condition(n, i):
            count += 1
    return count
return counter
```

**lab02 的 `cycle(f1, f2, f3)`** 按 `i % 3` 选择要应用的函数，
本质是用循环下标在一组函数里轮转。

**易错点：**

1. `lambda` 只能是表达式，写不了 `return`；
2. 返回内层函数时，外层的参数被闭包捕获，是「值绑定」不是「值拷贝」，
   如果外层参数之后被重新赋值，内层看到的是新值；
3. `make_repeater(square, 0)` 应该返回 identity，循环写法天然正确，
   递归写法则要小心基准情形。

## 三、递归与树递归

涉及：hw03、lab03 的 `double_eights`。

递归函数只需要回答两个问题：**基准情形是什么？如何把规模缩小？**

**`num_eights`（hw03）** 禁止赋值与循环，纯递归：

```python
if n < 10:
    return 1 if n == 8 else 0
return (1 if n % 10 == 8 else 0) + num_eights(n // 10)
```

**`count_coins`（hw03）** 是经典的换硬币计数，递归有两种选择：

```python
def count(amount, coin):
    if amount == 0:
        return 1
    if amount < 0 or coin is None:
        return 0
    return count(amount - coin, coin) + count(amount, next_larger_coin(coin))
```

用「当前可用最小面额」作为参数来消除排列重复：
同一组硬币只按面额不增的顺序被数一次。

**`move_stack`（hw03）** 汉诺塔：

```python
other = 6 - start - end
move_stack(n - 1, start, other)
print_move(start, end)
move_stack(n - 1, other, end)
```

`6 - start - end` 巧在三个杆的编号和是常数。

**`make_anonymous_factorial`（hw03）** 是最烧脑的一题：
禁止赋值、禁止 `def`、禁止递归名字。解法是把「自己」当参数传：

```python
return (lambda f: lambda x: f(f, x))(
    lambda self, x: 1 if x == 0 else x * self(self, x - 1)
)
```

它证明了一件事：递归不需要名字，只需要一种引用「当前这个函数」的方式。

**易错点：**

1. 树递归的复杂度通常是指数级，`count_coins(200)` 能算但别再往上加数量级；
2. `interleaved_sum` 禁用 `%`，用布尔参数在奇偶之间翻转即可；
3. 递归写法的基准情形漏判 `0` 或负数是最常见错误。

## 四、数据抽象

涉及：hw04 的 mobile/planet、lab04 的 city、lab06 的 Card/Deck。

数据抽象的规则：**使用方只调构造函数和选择函数，不碰底层表示。**

lab04 的城市抽象有列表和字典两种表示，`change_abstraction(True)` 一切换，
不守规矩的代码立刻崩。这也是为什么 hw04 的 `balanced` 会被
`construct_check` 禁止使用 `Index`（下标访问）：

```python
left_arm, right_arm = left(m), right(m)
left_torque = length(left_arm) * total_mass(end(left_arm))
right_torque = length(right_arm) * total_mass(end(right_arm))
return (
    left_torque == right_torque
    and balanced(end(left_arm))
    and balanced(end(right_arm))
)
```

**易错点：**

1. 判断「是否走数据抽象」的标准很简单：换掉底层表示后代码是否还能跑；
2. 递归遍历复合数据时，先判断基准情形（`is_planet` / `is_mobile`），再递归；
3. `deep_map`（hw04）要求原地修改，且不能新建列表，所以要按下标赋值而不是拼接。

## 五、树

涉及：hw04 的 `max_path_sum`、lab05 的 `sprout_leaves`、lab08 的三个函数。

树递归的模板：

```python
def traverse(t):
    if 是叶子:
        return ...
    return combine(label(t), [traverse(b) for b in branches(t)])
```

- `max_path_sum`：根标签 + 子树最大路径和；
- `sprout_leaves`：叶子长出新叶，非叶则递归重建；
- `cumulative_mul`（lab08）：先递归处理子树，再把子树标签乘进根；
- `prune_small`（lab08）：循环删掉标签最大的分支直到剩 n 个，再递归；
- `delete`（lab08）：把被删节点的孩子上提给父节点，是最难的一个，
  关键在于**先递归删子树，再判断当前孩子是否要删**，顺序反了会漏。

**易错点：**

1. 树的默认参数 `branches=[]` 是共享可变默认值的坑（见基础笔记 1.2 节）；
2. `delete` 里 `new_branches += b.branches` 上提的是「删除之后」的孩子，
   所以递归必须放在判断之前；
3. lab08 的树是类实现（`t.branches`），lab05 是列表实现（`branches(t)`），
   两套接口不要混。

## 六、可变数据与链表

涉及：lab05 的 `insert_items`、`partial_reverse`，lab07 的 `duplicate_link`。

原地修改列表最大的坑是**边遍历边插入**。`insert_items` 的解法：

```python
i = 0
while i < len(s):
    if s[i] == before:
        s.insert(i + 1, after)
        i += 1  # 跳过刚插入的元素，防止 after == before 时死循环
    i += 1
return s
```

链表的同类问题 `duplicate_link`（lab07）：

```python
if s.first == val:
    s.rest = Link(val, s.rest)
    duplicate_link(s.rest.rest, val)   # 从新插入节点的下一个继续
else:
    duplicate_link(s.rest, val)
```

跳两个节点，是为了让「新插入的副本」也被检查到（连续相同值各补一个）。

**易错点：**

1. `insert_items` 里如果 `after == before` 且不跳过新元素，会无限插入；
2. `partial_reverse` 用双指针交换，`start < end` 是终止条件；
3. `Link` 的 `rest` 必须是 `Link` 或 `Link.empty`，直接塞列表会在 `__repr__` 崩掉。

## 七、迭代器与生成器

涉及：hw05、lab05 的 `count_occurrences`、`repeated`。

迭代器是「按需生产值」的对象，`next()` 取下一个，取完抛 `StopIteration`；
生成器是带 `yield` 的函数，天然是迭代器。

**hw05 的 `merge`** 归并两个无限递增序列：

```python
x, y = next(a), next(b)
while True:
    if x < y:
        yield x
        x = next(a)
    elif y < x:
        yield y
        y = next(b)
    else:
        yield x          # 相同只输出一次
        x, y = next(a), next(b)
```

**hw05 的 `hailstone`** 要求序列结束后无限 yield 1：

```python
while n != 1:
    yield n
    ...
while True:
    yield 1
```

**hw05 的 `yield_paths`** 是「生成器 + 树递归」的组合：

```python
if label(t) == value:
    yield [label(t)]
for b in branches(t):
    for path in yield_paths(b, value):
        yield [label(t)] + path
```

惰性的地方在于：`next()` 取一条路径时只计算到那条路径为止。

**lab05 的 `repeated`** 要求「尽可能少地调用 next」，
所以必须逐个读、计数连续相同值，而不是把迭代器转成列表。

**易错点：**

1. 生成器只能消费一次，`repeated(u, 3)` 被调用两次是**接续**上次的进度，
   doctest 里 `>>> repeated(u, 3)` 出现两次正是考这一点；
2. `count_occurrences(t, n, x)` 只准读前 n 个，多读一个后面的 `list(u)` 就会缺元素；
3. 生成器函数被调用时**什么都不执行**，第一次 `next` 才开始跑。

## 八、面向对象与继承

涉及：lab06 的 `classes.py`、lab07 的 `Account` / `FreeChecking`。

**lab06 的 Magic: the Lambda-ing** 一套类覆盖了 OOP 的全部基础：

- `Card.power` 是「本卡攻击力 − 对手防御力」；
- 各种子类只覆盖 `effect`（和必要时 `power`）；
- `TutorCard` 通过把 power 压成 `-inf` 实现「出这张牌必输一轮」的代价；
- `TACard` 弃掉手里 power 最高的牌并吸收它的攻防：

```python
best_card = max(player.hand, key=lambda card: card.power(opponent_card))
player.hand.remove(best_card)
self.attack += best_card.attack
```

- `InstructorCard` 每轮攻防各减 1000，只要还有一项非负就回到手牌；
- `Deck.draw` 用 `random.randrange` 随机抽牌；
- `Game.play_round` 先触发双方 effect，再比较 power 计分。

**lab07 的 `FreeChecking`** 演示继承 + 类属性：

```python
def withdraw(self, amount):
    self.free_withdrawals -= 1      # 失败的取款也消耗次数
    if self.free_withdrawals >= 0:
        fee = 0
    else:
        fee = self.withdraw_fee
    if amount + fee > self.balance:
        return "Insufficient funds"
    ...
```

`self.free_withdrawals -= 1` 第一次执行时会把类属性复制成实例属性，
所以每个账户独立计数——这正是 lab06 `change_abstraction` 之外另一处
「类属性 vs 实例属性」的实战。

**lab07 的 `time_to_retire`** 用局部变量复利模拟，不碰 `self.balance`，
因为 doctest 明确要求调用后余额不变。

**易错点：**

1. 覆盖 `power` 时注意它接收的是**对手卡**，返回值语义是「本卡战力」；
2. `effect` 里修改 `self.attack` 后，`copy()` 返回的是新对象，
   二者不会共享状态；
3. 类属性 `free_withdrawals` 若写成可变对象（如列表）就是灾难。

## 九、Scheme 基础

涉及：lab09、hw07、hw08。

Scheme 的四个基本件：`define`、`lambda`、`cond`、`let`。

**hw07 的 `pow`** 用平方降幂，复杂度 O(log n)：

```scheme
(define (pow base exp)
  (cond ((= exp 0) 1)
        ((even? exp) (square (pow base (/ exp 2))))
        (else (* base (pow base (- exp 1))))))
```

**hw07 的 `repeatedly-cube`** 练 `let` 的绑定顺序：

```scheme
(let ((y (repeatedly-cube (- n 1) x)))
  (* y y y))
```

`let` 先求值所有绑定再进入 body，等价于「先算 y，再用三次」。

**lab09 的 `composed` 与 `repeat`**：

```scheme
(define (composed f g) (lambda (x) (f (g x))))
(define (repeat f n)
  (if (= n 0)
      (lambda (x) x)
      (composed f (repeat f (- n 1)))))
```

`repeat` 用 `composed` 组装，`n = 0` 时返回 identity。

**hw08 的 `interleave`** 交替取两个表的元素，注意任一为空就返回另一个。

**hw08 的 `no-repeats`** 用自己写的 `my-filter` 去重：

```scheme
(cons (car s)
      (no-repeats (my-filter (lambda (x) (not (= x (car s)))) (cdr s))))
```

**易错点：**

1. Scheme 传给 `define` 的函数体里写递归调用没问题（名字已绑定）；
2. `cond` 的每个分支是 `(条件 结果)`，别漏 `else`；
3. `quote` 的简写 `'()` 是空表，`(list 1 2 3)` 会**求值**每个元素，
   `'(1 2 3)` 不会——hw10 里 `'(1 x 3)` 与 `` `(1 ,x 3) `` 的区别就在这。

## 十、Scheme 高阶函数与宏

涉及：hw09、lab11。

**hw09 的 `curry-cook`** 把多参数 lambda 变成柯里化形式：

```scheme
(define (curry-cook formals body)
  (if (null? formals)
      body
      (list 'lambda (list (car formals))
            (curry-cook (cdr formals) body))))
```

它构造的是**代码**（列表），要用 `eval` 才能变成可调用过程。
`curry-consume` 则反过来逐个喂参数。

**hw09 的 `switch` 宏**把自定义语法编译成 `cond`：

```scheme
(define (switch-to-cond switch-expr)
  (cons 'cond
        (map (lambda (option)
               (cons (list 'equal? (car (cdr switch-expr)) (car option))
                     (cdr option)))
             (car (cdr (cdr switch-expr))))))
```

宏在**编译期**操作代码，所以判断条件用 `equal?` 而不是先求值。
一开始用 `=` 导致符号比较报错，是这题唯一的坑。

**lab11 的 `if-program`** 把 if 变成数据：

```scheme
(define (if-program condition if-true if-false)
  (list 'if condition if-true if-false))
```

**lab11 的 `pow-expr`** 生成幂运算的展开式，奇数拆一颗、偶数套 square：

```scheme
(cond ((= exp 0) 1)
      ((even? exp) (list 'square (pow-expr base (/ exp 2))))
      (else (list '* base (pow-expr base (- exp 1)))))
```

关键理解：内层 `(pow-expr base (/ exp 2))` 是**函数调用**，
它在构造表达式时就被求值成完整展开式，所以 `(eval (pow-expr 2 16))`
看到的是纯粹的 `(square (square ...))`，可以直接算。
写成 `(list 'pow-expr ...)` 会把调用本身留在表达式里，eval 就会崩。

**lab11 的 `repeat` 宏**把表达式包成零参 lambda 延迟执行：

```scheme
(define-macro (repeat n expr)
  `(repeated-call ,n (lambda () ,expr)))
```

反引号 + 逗号：反引号内不求值，逗号处求值——这就是准引用。

## 十一、解释器是怎么工作的

涉及：lab10 的 calc 解释器。

lab10 用 Pair 链表实现了一个迷你算术语言，流程是：

1. **读**：表达式是 `Pair(operator, Pair(operand1, Pair(operand2, nil)))`；
2. **eval**：字符串查 `OPERATORS` 或绑定表，数字原样返回，Pair 递归；
3. **apply**：`calc_apply(op, args)` 调用求值后的运算符。

核心三行：

```python
operator = exp.first
operands = exp.rest
return calc_apply(calc_eval(operator), operands.map(calc_eval))
```

`operands.map(calc_eval)` 是关键：操作数在应用前要**全部求值**，
嵌套的 `Pair("+", ...)` 会先被算成数字。

`eval_and` 实现短路语义：遇到 `False` 立即返回，
否则继续求值，最后一个表达式的值就是整个 and 的值（Scheme 里 0 也是真值）。

`eval_define` 把名字写进 `bindings`，之后 `calc_eval("a")` 走到
字符串分支查表——这也解释了为什么字符串分支必须放在 `OPERATORS` 判断之后。

**易错点：**

1. 变量名和运算符都是字符串，判断顺序错会查错表；
2. `nil` 在 `map` 里有自己的实现（返回自身），空参数列表不用特判；
3. `calc_apply` 拿到的 args 必须是**已求值**的 Pair。

## 十二、SQL

涉及：hw10、lab12。

SQL 声明式：描述「要什么」，不描述「怎么算」。

**hw10 的四个查询：**

```sql
-- 孩子按父母身高降序
CREATE TABLE by_parent_height AS
  SELECT child FROM parents, dogs WHERE name = parent
  ORDER BY height DESC;

-- 狗的体型档位：min < height <= max
CREATE TABLE size_of_dogs AS
  SELECT dogs.name, sizes.size
    FROM dogs, sizes
   WHERE dogs.height > sizes.min AND dogs.height <= sizes.max;

-- 同体型兄弟姐妹造句
CREATE TABLE sentences AS
  SELECT "The two siblings, " || first || " and " || second
         || ", have the same size: " || s1.size
    FROM siblings, size_of_dogs AS s1, size_of_dogs AS s2
   WHERE s1.name = first AND s2.name = second AND s1.size = s2.size;

-- 低方差毛型：所有身高都落在均值的 ±30% 内
CREATE TABLE low_variance AS
  SELECT fur, MAX(height) - MIN(height)
    FROM dogs GROUP BY fur
  HAVING MIN(height) > 0.7 * AVG(height) AND MAX(height) < 1.3 * AVG(height);
```

**lab12 的四个查询** 对应四类套路：

```sql
-- big：GROUP BY + HAVING 做组级过滤
CREATE TABLE big AS
  SELECT course FROM finals, sizes WHERE hall = room
  GROUP BY course HAVING SUM(seats) >= 1000;

-- remaining：SUM - MAX 即「去掉最大的那个考场」
CREATE TABLE remaining AS
  SELECT course, SUM(seats) - MAX(seats) AS remaining
    FROM finals, sizes WHERE hall = room GROUP BY course;

-- sharing：自连接找同考场不同课程
CREATE TABLE sharing AS
  SELECT a.course, COUNT(DISTINCT a.hall) AS shared
    FROM finals AS a, finals AS b
   WHERE a.hall = b.hall AND a.course != b.course
   GROUP BY a.course;

-- pairs：自连接 + 字符串拼接 + 排序
CREATE TABLE pairs AS
  SELECT a.room || " and " || b.room
         || " together have " || (a.seats + b.seats) || " seats" AS rooms
    FROM sizes AS a, sizes AS b
   WHERE a.room < b.room AND a.seats + b.seats >= 1000
   ORDER BY a.seats + b.seats DESC;
```

**易错点：**

1. `WHERE` 过滤行，`HAVING` 过滤组，混用是逻辑错误不是语法错误；
2. 自连接必须给表起别名 `a`、`b`，并用 `a.room < b.room` 去掉对称重复；
3. 拼接数字要加括号：`|| (a.seats + b.seats) ||`，否则 `||` 优先级会把表达式拆散；
4. 区间用「左开右闭」防止边界身高（28、35、45）同时落进两档。

## 十三、Hog 项目复盘

Hog 是第一个完整项目，12 个问题串起前三周的全部概念。

**规则：** 掷 n 个骰子得分为其和；出现 1 则只得 1（Sow Sad）；
掷 0 个骰子得 `max(3 * |对手分数十位 − 我方分数个位|, 1)`（Boar Brawl）；
新分数恰好有 3 或 4 个因子则升到下一个素数（Sus Fuss）。

**Phase 1（模拟器）：**

- `roll_dice`：循环掷骰，用一个布尔标记 Sow Sad；
- `boar_brawl`：纯位运算取数位，禁用 `str` 与 `[]`；
- `take_turn`：组合前两者，不重复实现；
- `num_factors` / `sus_points` / `sus_update`：因子计数 + 找下一个素数；
- `play`：`while score0 < goal and score1 < goal` 交替调用
  `strategy` 与 `update`，注意 `who` 在每次行动后翻转。

**Phase 2（策略）：**

- `always_roll(n)`：闭包返回常量策略；
- `is_always_roll`：遍历所有输入组合验证策略是否恒定；
- `make_averaged`：`*args` 打包参数，重复采样取平均；
- `max_scoring_num_rolls`：对 1-10 个骰子逐一采样比较；
- `boar_strategy` / `sus_strategy`：算出「掷 0 骰」的收益，达到阈值就不掷；
- `final_strategy`：落后多滚、领先少滚、临近终点控方差。

**经验：**

1. `make_test_dice(4, 2, 5, 1)` 让随机过程变成确定性的，是所有测试的基础；
2. `play` 里策略函数每回合只能调一次——有副作用的策略会破坏 UI；
3. 统计胜率用 `make_averaged(winner)`，采样 1000 局大约几十秒，
   调参时先降到几十局。

## 十四、成绩说明

| 部分 | ok 本地得分 | 备注 |
| --- | --- | --- |
| hw01 | 6/6 | |
| hw02 | 5/5 | |
| hw03 | 4/4（默认测试） | move_stack 与匿名阶乘由 doctest 验证 |
| hw04 | 4/4 | |
| hw05 | 3/3 | |
| hw06 | 1/2 | `midsem_survey` 需要期中问卷现场口令，无法离线得出 |
| hw07 | 3/3 | Scheme |
| hw08 | 1/3 + 手工验证 | 其余为锁定测试，输出已用解释器逐条核对 |
| hw09 | 3/3 | |
| hw10 | 4/4 | SQL |
| lab00-12 | 全部通过 | lab11 的 pow 曾因表达式未展开而失败，见第十节 |
| hog | 7.3/24（锁定部分未解锁） | 全部 doctest 通过，整局模拟正常 |

锁定测试是 ok 的「先答题再解锁」机制，需要人工逐条预测输出，
本仓库未逐条解锁，但对应代码都通过了文件内 doctest 与手工核对。
