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

在内核的视角下，用户的内存空间是以页面为单位的几个连续的虚拟地址区域。我们将每个连续的区域用 `struct vma` (Virtual Memory Area) 结构体表示，并使用链表将它们串起来。

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

此外，还有一个大小为0的区域，它跟随在所有 LOAD 段后面，这是进程的堆区 (`break`)。进程需要使用 `sbrk` 系统调用来扩展或收缩堆区。

```
    [0x0000000000406000, 0x0000000000406000), flags: ---U-WR-
```

![alt](../assets/xv6lab-userprocess/userprocess-vma.png)


## fork

## exec

## wait