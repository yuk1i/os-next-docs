# 互斥与同步 Mutual Exclusion & Synchronization

## 什么是互斥，什么是同步：

互斥 (Mutual Exclusion) 是指 **在同一时刻，只有一个线程** 可以访问共享资源。

同步 (Synchronization) 是指多个进程之间的事件 **按某种顺序执行** ，我们称之为 happens-before。

我们可以用现实的例子来描述这两件事情。

1. 考虑有一个厕所单间，有许多人需要上厕所。但是，在同一时刻，只有一个人能呆在这个厕所单间里面。

    这个问题中，“厕所” 即是共享资源。

2. 考虑一个十字路口的红绿灯：每个方向上，有机动车道的红绿灯；与之垂直的，有人行斑马线的红绿灯。我们要求，在机动车道亮绿灯前，与之垂直的斑马线一定已经亮红灯。

    这个问题中，我们定义了 `斑马线亮绿灯` happens-before `机动车道亮红灯`。

## 为什么需要互斥

!!!info "函数声明"
    我们会在之后的代码中使用一些简化的函数来表示线程创建等问题：

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
    $ gcc -O0 alipay.c && ./a.out
    money = 18446744073709551547
    ```

山寨支付宝会创建100个线程，每个线程都尝试从钱包（共享资源）中扣款，如果钱包没钱了那就不扣款（局部序）。`usleep` 用于强制触发一段时间的等待。

我们会发现，`money` 突然变成了一个很大的值，这是因为我们对 `unsigned long` 进行减法导致了溢出。我们考虑如下运行图，对所有白色方块强制排序（全局序）：

![image](../assets/xv6lab-sync/xv6lab-sync-alipay.png)

在最坏的情况下，钱包里只剩下1元时，两个线程都检查到了钱包余额为1元，所以它们俩都进行了扣款，然后就导致了溢出。

!!!info "数学视角的多线程"
    将 `money >= 1 ?` 和 `money--` 两步骤称为 A 与 B。A永远在B之前执行，我们写作 `A > B` (A happens-before B)。
    
    我们发现，多线程的运行步骤（全局序）是每个线程的运行步骤（局部序）的一个排列 (Permutation)。
    
    全局序是四个步骤 `{A1, B1, A2, B2}` 进行排列，其中满足局部序 `A1 > B1` 和 `A2 > B2` 的排列均是一个合法的全局序。
    例如，`(A1, B1, A2, B2)`, `(A2, B2, A1, B1)`, `(A1, A2, B1, B2)` 均是合法的全局序，而后者即是 bug 的根源。

    如果你感兴趣，你可以试着回答这个问题：我们可以从数学上验证一个多线程程序的正确性，即所有全局序都不会造成 bug。从计算复杂性理论 (Computational complexity theory) 的角度而言，解这个问题是 P 问题、NP 问题、还是 NP完全问题。

### 求和

考虑以下程序，我们创建了两个线程

```c
#include "thread.h"

#define N 100000000
long sum = 0;

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