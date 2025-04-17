# 互斥与同步 Mutual Exclusion & Synchronization

## 多处理器编程

> Multiple Processes Programming 多处理器编程，从入门到放弃。

我们常说：进程有独立的地址空间，而线程是共享地址空间。这引入了 **共享内存** 的概念：即一个进程内的多个线程，会共享一部分内存空间。

这就会引入一个问题：当一个线程在读写一个内存地址时，另一个线程也在读写同一个内存地址，那这时候会发生什么？

## 互斥 Mutual Exclusion

!!!info "函数声明"
    我们会在之后的代码中使用一些简化的函数来表示线程创建等步骤：

    - `create(func)`: 创建一个线程，它从给定的函数 `func` 起开始运行。

    - `join()`: 等待所有线程退出。

    - `usleep()`: 等待几个us。

在理解我们为什么需要互斥前，我们先要明白 Data Race (数据竞争) 是怎么回事。

### 山寨支付宝

!!!info "code"

    ```c
    #include "thread.h"

    unsigned long money = 30;

    void deduct() {
        if (money >= 1) {
            usleep(1);
            money -= 1;
        }
    }

    void main() {
        for (int i = 0; i < 100; i++) create(deduct);
        join();
        printf("money = %lu\n", money);
    }
    ```

    使用 `gcc -O2 alipay.c && ./a.out` 编译并运行，体验一把亿万富翁。

    ```
    $ gcc -O2 alipay.c && ./a.out
    money = 18446744073709551547
    ```

山寨支付宝会创建100个线程，每个线程都检查钱包中是否有钱，如果有那就扣款（局部序）。`usleep` 用于强制触发一段时间的等待。

在这个问题中，钱包 `money` 即是共享资源。我们会发现，`money` 突然变成了一个很大的值，这是因为我们对 `unsigned long` 进行减法导致了溢出。我们考虑如下运行图，对所有白色方块强制排序（全局序）：

![image](../assets/xv6lab-sync/xv6lab-sync-alipay.png)

在最坏的情况下，钱包里只剩下1元时，两个线程都检查到了钱包余额为1元，所以它们俩都进行了扣款，然后就导致了溢出。

!!!info "数学模型下的多线程"
    将 `money >= 1 ?` 和 `money--` 两步骤称为 A 与 B。A永远在B之前执行，我们写作 `A > B` (A happens-before B)。
    
    我们发现，多线程的运行步骤（全局序）是每个线程的运行步骤（局部序）的一个排列 (Permutation)。
    
    全局序是四个步骤 `{A1, B1, A2, B2}` 进行排列，其中满足局部序 `A1 > B1` 和 `A2 > B2` 的排列均是一个合法的全局序。
    例如，`(A1, B1, A2, B2)`, `(A2, B2, A1, B1)`, `(A1, A2, B1, B2)` 均是合法的全局序，而后者即是 bug 的根源。

    如果你感兴趣，你可以试着回答这个问题：我们可以从数学上验证一个多线程程序的正确性，即枚举所有全局序，验证它们都不会造成 bug。从计算复杂性理论 (Computational complexity theory) 的角度而言，解这个问题是 P 问题、NP 问题、还是 NP完全问题。

如果我们不在 `if (money >= 0)` 后面加上 `usleep`，我们会发现程序的运行结果 **大概率** 是正确的。这是因为检查和扣款的指令序列太短了，以至于我们不太可能会造成 data race。但是，不太可能 != 绝对不会。在考虑并发问题时，我们需要的是正确性。

数学模型中，`(A1, A2, B1, B2)` 表示线程1和线程2都识别到了 `money == 1`，并且都将执行 `money--`。所以，解决这个问题的方式就是：不要让 `(A, B)` 变得可分割。我们可以从多个视角来理解：

1. 我们不再允许 `(A1, B1)`, `(A2, B2)` 交错，即我们将 `(A1, A2, B1, B2)` 这种情况排除出“合法的全局序”中。

2. 我们可以将 `(A, B)` 打包 **一个不可中断的整体**。即，在其他CPU的视角下，这两个事件是在一瞬间就发生完了的（即原子的 (Atomic)）。也就是说，其他CPU不可能看到这个整体的中间状态。

3. 注意到第二种描述，实际上就是 Critical Section。

!!!info "Takeaway Message"
    人是一种单线程生物。在多处理器编程的模型下，单线程思维不再一定正确了，共享变量有可能在任何时刻被别人更改。

### 单核处理器

如果你成功理解了上述的三个视角，在单 CPU 下，解决方案变得非常明朗：我们不允许在 `(A, B)` 中间产生 Context Switch。这即是我们所学习的第一种实现互斥的方式：关中断。这也是内核实现 "不可中断的整体" 的方式。

但是，需要注意到关中断不是万能的。**用户模式关不了中断**。（回忆：允许 Interrupt 的条件）

### 原子 Compare-And-Swap 指令

对于山寨支付宝的例子，我们可以从另一个角度理解为什么会出问题：当线程2检查完 `money`，在进行 `money--` 前，`money`的值已经被线程1改了；这时，线程2进行 `money--` 的条件就不再满足了！

我们可以对此进行进一步抽象：要修改某个变量（内存地址）的值时，该变量的值已经不是原来的值了。

幸运的是，现代 CPU 基本都具有一种特殊的指令：当修改某个地址的值时，检查该地址的值是否为给定的原来的值。这种指令被称为 Compare-And-Swap 指令。绝大多数情况，这种指令会被以 **原子的** 方式执行；即，在其他 CPU 的眼里，该指令是 **一瞬间** 就完成的。

我们可以把 `deduct` 函数改成下面这样，它显著地区分了共享变量 `money` 和它的局部副本 `local_money`。每当想修改 `money` 的值时，我们使用 `__sync_bool_compare_and_swap` 函数来修改 `&money` 这个内存地址的值，并且期望它现在的值和原来我们读到的值 (`local_money`) 一致。该函数会生成一条原子指令 `lock cmpxchg`。在 RISC-V 平台上，这会是一条 `amoswap` 指令。

```c
// bool __sync_bool_compare_and_swap (type *ptr, type oldval, type newval). 
//   -> return true if the comparison is successful and newval is written.
unsigned long money = 30;

void deduct() {
    long local_money;
    do {
        local_money = money;
        if (local_money == 0)
            break;
        usleep(1);
    } while(!__sync_bool_compare_and_swap(&money, local_money, local_money - 1));
    // will be compiled to: 
    // 124e:       f0 48 0f b1 15 f1 2d     lock cmpxchg QWORD PTR [rip+0x2df1],rdx
}
```

gcc 下所有 __sync_ 开头的内置 Atomic 函数：https://gcc.gnu.org/onlinedocs/gcc-14.2.0/gcc/_005f_005fsync-Builtins.html

### 锁原语 Lock Primitive

尽管我们可以使用 __sync 等内置 Atomic 函数来解决山寨支付宝的例子，我们仍需要一种通用的、实现互斥的办法。

回顾 Mutual Exclusion 的最基本要求：同一时刻，有且只有一个线程能够执行。我们定义一套原语：`lock`/`unlock` （也可以写作 `acquire`/`release` ）：

1. 所有期望实现 Mutual Exclusion 的线程都需要调用 `lock` 方法。在同一时刻，只能有一个线程将从 `lock` 方法中返回。

2. 当某线程成功从 `lock` 方法中返回后，在该线程调用 `unlock` 前，其他所有线程不得从 `lock` 中返回。

我们可以发现：从 `lock` 返回后，即是 Critical Section 的开始，`unlock` 即是 Critical Section 的结束。

### 锁的实现

我们可以想当然地写出以下代码，`status` 是一个共享变量，多个线程同时调用 `lock` 方法，尝试把 `status` 改为 `LOCKED`。最终，只有一个线程成功执行到 `status = LOCKED` 处，其他线程都在 `retry` 中打转。

```c
int status = UNLOCKED;

void lock() {
retry:
    if (status != UNLOCKED) {
        goto retry;
    }
    status = LOCKED;
}

void unlock() {
    status = UNLOCKED;
}
```

但是，如果我们按照上述山寨支付宝例子进行分析，我们可以很容易地发现一处 data race：当某个线程通过了 `if (status != UNLOCKED)` 检查后，另一个线程已经执行到了 `status = LOCKED` 处，这破坏了该线程上锁的条件。

所以，我们应该使用一个原子指令来替代 Compare and Set 这一步：每个线程都尝试原子地将 `status` 从 `UNLOCKED` 改为 `LOCKED`，CPU的实现保证了只有一个 CPU 能成功。对于那些没有成功的 CPU，它们会在这个 while 循环上一直等待。

```c
void lock() {
    while(!__sync_bool_compare_and_swap(&status, UNLOCKED, LOCKED));
}
```

!!!warning "如果没有原子指令"
    那我们只能使用 Peterson 算法来实现两个线程之间的互斥。

## 什么是互斥，什么是同步：

互斥 (Mutual Exclusion) 是指 **在同一时刻，只有一个线程** 能够执行。

同步 (Synchronization) 是指多个线程之间的事件 **按某种顺序执行** ，我们称之为 `happens-before`。

我们可以用现实的例子来描述这两件事情。

1. 考虑有一个厕所单间，有许多人需要上厕所。但是，在同一时刻，只有一个人能呆在这个厕所单间里面。

    这个问题中，“厕所” 即是共享资源。

2. 考虑一个十字路口的红绿灯：每个方向上，有机动车道的红绿灯；与之垂直的，有人行斑马线的红绿灯。我们要求，在机动车道亮绿灯前，与之垂直的斑马线一定已经亮红灯。

    这个问题中，我们定义了 `斑马线亮绿灯` happens-before `机动车道亮红灯`。

我们需要注意到，互斥并不一定代表着同步：例如 A、B、C 三个事件互斥，这表示它们不能同时执行；但这并不代表着它们执行的顺序一定是 ABC。




TO BE REMOVED:

### 求和

!!!info "code"
    ```c
    #include "thread.h"

    #define N 100000000
    volatile long sum = 0;

    void T_sum() { 
        for (int i = 0; i < N; i++) {
            sum++;
        }
    }

    int main() {
        create(T_sum);
        create(T_sum);
        join();
        printf("sum = %ld\n", sum);
    }
    ```

    使用 `gcc -O0 sum.c && ./a.out` 编译并运行，观察运行结果。

    `sum.c` 创建了两个线程分别执行 `T_sum`，每个线程执行 N 次的 `sum++`，我们期望最终的结果是 `sum = 2 * N`。

这个例子很好地展示了两个问题：数据竞争 Data race 和指令的原子性

