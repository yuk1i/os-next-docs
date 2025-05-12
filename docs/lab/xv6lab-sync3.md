## 并发 Bug

### Deadlock

上锁是一个非常精细的步骤，而最常见的问题就是死锁。死锁问题通常分为两种：AA-deadlock 和 ABBA-deadlock。

#### AA-deadlock

AA-deadlock 表示你在对一把已经获得了的锁重新上锁：

```c
acquire(&lk);
assert(holding(&lk));
// ...

    // maybe in interrupt handler or other methods
    acquire(&lk);
    // <-- deadlock here.
```

尽管我们看起来不会犯这种错误，但是真实的系统往往是很复杂的，函数的控制流可能不会那么的显然。

想象你正在写函数 `C()`，已经存在函数 `B` 和函数 `A`，而 `B` 调用 `A` 时会在 `A` 中上锁和解锁。
而 `C` 可能也需要用到同一把锁，所以你会在 `C` 中也上锁解锁。而你发现你会需要复用 `A` 的功能，于是你在持有锁的情况下调用了 `A`。

```c
void A() {
    acquire(&lk);
    // ...
    release(&lk);
}

void B() {
    // ...
    A();
    // ...
}

void C() {
    acquire(&lk);
    A();
    release(&lk);
}
```

当控制流从 `B` 进入 `A` 时是不会死锁的，而从 `C` 进入 `A` 时会死锁。

以及想象另一种情况，你 debug 找到了一个并发 bug；为了解决它，你在 `A` 中加入了上锁解锁的代码；你可能认为只有 `B` 会调用 `A`，而实际上存在 `C -> A` 这一条调用链，而这条调用链里面你在 `C` 中上了锁。

#### 防御性编程

xv6 中，我们使用防御性编程来避免这种问题：

1. 在 `acquire` 上锁时，检查当前 CPU 是否持有着这把锁。如果是，则是 AA 型死锁，使用 `panic("already acquired by")` 中断内核执行。

    ```c
    // Acquire the lock.
    // Loops (spins) until the lock is acquired.
    void acquire(spinlock_t *lk)
    {
        uint64 ra = r_ra();
        push_off(); // disable interrupts to avoid deadlock.
        if (holding(lk))
            panic("already acquired by %p, now %p", lk->where, ra);
        
        // ...
    }
    ```

2. 对于一些常用的函数，我们在入口处 `assert(holding(&lk))` 来断言进入函数时我们持有这把锁。

    ```c
    // vm.c

    pte_t *walk(struct mm *mm, uint64 va, int alloc) {
        assert(holding(&mm->lock));
    }

    int mm_mappages(struct vma *vma) {
        // ...

        assert(holding(&vma->owner->lock));
    }
    ```

#### ABBA-deadlock

ABBA 型死锁则是：线程 1 以 `A -> B` 的顺序上锁，线程2 以 `B -> A` 的顺序上锁。
在某个最坏情况下，线程1和2分别得到了A和B，但是它们又各自在等待B和A，而这两把锁恰好在别人手上。

还有一些更加复杂的情况，如：

- 线程 1 上锁顺序：`A -> B`
- 线程 2: `B -> C`
- 线程 3: `C -> A`

我们可以总结出死锁产生的 **必要条件**，将锁（可以推广为“共享资源”）视为一个球：

1. Mutual Exclusion: 拿到的完整的球，不可能出现一人一半的情况
2. Hold and Wait：持有球的情况下等待额外的球
3. No-Preemption：不能抢别人手里的球
4. Circular wait：形成循环等待的关系

（推荐阅读 https://dl.acm.org/doi/10.1145/356586.356588）

> 论文原文：
> This deadlock situation has arisen only
> because all of the following general conditions were operative:
> 1) Tasks claim exclusive control of the resources they require ("mutual exclusion" condition).
> 2) Tasks hold resources already allocated
> to them while waiting for additional resources ("wait for" condition).
> 3) Resources cannot be forcibly removed
> from the tasks holding them until the
> resources are used to completion ("no
> preemption" condition).
> 4) A circular chain of tasks exists, such
> that each task holds one or more resources that are being requested by the
> next task in the chain ("circular wait"
> condition). 

既然说这是 **必要条件**，那么我们只需要打破任何一个就可以避免死锁问题了。在大型系统中，显然最后一个是最容易打破的。

上锁顺序可以被视为一个有向边，而全局的上锁顺序则构成了一张图(dependency graph)，如果这个图上存在环，则表明有死锁问题。

如果避免环：我们可以给锁编号(Lock Ordering)，强制按照从小到大的顺序上锁。

此外，我们也可以动态检测死锁。

### Data Race

有时候，我们即使对共享资源的访问上了锁，但是没有上对，仍然会有数据竞争的并发 bug，主要是以下两种：

1. 上错了锁

```c
void T1() { acquire(&A); sum++; release(&A); }
void T2() { acquire(&B); sum++; release(&B); }
```

2. 忘记上锁

```c
void T1() { acquire(&A); sum++; release(&A); }
void T2() { sum++; }
```

即使 T1 访问 sum 时上了锁，但是它依然和 T2 有 data race。结论是，对于同一个共享变量，我们应该总是使用同一把锁来保护。

即使是 Mozilla 和 Google 的程序员也会犯这种错误。

## Futex

在之前的课程中，我们介绍并发和同步的代码均是在内核模式中介绍的。那么，在用户模式下的互斥与同步是怎么实现的？

!!!info "共享内存"
    在本小章节的介绍都是基于共享内存的模型，在 Linux 上，它们可以使用 `mmap(2)` 和 `shm(2)` 创建。

    在 xv6 上，我们的进程模型尚未支持共享内存，但是其核心思想是相同的。

!!!info "用户模式和内核的区别"
    当我们讨论并发时，用户模式（usermode）和内核模式（kernel）最显著的区别是：内核可以屏蔽中断，而用户程序不可以。

在用户模式下，我们依然可以使用原子指令来实现 `spinlock` 自旋锁。但是，对于 `sleeplock` 来说，事情会变得更加复杂。

`sleeplock` 要求在抢不到锁时睡眠进程，并在锁被释放后唤醒进程。这样的话，我们就需要系统调用来做“睡眠”和“唤醒”这两件事情，因为只有内核才能修改某个进程的状态。

```c
void sleeplock_acquire(sleeplock_t *lk) {
retry:
    if (__sync_lock_test_and_set(&lk->locked, 1) == 0) {
        // we succeed in 0-to-1 transition, aka, we get the lock.
        return;
    } else {
        // we fail to get the lock, sleep myself.
        int mypid = getpid();

        // append myself to the waiter queue.
        acquire(&lk->waiters_lock);
        append_waiter(lk, mypid);
        release(&lk->waiters_lock);

        // <-- this process may be wakeup here.

        syscall_sleep();

        // <-- then we will never be woken-up.

        goto retry;
    }
}

void sleeplock_release(sleeplock_t *lk) {

    // A.
    __sync_lock_release(&lk->locked);

    // B.
    // find the next one to wakeup.
    acquire(&lk->waiters_lock);
    int nextone = pop_waiter(lk);
    release(&lk->waiters_lock);

    // C.
    syscall_wakeup(nextone);
}
```

然后，我们就会陷入和 Sync 1 课上讲的 "The Lost Wake-Up Problem" 一样的问题，`syscall_sleep` 可能会导致唤醒信号丢失。

最简单的正确方法即是将所有加锁和解锁的操作都放置到内核处理。但是，系统调用是一种相当耗时的操作，所以我们期望将 fast-path 留在用户态。对于 `sleeplock` 而言，fast-path 就是没有人争抢锁的情况下，只需要使用一条原子指令标记当前锁被占有，而不需要非常耗时地陷入内核态。

对于 "lost wakeup" 问题，我们只需要将 slow-path “把自己睡眠” 交给内核处理，并由内核实现与 wakeup 的互斥即可。

> man 7 futex, man 2 futex

futex 是 Linux 内核提供的一个 syscall，用于实现 fast user-space mutexes，其定义如下：

```c
long syscall(SYS_futex, 
    uint32_t *uaddr, int futex_op, uint32_t val,
    const struct timespec *timeout,   /* or: uint32_t val2 */
    uint32_t *uaddr2, uint32_t val3);
```

它接受一个虚拟地址 uaddr 和用户的预期值 val，以及 futex 的操作 futex_op。
futex 会通过虚拟地址背后的物理地址来区分调用者将在哪个 futex 对象同步。
<!-- 所以，对于跨进程的 `shm` 而言，只要它们各自的虚拟地址是同一个物理地址，那它们就可以通过 futex 实现同步。 -->

最重要的两个op是：

1. `FUTEX_WAIT`：如果 `uaddr` 的值与 `val` 中一致，则陷入睡眠，它将等待一个 `FUTEX_WAKE` 操作将其唤醒。如果内核检测到 `uaddr` 的值与用户预期的 `val` 不一致（这说明用户调用 `futex` syscall 的背景发生了变化），那它会立刻从系统调用中返回 `EAGAIN`，而不陷入睡眠。（这就避免了 lost-wakeup 问题）

    内核也会使用原子指令对该虚拟地址背后的物理地址进行访问，确保原子性。

    This operation tests that the value at the futex word pointed to by the address` uaddr` still contains the expected value `val`, and if so, then sleeps waiting for a `FUTEX_WAKE` operation on the futex word.  
    
    If the thread starts to sleep, it is considered a waiter on this futex word. 
    **If the futex value does not match val, then the call fails immediately with the error EAGAIN.**

    The purpose of the comparison with the expected value is to prevent lost wake-ups.
    If another thread changed the value of the futex word after the calling thread decided to block based on the prior value, and if the other thread executed a `FUTEX_WAKE` operation after the value change and before this `FUTEX_WAIT` operation, then the calling thread will observe the value change and will not start to sleep.

2. `FUTEX_WAKE`： 唤醒在 `uaddr` 上等待的所有 waiter。

    This operation wakes at most `val` of the waiters that are waiting (e.g., inside `FUTEX_WAIT`) on the futex word at the address `uaddr`.  Most commonly, val is specified as either 1 (wake up a single waiter) or `INT_MAX` (wake up all waiters).

我们可以一探究竟 `pthread_mutex_t` 是如何实现的：

!!!info "glibc 源代码"
    pthread 的实现源代码位于 glibc 源代码中。它为了性能进行了高度优化，所以看起来会非常复杂。
    
    `pthread_mutex_t` 的基础功能是依赖于 `lll` lowlevellock 的。

    这一部分代码位于 `nptl/lowlevellock.c` 以及 `sysdeps/nptl/lowlevellock.h`。

`pthread_mutex_t` 中有一个 `uint32_t`，表示锁的状态：0 表示未上锁，1 表示上锁了但是没有 waiter，`>1` 表示上锁但是可能存在 waiter。

```c
void lll_lock(uint32_t* futex) {
    // try to make futex transit from 0 (UNLOCKED) to 1 (LOCKED).
    if (atomic_compare_and_exchange_bool_acq(futex, 1, 0)) {
        // if cmpxhg fails: 

        // try to exchange 2 into `*futex`, return the original value.
        while (atomic_exchange_acquire(futex, 2) != 0) {

            // if old value is not `UNLOCKED`
            syscall_futex(futex, FUTEX_WAIT, 2); /* Wait if *futex == 2.  */
            
            // if syscall returns, *futex is not 2 or someone wakes me up.
        }
        
        // when we get there, old *futex is 0, now 2 (LOCKED).
    }
    // succeed, LOCKED (*futex is 1 or 2)
}

void lll_unlock(uint32_t* futex) {
    // exchange 0 UNLOCKED into futex
    int __oldval = atomic_exchange_release(futex, 0);

    if (__oldval > 1) {
        // wake up one waiter
        syscall_futex(futex, FUTEX_WAKE, 1);
    }
}
```

上锁步骤：

1. 首先尝试将 futex: `0->1`，如果失败了，则说明有其他线程占用着锁。
2. 随后，死循环地尝试将 futex: `0->2`，如果成功，则表明上锁成功。
3. 否则，在 `futex` 上通过系统调用 `futex_wait` 等待。当从 syscall 中退出时，重试第 2 步。

解锁步骤：

1. 将 0 写入 futex，如果旧值大于1，则使用 `futex` syscall 唤醒一个 waiter。

你可以试着证明这个锁满足三个锁的要求：Mutual Exclusion, Bounded Waiting, Progress。注意，在用户模式下，每一步执行都是可以被中断的、可以与其他函数执行步骤交错的。

例如以下例子描述了 T1 T2 竞争锁的流程图：

```
        T1                  T2
        |                   |
  lock (0->1, ok)           |
    (acquired)              |
        |              lock (0->1, fail)
unlock(store 0, see 1)      |
        |              lock (0->2, ok)
        |                   |
    (released)          (acquired)


        T1                  T2
        |                   |
  lock (0->1, ok)           |
    (acquired)         lock (0->1, fail)
        |              lock (0->2, fail)
        |                futex_wait()
unlock(store 0, see 2)      |
    futex_wake()        (woken-up)
        |              lock (0->2, ok)
    (released)              |
                         (acquired)


        T1                  T2
        |                   |
  lock (0->1, ok)           |
    (acquired)              |
        |              lock (0->1, fail)
        |              lock (0->2, fail)
unlock(store 0, see 2)      |
        |               futex_wait()
    futex_wake()     (EAGAIN, kernel sees 0)
        |                   |
    (released)         lock (0->2, ok)
                            |
                         (acquired)
```

你可以试着补全如下的图：

```
        T1                  T2                      T3
        |                   |                       |
  lock (0->1, ok)           |                 lock (0->1, fail)
    (acquired)              |                 lock (0->2, fail)
        |                   |                    futex_wait()
        |              lock (0->1, fail)            |
        |              lock (0->2, fail)            |
        |                   |                       |
unlock(store 0, see 2)      |                       |
        |               futex_wait()                |
    futex_wake()   (EAGAIN, kernel sees 0)          |
        |                   |                   (woken-up)
    (released)         
```

## Sync 1 & 2 Lab 练习解析

TODO

## I/O

什么是 I/O 设备？ **I/O 设备就是一堆寄存器**。IO 设备通过寄存器完成与 CPU 的数据交换，然后根据寄存器中的指令完成任务。

CPU 怎么访问 I/O 设备的寄存器：I/O指令，或 Memory-Mapped Register。

!!!success "Recall 计组"
    我们可以先回顾一下，在计算机组成原理课的 Project 上，我们要使用 RISC-V 指令点亮一个 FPGA 板子上的一个灯泡。

    而 “FPGA 板子上的灯泡” 是通过 FPGA 芯片上的引脚连接到电路板上的 LED 灯。我们在 FPGA 上编程时，需要使用 `reg led[0:7]` 创建一些 Registers 并用它驱动 FPGA 芯片的引脚。

    而我们的 CPU 是怎么访问这些寄存器的？计组课可能会教两种方法：创建一种新的指令，专门用它来操作 LED 灯；将 LED 灯这些寄存器映射到 Address Space 上，通过普通的访存指令访问它们。

### 串口设备

在 QEMU 平台和 VisionFive2 上，串口所使用的设备模型是 uart8250。它的 MMIO 接口暴露了 8 个寄存器。具体的细节可见：https://www.lammertbies.nl/comm/info/serial-uart

uart8250 具有一个读口和一个写口，分别是 `RHR` 和 `THR`，它们都是8-bits的寄存器。在寄存器 `LSR` 中，各有一个 bit 表示读口有数据 (Bit 0, Data available) 和写口空闲（Bit 5, THR is empty）。

我们通过 Memory-mapped 地址访问设备的寄存器：

```c
#define Reg(reg) ((volatile unsigned char *)(KERNEL_UART0_BASE + (reg)))

static void set_reg(uint32 reg, uint32 val) {
    writeb(val, Reg(reg));
}

static uint32 read_reg(uint32 reg) {
    return readb(Reg(reg));
}
```

对于写入，我们使用轮询 Polling，只要 `LSR.THR` 提示 `THR` 空闲，我们就向 `THR` 中写入一个字符。

```c
static void uart_putchar(int ch) {
    while ((read_reg(LSR) & LSR_TX_IDLE) == 0);

    set_reg(THR, ch);
}
```

对于读取，我们使用中断，每当 I/O 设备填充完毕 `RHR` 后，它会发起一个中断，我们在中断处理函数中读取该字节。

```c
void uart_intr() {
    while (1) {
        int c = uartgetc();
        if (c == -1)
            break;
        // infof("uart: %c", c);
        consintr(c);
    }
}
```

### 块设备

我们对串口设备的访问是一个字节一个字节的，我们称这种设备为 Character Device。
与之对应的，块设备的访问是以一个块为单位的，块大小一般为 512B 或 4KiB，我们称这种设备为 Block Device。
我们所使用的硬盘，包括固态硬盘和机械硬盘，都是块设备。

在 QEMU 上，块设备一般由 VirtIO Block-Device 提供。

VirtIO 是一种在虚拟化平台上非常常用的设备模型。它也定义了一堆寄存器接口，并通过 Memory-mapped register 进行访问。

!!!info "virtio"
    VirtIO 代码位于 `fs/virtio.c`，你可以参照 VirtIO 手册了解具体的细节。

    https://docs.oasis-open.org/virtio/virtio/v1.3/csd01/virtio-v1.3-csd01.pdf

`make run` 运行内核，它包含一个基本的操作 Block Device 的代码样例。

```c
void fs_init() {
    infof("fs_init");

    struct buf* b = bread(0, 0);
    assert(b->valid);
    infof("first read done!");

    hexdump(b->data, BSIZE);

    memmove(b->data, "hello, world!", 13);
    bwrite(b);
    infof("first write done!");

    infof("fs_init ends");
}
```

首先我们通过 `bread` 读取 0 号设备（我们只有这一个块设备）的第0号块（block no），然后将其最初始的内容覆盖为 "hello world"，随后重新将这个块写入到块设备中。

## Virtual File System

在进入文件系统一章前，我们可以先试着了解：**什么是文件？**

1. 当讨论文件系统上存储的文件时，**文件是一个字节序列**。

    不管是二进制文件（如 ELF 格式的可执行文件）还是 Markdown 格式的文本文件，它们本质上都是一串字节序列，只不过我们解读 (interpret) 它们的方式不同。

    内存空间也是一个字节序列，所以，能不能将文件的一部分映射到内存空间呢？这就是 `mmap(2)` 系统调用。

2. 当讨论操作系统中内核与用户模式交互时，**文件是内核中一个可以和用户程序交互的对象**。

    当我们使用 `open(2)` 系统调用打开一个文件路径时，内核返回了一个 `int` 类型的值，它是文件描述符 file descriptor。

    我们可以使用 `read(2)`、`write(2)`、`fcntl(2)` 等系统调用对这个文件进行读写等操作，它们的原型中均带有一个 `fd` 参数。

    ```c
    ssize_t read(int fd, void buf[.count], size_t count);
    ssize_t write(int fd, const void buf[.count], size_t count);
    int fcntl(int fd, int op, ... /* arg */ );
    off_t lseek(int fd, off_t offset, int whence);
    ```

    Unix 哲学中 Everything is a file. 当然内核可以创建一个不是代表着“文件系统上的文件”的文件描述符。

    例如，我们可以创建一个 fd 来接收 signal！（就是我们project的那个signal）

    ```c
    int signalfd(int fd, const sigset_t *mask, int flags);
    // signalfd() creates a file descriptor that can be used to accept signals targeted at the caller.  
    // This provides an alternative to the use of a signal handler or sigwaitinfo(2), and has the advantage that the
    //   file descriptor may be monitored by select(2), poll(2), and epoll(7).
    ```

    以及一种特殊的对象 epoll，它可以以非常低的性能代价监控超多 file descriptor 的状态变化。

    ```c
    // epoll_create, epoll_create1 - open an epoll file descriptor. 
    //  epoll_create() returns a file descriptor referring to the new epoll instance.
    int epoll_create(int size);

    // This  system call is used to add, modify, or remove entries in the interest list of the epoll(7) instance
    //    referred to by the file descriptor epfd.  It requests that the operation op be performed for  the  target
    //    file descriptor, fd.
    int epoll_ctl(int epfd, int op, int fd, struct epoll_event *_Nullable event);

    // epoll_wait - wait for an I/O event on an epoll file descriptor
    int epoll_wait(int epfd, struct epoll_event *events, int maxevents, int timeout);
    ```

    我们的控制台对应的文件描述符 0 (stdin), 1 (stdout), 2 (stderr) 也不是存储在磁盘上的文件系统中的一个文件。
    
    在xv6启动第一个进程时，它会创建两个文件 stdin 和 stdout，分别绑定(install) 到第一个进程的 0 号 fd 和 1 号 fd。

    在第一个进程(init)通过 fork exec 创建第二个进程 `sh` 时，`sh` 从 `init` 手里继承了这两个文件，并且仍然通过 0 和 1 这两个文件描述符索引它们。


总而言之，**文件描述符是用户程序操作内核对象的一个标识符**。当内核创建一个对象后（它可能不是一个“存储在磁盘上的文件”），内核将它绑定到文件描述符表 (File Descriptor Table, fdt) 中的某个整数上，用户可以通过一些系统调用对这个文件进行操作，通过文件描述符来指定操作哪个文件。

