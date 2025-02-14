# 用户空间

用户空间 (Userspace) 是操作系统为用户程序提供的一个受限制的运行环境。操作系统通过 CPU 的硬件功能辅助来实现隔离，这通常包括：

- 特权级的隔离。用户空间一般使用低特权级运行，使用高特权级指令会触发异常。
- 内存空间的隔离。用户空间下可见的地址是操作系统为其设置的。

## 用户态和内核态的切换

RISC-V CPU 运行时会处于某个特权级状态。操作系统运行在 S mode，而用户模式处于 U mode。

### Kernel -> User

在 CSR `sstatus` 中，`SPP` 的描述如下：

The SPP bit indicates the privilege level at which a hart was executing before entering supervisor mode.
When a trap is taken, SPP is set to 0 if the trap originated from user mode, or 1 otherwise.
When an SRET instruction (see Section 3.3.2) is executed to return from the trap handler, the privilege level is set to user mode if the SPP bit is 0, or supervisor mode if the SPP bit is 1; SPP is then set to 0.

只要在 `sret` 执行时，`sstatus.SPP` 为 0，我们即可去到 U mode 下。（这并不要求我们一定处于 Trap Handler 中）

### User -> Kernel

若 CPU 运行在 U mode 下，CPU 通过触发 Trap 来回到 S mode，这通常包括：

- 中断。包含时钟中断、外部中断等。
- 异常通常包括：

    - Illegal Instruction
    - (Load, Store, Fetch) Page Fault
    - Environment call (**这是 RISC-V 的 syscall 方式**)

当需要进行系统调用时，用户程序可以使用 `ecall` 指令触发一次异常，而这将使内核 Trap 回到 S mode.

### 用户页表 / 内核页表

在上一节 Lab 中，我们介绍了 RISC-V 的页表模型，并且为内核设置了页表。在 PTE 中的第 4 个 bit U 表示该映射关系是否允许在用户模式下访问。

我们将 512 GiB 的地址切分为用户地址(低地址)和内核地址(高地址)，用户地址为 0x0000_00 开头，而内核地址以 0xffff_ff 开头。

每一个用户进程都有自己独立的地址空间，所以，对于每一个用户程序，我们都为它创建一个单独的页表。我们将其称为用户页表。

在 xv6 中，用户页表并不包含内核页表项目，也就是说不包含内核镜像的代码、数据和 Direct Mapping 等。

由于我们从 U mode 进入 S mode 的方式是 Trap，而在进入 Trap Handler 时，CPU 还会在使用着处于 U mode 时所用的页表，并不包含内核空间的地址映射。所以说，我们不能直接在 U mode 下使用内核所用的 `stvec`。这个问题与我们在实现 Relocation 时所遇到的问题类似。

所以，我们设置一个专门的代码页面，让它在内核页表和用户页表中都映射到相同的虚拟地址。在我们需要 S mode -> U mode 时，我们切换到用户页表，并设置用户的 `stvec` 为该代码页面中的一个简易 Trap Handler。而在进入该 Trap Handler 时，即 U mode -> S mode 时，我们切换回内核的页表和内核的 `stvec`，保存用户的执行环境，并恢复内核的运行环境。


### Trampoline

> Trampoline n. 蹦床

在 xv6 中，Trampoline 是两段特殊的代码 `uservec` 和 `userret`，用于切换到用户态和切换回内核态。

```asm
	.section trampsec
.globl trampoline
trampoline:

.globl uservec
uservec:
        # trap.c sets stvec to point here, so
        # traps from user space start here,
        # in supervisor mode, but with a
        # user page table.
        #
        # sscratch points to where the process's p->trapframe is
        # mapped into user space, at TRAPFRAME.
        #

        j usertrap

.globl userret
userret:
        # userret(TRAPFRAME, pagetable, stvec)
        # switch from kernel to user.
        # usertrapret() calls here.

        # ...

        # return to user mode and user pc.
        # usertrapret() set up sstatus and sepc.
        sret
```