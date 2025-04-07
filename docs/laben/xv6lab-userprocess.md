# User Process

## Lab Objectives

1. Understand user address space
2. Master the implementation principles of fork\exec\exit\wait

!!!warning "xv6-lab6 Code Branch"
    
    https://github.com/yuk1i/SUSTech-OS-2025/tree/xv6-lab6

    Use the command `git clone https://github.com/yuk1i/SUSTech-OS-2025 -b xv6-lab6 xv6lab6` to download the xv6-lab6 code.

    Use `make run` to run the kernel for this Lab, which will start the first user process `init`, and `init` will start the Shell process `sh`.

    You will see the user space structure of the `sh` process.

    ```
    init: starting sh
    [INFO  0,2] exec: exec-ed sh, mm structure:
    mm 0xfffffffd000fff48:
    pgt: 0xffffffc080d25000
    ref: 1
    vma: 0xfffffffd010bfd38
        [0x00000000fffe8000, 0x00000000ffff0000), flags: ---U-WR-
        [0x0000000000406000, 0x0000000000406000), flags: ---U-WR-
        [0x0000000000405000, 0x0000000000406000), flags: ---U-WR-
        [0x0000000000404000, 0x0000000000405000), flags: ---U--R-
        [0x0000000000402000, 0x0000000000404000), flags: ---UX-R-
    === PageTable at 0xffffffc080d25000 ===
    ...
    ```

    **Note:** The initialization code for `struct mm` in this Lab has been modified compared to the previous Lab code.

## Address Space

First, let's review how the address space in U-mode is described from the perspective of the kernel and CPU.

For the CPU, all memory accesses in U-mode, including instruction fetch (IF), memory read (LD), and memory write (ST), must go through page table address translation. The CPU uses the CSR `satp` as the base address of the page table for address translation.

Therefore, the kernel needs to set up a page table structure for user processes. In the kernel, we use `struct mm` to manage user memory, and each PCB `struct proc` has a pointer `*mm` pointing to `struct mm`.

```c
// os/vm.h
struct mm {
    spinlock_t lock;

    pagetable_t __kva pgt;
    struct vma* vma;
};
```

Each `struct mm` contains a page table `pgt`, which is the `satp` used by the user process. We can observe this in `usertrapret` and trampoline:

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

From the kernel's perspective, **the user's memory space consists of several contiguous virtual address regions**. Each contiguous region is represented by a `struct vma` (Virtual Memory Area), and they are linked together in a list. Each `vma` contains the start and end addresses of the region (aligned to page boundaries) and the permissions for the region.

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

Note that `struct vma` contains a `struct mm*` pointer, indicating that each VMA belongs to a `struct mm`.

### Loading

A user **program** specifies which contiguous regions (also called segments) it needs to load during loading. 
The following is the output of `llvm-readelf-19 -a user/build/sh`, showing that the `sh` program requires three contiguous regions when loading (LOAD):

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

We can use the `mm_print` function in the `exec` function in `os/proc.c` to print the `struct mm` structure and `pgt` page table of the **process** after `sh` is loaded.

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

We can observe that in the vma linked list, three regions correspond to the LOAD segments in the ELF file, which are the `.text`, `.rodata`, and `.data/.bss` segments.
```
    [0x0000000000402000, 0x0000000000404000), flags: ---UX-R-
    [0x0000000000404000, 0x0000000000405000), flags: ---U--R-
    [0x0000000000405000, 0x0000000000406000), flags: ---U-WR-
```

Another address starting with `0xfffe` is the stack area of the process.
```
    [0x00000000fffe8000, 0x00000000ffff0000), flags: ---U-WR-
```

Additionally, there is a region of size 0, which follows all LOAD segments. This is the heap area (Heap, known as `Program Break` in ancient operating systems). The process needs to use the `sbrk` system call to expand or shrink the heap area.

```
    [0x0000000000406000, 0x0000000000406000), flags: ---U-WR-
```

### Overview Diagram

This diagram shows the data structures used by the kernel to manage the user address space of the `sh` process.

![alt](../assets/xv6lab-userprocess/userprocess-vma.png)

## fork

The fork system call is used in the operating system to create a new process. When a process calls fork, it creates a new process (called the child process) that is almost identical to the parent process. The child process copies the parent process's address space and all register values. The only difference is the return value of the fork call:

- Parent process: fork returns the PID (process ID) of the child process.

- Child process: fork returns 0.

The implementation of `fork` in xv6 is located in the `fork` function in `os/proc.c`. Here is a simplified version:

```c
int fork() {
    int ret;
    struct proc *np = allocproc();  // child process
    struct proc *p = curr_proc();   // parent process

    // create a new struct mm for child process
    np->mm = mm_create(np->trapframe);

    // Copy user memory from parent to child.
    mm_copy(p->mm, np->mm);

    // copy saved user registers.
    *(np->trapframe) = *(p->trapframe);

    // Cause fork to return 0 in the child.
    np->trapframe->a0 = 0;
    np->parent        = p;

    // add the child process to scheduler
    np->state         = RUNNABLE;
    add_task(np);

    return np->pid; // return value for the parent process
}
```

The caller of `fork` is the parent process, and the new PCB allocated with `allocproc` is the child process. We modify the trapframe of `np` to ensure that the two processes have different return values. Note that we do not modify the trapframe of `p` because the `syscall` function will write the return value of the `fork` function into the `a0` register in the trapframe when dispatching the system call. We only need to make `fork` return the PID of the child process.

The `mm_copy` function (located in `os/vm.c`) ultimately implements the copying of all `vma`s: it creates new `struct vma`s under the new `mm`, assigns the attributes in `vma`, calls `mm_mappages` to map the `vma`, and finally copies the actual memory data.

!!!warning "Trapframe and Trampoline"
    In the overview diagram, we can see that the user page table includes Trapframe and Trampoline, but the `vma` linked list does not include these two pages. This design is intentional, not a bug.

    Consider the **lifecycle** of `vma` (user's Virtual Memory Area). The `exec` system call will delete all existing user memory mappings and replace them with new ones, but the PCB (i.e., `struct proc`) object does not need to be destroyed and recreated, and the Trapframe does not seem to require reallocation of physical pages.
    
    Therefore, the lifecycle of Trapframe and Trampoline is actually consistent with the process itself, not with any `vma` entry.

    In implementation, we allocate the Trapframe page during system initialization, i.e., in `proc_init`, and map Trampoline and Trapframe in `create_mm`.

## exec

The exec system call is used to execute a new program and replace the current process's memory space with the new program. Unlike fork, exec does not create a new process but replaces the current process's code, data, and stack with a new program.

When exec is called, the current process's address space is replaced by the new program's code and data. The original process's code, data, and stack are cleared, and the new program is loaded. Then, the current process's execution flow jumps to the new program's entry point and continues executing the new program's code.

```c
int exec(char *name, char *args[]) {
    struct user_app *app = get_elf(name);

    struct proc *p = curr_proc();

    // execve does NOT preserve memory mappings:
    //  free VMAs including program_brk, and ustack
    // load_user_elf() will create a new mm for the new process and free the old one
    //  , if page allocations all succeed.
    // Otherwise, we will return to the old process.
    // However, keep the phys page of trapframe, because it belongs to struct proc.
    load_user_elf(app, p, args);

    // syscall() will overwrite trapframe->a0 to the return value.
    return p->trapframe->a0;
}
```

The `load_user_elf` function has been modified compared to the previous Lab. We need to note that **allocating physical pages may fail**. When the system does not have enough memory, the `exec` function fails to execute, and we need to return to the original process to continue execution, releasing the half-allocated memory.

Therefore, we create a new `struct mm` and load the segments from the ELF file and the process stack into it. Only after we no longer need to allocate memory (`mm_mappages`) do we clear and overwrite `p->mm`.

```c
// os/loader.c, Simpilfied version.
int load_user_elf(struct user_app *app, struct proc *p, char *args[]) {

    // create a new mm for the process, including trapframe and trampoline mappings
    struct mm *new_mm = mm_create(p->trapframe);
    
    Elf64_Ehdr *ehdr      = (Elf64_Ehdr *)app->elf_address;
    for (int i = 0; i < ehdr->e_phnum; i++) {
        struct vma *vma = mm_create_vma(new_mm);
        // Load Segment from phdr.
        if (mm_mappages(vma) < 0)   // if page allocation fails, jump to bad.
            goto bad;
    }
    // setup brk: zero
    mm_mappages(vma_brk);
    // setup stack
    mm_mappages(vma_ustack);

    // from here, we are done with all page allocation 
    // (including pagetable allocation during mapping the trampoline and trapframe).

    // free the old mm.
    if (p->mm)
        mm_free(p->mm);    
    
    // we can modify p's fields because we will return to the new exec-ed process.
    p->mm      = new_mm;
    // setup trapframe
    p->trapframe->epc = ehdr->e_entry;
    
    return 0;

    // otherwise, page allocations fails. we will return to the old process.
bad:
    warnf("load (%s) failed: %d", app->name, ret);
    mm_free(new_mm);
    return ret;
}
```

## Lifecycle

### exit

The `exit` system call is used to terminate the current process and return an exit status to the operating system. The `exit` system call never returns. After calling `exit`, **some resources of the process are not immediately reclaimed by the operating system**. Moreover, `exit` does not immediately make the process disappear from the parent process's view. It remains in the "zombie process" state until the parent process obtains the child process's exit status through the `wait` system call and reclaims the process.

Here is a simplified version of `exit`. Note that we do not reclaim user resources here: up to this Lab, we have only introduced one type of user resource, namely user memory.

In `exit`, we only set our state to `ZOMBIE` and save the exit code to `p->exit_code`. Then, we use `wakeup` to **wake up** our parent process.

```c
// Exit the current process.
void exit(int code) {
    int wakeinit = 0;
    struct proc *p = curr_proc();

    acquire(&wait_lock);
    // reparent

    // wakeup wait-ing parent.
    wakeup(p->parent);

    acquire(&p->lock);
    p->exit_code = code;
    p->state     = ZOMBIE;
    release(&wait_lock);

    sched();
    panic_never_reach();
}
```

!!!warning "wakeup"
    We will explain locks and synchronization in detail in subsequent synchronization Labs, including what `wait_lock` is in the above code.

    In this Lab, we only need to know that the parent process will **sleep** when `wait` cannot find a child process in the `ZOMBIE` state. The child process `exit` will set itself to `ZOMBIE`, which breaks **the condition for the parent process to sleep**, so we wake up the parent process to prevent it from sleeping.


### reparent

"Reparent" refers to the operating system changing the parent process of a process to the init process (process with PID 1) when the parent process terminates. This is a system-level management mechanism to ensure that when the parent process terminates, the child process still has a parent process to perform necessary operations such as resource reclamation and process management.

The reparent mechanism is mainly used to avoid the "orphan process" problem and ensure that system resources are properly reclaimed. In xv6, `init` is like an "orphanage," responsible for reclaiming the grandchild processes created by child processes.

```c
// user/src/init.c

for (;;) {
    // this call to wait() returns if the shell exits,
    // or if a parentless process exits.
    wpid = wait(-1, NULL);
    if (wpid == pid) {
        // the shell exited; restart it.
        printf("init: sh exited, restarting...\n");
        break;
    } else {
        // it was a parentless process; do nothing.
        printf("init: wait a parentless process %d\n", wpid);
    }
}
```
