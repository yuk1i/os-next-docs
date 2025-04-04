# 用户进程

## Address Space

我们首先回顾一下，在内核和 CPU 的视角下 U-mode 下的地址空间是如何进行描述的。

对于 CPU 而言，U-mode 下的所有访存，包括取指 (IF)、内存读 (LD)、内存写 (ST) 都是要通过页表进行地址翻译的。而 CPU 是通过 CSR `satp` 作为页表基地址来进行地址翻译的。

所以，内核需要为用户进程设置页表结构。在内核中，我们使用 `struct mm` 管理用户内存，每个 PCB `struct proc` 中均有一个指向 `struct mm` 的指针 `*mm`。

```c
// os/vm.h
struct mm {
    spinlock_t lock;

    pagetable_t __kva pgt;
    struct vma* vma;
};
```

每个 `struct mm` 中有一张页表 `pgt`，它就是用户进程使用的 `satp`，我们可以在 `usertrapret` 和 trampoline 中观察到这一点：

```c
// os/trap.c
void usertrapret() {
    // ...

    // tell trampoline.S the user page table to switch to.
    uint64 satp  = MAKE_SATP(KVA_TO_PA(curr_proc()->mm->pgt));      // <--
    uint64 stvec = (TRAMPOLINE + (uservec - trampoline)) & ~0x3;

    // jump to userret in trampoline.S at the top of memory, which
    // switches to the user page table, restores user registers,
    // and switches to user mode with sret.
    uint64 fn = TRAMPOLINE + (userret - trampoline);
    ((void (*)(uint64, uint64, uint64))fn)(TRAPFRAME, satp, stvec);
}

// os/trampoline.S
.globl userret
userret:
        # userret(TRAPFRAME, pagetable, stvec)
        # switch from kernel to user.
        # usertrapret() calls here.
        # a0: TRAPFRAME, in user page table.
        # a1: user page table, for satp.
        # a2: uservec

        # switch to the user page table.
        csrw satp, a1
        sfence.vma zero, zero
```

在内核的视角下， **用户的内存空间是几个连续的虚拟地址区域**。我们将每个连续的区域用 `struct vma` (Virtual Memory Area) 结构体表示，并使用链表将它们串起来。每个 `vma` 中有这一个区域的起始地址和结束地址（要求对齐到页边界），以及该区域的权限。

```c
// os/vm.h
struct vma {
    struct mm* owner;
    struct vma* next;   // linked list   
    uint64 vm_start;    // start address (user virtual address)
    uint64 vm_end;      // end address   (user virtual address)
    uint64 pte_flags;   // flags
};
```

用户 **程序** 会指定它在加载时，需要加载哪几个连续的区域（也成为段 Segment）。
以下是 `llvm-readelf-19 -a user/build/sh` 的输出，表示 `sh` 程序加载（LOAD）时会需要三个连续的区域：

```
Elf file type is EXEC (Executable file)
Entry point 0x402000
There are 4 program headers, starting at offset 64

Program Headers:
  Type           Offset   VirtAddr           PhysAddr           FileSiz  MemSiz   Flg Align
  ATTRIBUTES     0x00c3dc 0x0000000000000000 0x0000000000000000 0x000061 0x000000 R   0x1
  LOAD           0x001000 0x0000000000402000 0x0000000000402000 0x0011f4 0x0011f4 R E 0x1000
  LOAD           0x003000 0x0000000000404000 0x0000000000404000 0x0000cd 0x0000cd R   0x1000
  LOAD           0x004000 0x0000000000405000 0x0000000000405000 0x000020 0x0007d0 RW  0x1000
```

我们可以在 `os/proc.c` 中的 `exec` 函数中，使用 `mm_print` 打印 `sh` 加载完成后 **进程** 的 `struct mm` 结构以及 `pgt` 页表。

```
mm 0xfffffffd000fff88:
  pgt: 0xffffffc080b14000
  ref: 1
  vma: 0xfffffffd010bfe28
    [0x00000000fffe8000, 0x00000000ffff0000), flags: ---U-WR-
    [0x0000000000406000, 0x0000000000406000), flags: ---U-WR-
    [0x0000000000405000, 0x0000000000406000), flags: ---U-WR-
    [0x0000000000404000, 0x0000000000405000), flags: ---U--R-
    [0x0000000000402000, 0x0000000000404000), flags: ---UX-R-
=== PageTable at 0xffffffc080b14000 ===
[0], pte[0xffffffc080b14000]: 0x0000000000000000 -> 0x0000000080b22000 -------V
  [2], pte[0xffffffc080b22010]: 0x0000000000400000 -> 0x0000000080b23000 -------V
    [2], pte[0xffffffc080b23010]: 0x0000000000402000 -> 0x0000000080b21000 ---UX-RV
    [3], pte[0xffffffc080b23018]: 0x0000000000403000 -> 0x0000000080b20000 ---UX-RV
    [4], pte[0xffffffc080b23020]: 0x0000000000404000 -> 0x0000000080b1f000 ---U--RV
    [5], pte[0xffffffc080b23028]: 0x0000000000405000 -> 0x0000000080b1e000 ---U-WRV
[3], pte[0xffffffc080b14018]: 0x00000000c0000000 -> 0x0000000080b18000 -------V
  [1ff], pte[0xffffffc080b18ff8]: 0x00000000ffe00000 -> 0x0000000080b19000 -------V
    [1e8], pte[0xffffffc080b19f40]: 0x00000000fffe8000 -> 0x0000000080b1d000 ---U-WRV
    [1e9], pte[0xffffffc080b19f48]: 0x00000000fffe9000 -> 0x0000000080b1c000 ---U-WRV
    [1ea], pte[0xffffffc080b19f50]: 0x00000000fffea000 -> 0x0000000080b1b000 ---U-WRV
    [1eb], pte[0xffffffc080b19f58]: 0x00000000fffeb000 -> 0x0000000080b1a000 ---U-WRV
    [1ec], pte[0xffffffc080b19f60]: 0x00000000fffec000 -> 0x0000000080b24000 ---U-WRV
    [1ed], pte[0xffffffc080b19f68]: 0x00000000fffed000 -> 0x0000000080b25000 ---U-WRV
    [1ee], pte[0xffffffc080b19f70]: 0x00000000fffee000 -> 0x0000000080b26000 ---U-WRV
    [1ef], pte[0xffffffc080b19f78]: 0x00000000fffef000 -> 0x0000000080b27000 ---U-WRV
[ff], pte[0xffffffc080b147f8]: 0x0000003fc0000000 -> 0x0000000080b15000 -------V
  [1ff], pte[0xffffffc080b15ff8]: 0x0000003fffe00000 -> 0x0000000080b16000 -------V
    [1fe], pte[0xffffffc080b16ff0]: 0x0000003fffffe000 -> 0x0000000080b17000 DA---WRV
    [1ff], pte[0xffffffc080b16ff8]: 0x0000003ffffff000 -> 0x000000008020b000 -A--X-RV
=== END === 
```

我们可以发现，在 vma 链表中，有三个区域是和 ELF 中的 LOAD 段相同的，它们分别是 `.text`, `.rodata`, `.data/.bss` 段。
```
    [0x0000000000402000, 0x0000000000404000), flags: ---UX-R-
    [0x0000000000404000, 0x0000000000405000), flags: ---U--R-
    [0x0000000000405000, 0x0000000000406000), flags: ---U-WR-
```

另一个以 `0xfffe` 开始的地址则是进程的栈区。
```
    [0x00000000fffe8000, 0x00000000ffff0000), flags: ---U-WR-
```

此外，还有一个大小为0的区域，它跟随在所有 LOAD 段后面，这是进程的堆区 (Heap，在远古的操作系统上我们称之为 `Program Break`)。进程需要使用 `sbrk` 系统调用来扩展或收缩堆区。

```
    [0x0000000000406000, 0x0000000000406000), flags: ---U-WR-
```

### 概览图

![alt](../assets/xv6lab-userprocess/userprocess-vma.png)

## fork

fork 系统调用是操作系统中用于创建一个新进程的函数。当一个进程调用 fork 时，它会创建一个与父进程几乎完全相同的新进程（称为子进程）。子进程会复制父进程的地址空间、打开的文件描述符等信息。唯一不同的是，fork 调用返回的值：

- 父进程：fork 返回子进程的 PID（进程ID）。

- 子进程：fork 返回 0。

xv6 中的 `fork` 实现位于 `os/proc.c` 中的 `fork` 函数。以下为简化版本：

```c
int fork() {
    int ret;
    struct proc *np = allocproc();  // child process
    struct proc *p = curr_proc();   // parent process

    // Copy user memory from parent to child.
    mm_copy(p->mm, np->mm);

    // Set child's vma_brk
    np->vma_brk = mm_find_vma(np->mm, p->vma_brk->vm_start);
    np->brk     = p->brk;

    // copy saved user registers.
    *(np->trapframe) = *(p->trapframe);

    // Cause fork to return 0 in the child.
    np->trapframe->a0 = 0;
    np->parent        = p;

    // add child process to scheduler
    np->state         = RUNNABLE;
    add_task(np);

    return np->pid; // return value for the parent process
}
```

`fork` 的调用者即为父进程，其中用 `allocproc` 申请的新 PCB 即为子进程。我们通过修改 `np` 的 trapframe 来实现两者拥有不同的返回值。注意到我们并没有改 `p` 的 trapframe，这是因为 `syscall` 函数会为我们将 `fork` 函数的返回值写入 trapframe 中的 `a0`，我们只需让 `fork` 返回子进程的 PID 即可。

`mm_copy` 函数最终实现了对所有 `vma` 的复制：实际上就是在新的 `mm` 下面创建新的 `struct vma`，赋值 `vma` 中的属性，调用 `mm_mappages` 映射该 `vma`，最后复制实际的内存数据。

```c
// Used in fork.
// Copy the pagetable page and all the user pages.
// Return 0 on success, negative on error.
int mm_copy(struct mm *old, struct mm *new) {
    struct vma *vma = old->vma;

    while (vma) {
        struct vma *new_vma = mm_create_vma(new);
        new_vma->vm_start   = vma->vm_start;
        new_vma->vm_end     = vma->vm_end;
        new_vma->pte_flags  = vma->pte_flags;
        mm_mappages(new_vma);
        for (uint64 va = vma->vm_start; va < vma->vm_end; va += PGSIZE) {
            void *__kva pa_old = (void *)PA_TO_KVA(walkaddr(old, va));
            void *__kva pa_new = (void *)PA_TO_KVA(walkaddr(new, va));
            memmove(pa_new, pa_old, PGSIZE);
        }
        vma = vma->next;
    }

    return 0;
}
```

!!!warning "Trapframe 和 Trampoline"
    在概览图中我们可以发现，用户页表中包含 Trapframe 和 Trampoline，而 `vma` 链表中并不包含这两个页面。这样的设计是刻意的而非bug。

    考虑 `vma` （用户的 Virtual Memory Area） 的 **生命周期** (Lifecycle)，`exec` 系统调用会删除所有现有的用户内存映射并替换为新的，但是 PCB (即 `struct proc`) 对象是不需要销毁重建的，Trapframe 似乎也不需要重建。
    
    实际上，Trapframe 和 Trampoline 的生命周期实际上与该进程一致，而不是与任何一个 `vma` 条目一致。

    所以，我们在 `allocproc` 中映射 Trampoline、申请 Trapframe 页面、并映射 Trapframe，在 `freeproc` 释放 Trapframe 页面。

## exec

## wait

## 课堂报告

1. 请你参照 概览图，画出第一个用户进程，即 `init` 的内存结构。

2. Trampoline 和 Trapframe 的物理页面是哪里来的？在不同的进程中，它们的 Trapframe 及 Trampoline 是同一张物理页面吗？

参照上述我们打印的用户页表，注意其中最后两条映射的物理地址：

```
[ff], pte[0xffffffc080b147f8]: 0x0000003fc0000000 -> 0x0000000080b15000 -------V
  [1ff], pte[0xffffffc080b15ff8]: 0x0000003fffe00000 -> 0x0000000080b16000 -------V
    [1fe], pte[0xffffffc080b16ff0]: 0x0000003fffffe000 -> 0x0000000080b17000 DA---WRV
    [1ff], pte[0xffffffc080b16ff8]: 0x0000003ffffff000 -> 0x000000008020b000 -A--X-RV
```

参照 "Week 6 - 内核页表 Kernel Paging" 中的 "xv6 内核内存布局" 一章，找出这两个物理地址分别位于哪个物理地址区域。

参照内核的 linker script `os/kernel.ld`，以及内核页表的构建函数 `kvm.c:kvmmake` 日志，验证你的答案。

## 推荐阅读

回顾上周的课堂报告问题：Trapframe 和 Trampoline 是两个页面，这两个页面应该允许 U-mode 访问吗？

请你亲自做实验验证。

对于 Trampoline，修改 `kvm.c` 中 `kvmmake` 函数，调用 `kvmmap` 映射 trampoline 处，在权限中 OR 上 PTE_U。

对于 Trapframe，修改 `proc.c` 中 `allocproc` 中，调用 `mm_mappage_at` 函数处，在权限中 OR 上 PTE_U。：

使用 `make debug` 以及 `gdb-multiarch` 挂载调试器。使用 `b kernel_trap_entry` 和 `b *0x3ffffff000` 在内核 Trap 入口处和 `uservec` 处打断点，使用 `print $scause` 手动查看 CSR 状态。