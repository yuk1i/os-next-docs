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

由于我们从 U mode 进入 S mode 的方式是 Trap，而在进入 Trap Handler 时，CPU 会将 pc 跳转为 `stvec`，但是此时 CPU 仍然还使用着原来的 satp，即 U mode 时所用的页表，并不包含内核空间的地址映射。所以说，我们不能直接在 U mode 下使用内核所用的 `stvec` (`0xffff_ffff_8020_xxxx`)。这个问题与我们在实现 Relocation 时所遇到的问题类似。

所以，我们设置一个专门的代码页面，让它在内核页表和用户页表中都映射到相同的虚拟地址。

在我们需要 S mode -> U mode 时，我们切换到用户页表，并设置用户的 `stvec` 为该代码页面中的一个简易 Trap Handler。而在进入该 Trap Handler 时，即 U mode -> S mode 时，我们切换回内核的页表和内核的 `stvec`，保存用户的执行环境，并恢复内核的运行环境。

我们将该特殊页面称为 Trampoline，并将其映射到 `0x0000_003f_ffff_f000`。

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
        # in supervisor mode, but with a user page table.
        #
        # sscratch points to where the process's p->trapframe is
        # mapped into user space, at TRAPFRAME.

	# swap a0 and sscratch, so that a0 is TRAPFRAME
        csrrw a0, sscratch, a0

        # save the user registers (x1 - x31) in TRAPFRAME
        sd ra, 40(a0)
        sd sp, 48(a0)
        # ...
        sd t5, 272(a0)
        sd t6, 280(a0)

        # we have saved t0, so we can smash it
        # resotre a0 from sscratch, and save it
        csrr t0, sscratch
        sd t0, 112(a0)

        # save epc
        csrr t1, sepc
        sd t1, 24(a0)

        # load kernel's satp, sp, usertrap handler, tp(hartid)
        ld t1, 0(a0)
        ld sp, 8(a0)
        ld t0, 16(a0)
        ld tp, 32(a0)

        csrw satp, t1
        sfence.vma zero, zero

        jr t0
```

在 Trampoline 中，所有 GPR (x1-x31) 均为用户程序所使用的，我们需要在进入 trap / 退出 trap 时保持所有 GPR 一致。

我们将保存用户寄存器的地方称为 Trapframe，大小小于一个页面。

Trapframe 定义在 `proc.h` 中：

```c
struct trapframe {
    /*   0 */ uint64 kernel_satp;    // kernel page table
    /*   8 */ uint64 kernel_sp;      // top of process's kernel stack
    /*  16 */ uint64 kernel_trap;    // usertrap()
    /*  24 */ uint64 epc;            // saved user program counter
    /*  32 */ uint64 kernel_hartid;  // saved kernel tp
    /*  40 */ uint64 ra;
    /*  48 */ uint64 sp;
    /*  ... */
    /* 272 */ uint64 t5;
    /* 280 */ uint64 t6;
};
```

由于 RISC-V 的指令的 destination 均为寄存器，而我们在保存用户寄存器前不能修改寄存器的内容，所以我们起码需要一个能修改的寄存器来给我们操作空间。RISC-V 提供了一个 `sscratch` 寄存器来给 Trap Handler 一个暂存寄存器的地方。我们可以使用 `csrrw a0, sscratch, a0` 交换 `sscratch` 和 `a0` 寄存器。

我们规定，`sscratch` 寄存器保存着用户页表中 Trapframe 所映射的虚拟地址，我们将它放置在 Trampoline 下面一个页，即 `0x0000_003f_ffff_e000`。

在进入 `uservec` 后，我们交换 a0 和 sscratch，此时 a0 为 `0x0000_003f_ffff_e000`，映射到该进程的 `struct trapframe` 结构体。

随后，我们即可使用 a0 + 40 来得到 `trapframe` 中的 ra 字段的地址，所以，我们用 `sd ra, 40(a0)` 等来保存除了 a0 以外的所有用户寄存器。在正确保存用户寄存器后，我们能够修改所有寄存器了，我们将保存在 `sscratch` 中的用户 `a0` 读取到 t0，并写入 trapframe 中，至此我们成功保存了所有用户寄存器。然，我们保存 `sepc` 寄存器。

最后，我们从 `trapframe` 中读取内核相关的数据，如内核的页表 `satp`，内核栈 sp `kernel_sp`，内核的 cpuid (tp寄存器) `kernel_hartid`，以及下一阶段的跳转地址 `kenrel_trap`。

在切换回内核的页表后，我们即可跳转 `tf->kernel_trap` 进入C语言环境处理 User Trap。此时，我们回到了内核的页表。

在 `usertrap` 中，我们先将 stvec 设置为 `kerneltrap`，以此捕捉可能出现的中断和异常。随后读取 scause 处理异常。最后，使用 `usertrapret` 返回用户空间。

```c
void usertrap() {
    set_kerneltrap();

    assert(!intr_get());
    if ((r_sstatus() & SSTATUS_SPP) != 0)
        panic("usertrap: not from user mode");
    
    struct trapframe *trapframe = curr_proc()->trapframe;
    uint64 cause = r_scause();
    
    // handle usertrap according to scause

    assert(!intr_get());
    usertrapret();
}
```

`usertrapret` 先将内核的信息保存到 `trapframe`，修改 `sepc`，设置 `sstatus` 返回 U mode，计算出用户页表的 satp 和 stvec 值，并跳转到 Trampoline 中的 `userret` 地址。

```c
//
// return to user space
//
void usertrapret() {
    if (intr_get())
        panic("usertrapret entered with intr on");

    struct trapframe *trapframe = curr_proc()->trapframe;
    trapframe->kernel_satp      = r_satp();                                 // kernel page table
    trapframe->kernel_sp        = curr_proc()->kstack + KERNEL_STACK_SIZE;  // process's kernel stack
    trapframe->kernel_trap      = (uint64)usertrap;
    trapframe->kernel_hartid    = r_tp();

    w_sepc(trapframe->epc);
    // set up the registers that trampoline.S's sret will use to get to user space.

    // set S Previous Privilege mode to User.
    uint64 x = r_sstatus();
    x &= ~SSTATUS_SPP;  // clear SPP to 0 for user mode
    x |= SSTATUS_SPIE;  // enable interrupts in user mode
    w_sstatus(x);

    // tell trampoline.S the user page table to switch to.
    uint64 satp  = MAKE_SATP(KVA_TO_PA(curr_proc()->mm->pgt));
    uint64 stvec = (TRAMPOLINE + (uservec - trampoline)) & ~0x3;

    uint64 fn = TRAMPOLINE + (userret - trampoline);
    tracef("return to user @%p, fn %p", trapframe->epc);
    ((void (*)(uint64, uint64, uint64))fn)(TRAPFRAME, satp, stvec);
}
```

在调用 `userret` 时，我们传入了3个参数。在汇编中，我们可以使用 a0-a3 引用它们。

我们首先换回用户页表，此时我们即可使用 `0x0000_003f_ffff_e000` 引用 trapframe，然后设置用户的 stvec。

我们先将用户的 a0 存入 `sscratch`，然后从 trapframe 中恢复了其他用户寄存器。最后，我们使用 `csrrw a0, sscratch, a0` 交换 a0 和 `sscratch`，此时 a0 为用户的 a0，`sscratch` 是 trapframe 的虚拟地址。

```asm
.globl userret
userret:
        # userret(TRAPFRAME, pagetable, stvec)
        # switch from kernel to user.
        # usertrapret() calls here.
        # a0: TRAPFRAME, in user page table.
        # a1: user page table, for satp.

        # switch to the user page table.
        csrw satp, a1
        sfence.vma zero, zero

        # switch to the user stvec.
        csrw stvec, a2

        # put the saved user a0 in sscratch, so we
        # can swap it with our a0 (TRAPFRAME) in the last step.
        ld t0, 112(a0)
        csrw sscratch, t0

        # restore all but a0 from TRAPFRAME
        ld ra, 40(a0)
        ld sp, 48(a0)
        # ...
        ld t5, 272(a0)
        ld t6, 280(a0)

        # restore user a0, and save TRAPFRAME in sscratch
        csrrw a0, sscratch, a0

        # return to user mode and user pc.
        # usertrapret() set up sstatus and sepc.
        sret
```

## 用户页表的设置

TODO: proc.c 设置 kstack，trapframe

kvm.c 映射 trampoline

vm.c 映射 trampline 和 trapframe

