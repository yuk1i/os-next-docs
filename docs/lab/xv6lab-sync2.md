## Synchronization 2

### Data Race

我们在上节课没有给数据竞争一个精准的定义，我们现在补上它：

Two (or more) memory operations **conflict** if they access the same location and at least one of them is a write operation.

如果多个内存访问访问同一个地址、并且至少一个为写，我们称这种情况为数据竞争。

!!!info "如果我们不让写，那是不是可以并发地读？"
    这就是 `rwlock` 的设计原理，我们将对共享资源（内存）的访问分为读、写两种情况。`lock` 操作分为 `rdlock` 和 `wrlock`。
    
    在同一时刻，所有读者 (reader) 可以并发地读（同时从 `rdlock` 返回），或者只能有一个写者 (writer)。单个 writer 和所有 reader 以及其他 writer 互斥。

!!!info "如果数据竞争没有副作用 (side-effect)"
    假如说，我们允许数据竞争的出现，但是保证它不引起bug，我们就可以避免使用锁了。

    RCU (Read-Copy-Update) 是一种同步机制，用于在由指针链接（如链表）的多个对象中避免使用锁。当更新指针时，所有读者被保证看到的都是旧副本或新副本，其中不会出现数据不一致的情况，例如读到一个非法指针。

    In computer science, read-copy-update (RCU) is a synchronization mechanism that avoids the use of lock primitives while multiple threads concurrently read and update elements that are linked through pointers and that belong to shared data structures (e.g., linked lists, trees, hash tables).

    Whenever a thread is inserting or deleting elements of data structures in shared memory, all readers are guaranteed to see and traverse either the older or the new structure, therefore avoiding inconsistencies (e.g., dereferencing null pointers).

### Semaphore

信号量是一种 **带计数器的互斥锁**，最多有 N 个线程能同时持有同一个 Semaphore。

我们定义一套原语：`sem_acquire`/`sem_release`（也可以写作 `P()`/`V()` ）：

1. 在同一时刻，**最多只能有 N 个** 线程将从 `sem_acquire` 方法中返回。我们称为该线程持有 Semaphore。

2. 超过数量的线程会等待（即互斥）。

3. 当某线程调用 `sem_release` 后，持有 Semaphore 的线程总数减一。在等待的线程可以从 `sem_acquire` 中返回。

我们可以发现，互斥锁 mutex 是 Semaphore 中 N = 1 的特殊情况。

我们可以用 “有限个数的共享资源” 来理解 Semaphore。例如游泳馆的储物柜、或者停车场的车位。

在进入游泳馆时，给每个人发一个手环（持有 Semaphore）；只有持有手环的人才能进入游泳馆（互斥）；当储物柜被占满时，我们无法给新来的人发手环了，于是他们只能等待（等待）；离开游泳馆的人要还回手环（释放）。

我们将在最后一次作业中，在 xv6 上实现信号量，并实现哲学家吃饭问题。

### 生产者-消费者模型

Producer-Consumer 模型

### 不变量 Invariant

### POSIX 

## Lab 练习

4. 假设有两种线程，每种线程若干个：第一种线程死循环地打印左括号 `(`，第二种线程死循环地打印右括号 `)`。现在要求：打印出来的字符串是平衡的括号字符串或其前缀，如 `()(())` 和 `((()`，最多允许 N 层嵌套括号。

    例如：
    - `()((()))` 是一个合法的平衡括号。
    - `())` 不是一个合法的平衡括号。
    - `((()` 是 `((()))` 的前缀，嵌套深度为 2。

    已知有一个变量表示：目前左括号比右括号多了几个。请你写出这两种线程的同步条件。即，每种线程在什么时候可以打印 `(` 或 `)`。

    这两种线程会一直打印，你不需要考虑程序 Ctrl C 结束时产生的字符串是否为一个完整的平衡括号，这时的字符串可以是一个平衡括号的中间状态。