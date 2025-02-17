
## 编译与运行内核

克隆内核代码和用户程序代码仓库：

```shell

git clone https://github.com/yuk1i/SUSTechOS
cd SUSTechOS
git clone https://github.com/yuk1i/SUSTechOS-2025S-user user
```

编译用户程序：

```shell
make user
```

编译内核:

```shell
make
```

在 QEMU 中运行内核：


```shell
make run
```

如果一切正常，你将能够看到：

```
OpenSBI v1.5
   ____                    _____ ____ _____
  / __ \                  / ____|  _ \_   _|
 | |  | |_ __   ___ _ __ | (___ | |_) || |
 | |  | | '_ \ / _ \ '_ \ \___ \|  _ < | |
 | |__| | |_) |  __/ | | |____) | |_) || |_
  \____/| .__/ \___|_| |_|_____/|____/_____|
        | |
        |_|

Platform Name             : riscv-virtio,qemu
Platform Features         : medeleg
Platform HART Count       : 1
Platform IPI Device       : aclint-mswi
Platform Timer Device     : aclint-mtimer @ 10000000Hz
Platform Console Device   : uart8250
Platform HSM Device       : ---
Platform PMU Device       : ---
Platform Reboot Device    : syscon-reboot
Platform Shutdown Device  : syscon-poweroff
Platform Suspend Device   : ---
Platform CPPC Device      : ---
Firmware Base             : 0x80000000
Firmware Size             : 327 KB
Firmware RW Offset        : 0x40000
Firmware RW Size          : 71 KB
Firmware Heap Offset      : 0x49000
Firmware Heap Size        : 35 KB (total), 2 KB (reserved), 11 KB (used), 21 KB (free)
Firmware Scratch Size     : 4096 B (total), 416 B (used), 3680 B (free)
Runtime SBI Version       : 2.0

Domain0 Name              : root
Domain0 Boot HART         : 0
Domain0 HARTs             : 0*
Domain0 Region00          : 0x0000000000100000-0x0000000000100fff M: (I,R,W) S/U: (R,W)
Domain0 Region01          : 0x0000000010000000-0x0000000010000fff M: (I,R,W) S/U: (R,W)
Domain0 Region02          : 0x0000000002000000-0x000000000200ffff M: (I,R,W) S/U: ()
Domain0 Region03          : 0x0000000080040000-0x000000008005ffff M: (R,W) S/U: ()
Domain0 Region04          : 0x0000000080000000-0x000000008003ffff M: (R,X) S/U: ()
Domain0 Region05          : 0x000000000c400000-0x000000000c5fffff M: (I,R,W) S/U: (R,W)
Domain0 Region06          : 0x000000000c000000-0x000000000c3fffff M: (I,R,W) S/U: (R,W)
Domain0 Region07          : 0x0000000000000000-0xffffffffffffffff M: () S/U: (R,W,X)
Domain0 Next Address      : 0x0000000080200000
Domain0 Next Arg1         : 0x000000009fe00000
Domain0 Next Mode         : S-mode
Domain0 SysReset          : yes
Domain0 SysSuspend        : yes

Boot HART ID              : 0
Boot HART Domain          : root
Boot HART Priv Version    : v1.12
Boot HART Base ISA        : rv64imafdch
Boot HART ISA Extensions  : sstc,zicntr,zihpm,zicboz,zicbom,sdtrig,svadu
Boot HART PMP Count       : 16
Boot HART PMP Granularity : 2 bits
Boot HART PMP Address Bits: 54
Boot HART MHPM Info       : 16 (0x0007fff8)
Boot HART Debug Triggers  : 2 triggers
Boot HART MIDELEG         : 0x0000000000001666
Boot HART MEDELEG         : 0x0000000000f0b509


=====
Hello World!
=====

Boot stack: 0x000000008021d000
clean bss: 0x000000008021e000 - 0x0000000080228000
Boot m_hartid 0
[INFO  0,-1] bootcpu_entry: basic smp inited, thread_id available now, we are cpu 0: 0x00000000802270d8
Kernel Starts Relocating...
Kernel size: 0x0000000000028000, Rounded to 2MiB: 0x0000000000200000
[INFO  0,-1] bootcpu_start_relocation: Kernel phy_base: 0x0000000080200000, phy_end_4k:0x0000000080228000, phy_end_2M 0x0000000080400000
Mapping Identity: 0x0000000080200000 to 0x0000000080200000
Mapping kernel image: 0xffffffff80200000 to 0x0000000080200000
Mapping Direct Mapping: 0xffffffc080400000 to 0x0000000080400000
Enable SATP on temporary pagetable.
Boot HART Relocated. We are at high address now! PC: 0xffffffff80203cc4
[INFO  0,-1] kvm_init: boot-stage page allocator: base 0xffffffc080400000, end 0xffffffc080600000
[INFO  0,-1] kvmmake: Memory after kernel image (phys) size = 0x0000000003c00000
[INFO  0,-1] kvm_init: enable pageing at 0x8000000000080400
[INFO  0,-1] kvm_init: boot-stage page allocator ends up: base 0xffffffc080400000, used: 0xffffffc080411000
Relocated. Boot halt sp at 0xffffffffff001fb0
Boot another cpus.
- booting hart 1: hsm_hart_start(hartid=1, pc=_entry_sec, opaque=1) = -3. waiting for hart online
skipped for hart 1
- booting hart 2: hsm_hart_start(hartid=2, pc=_entry_sec, opaque=1) = -3. waiting for hart online
skipped for hart 2
- booting hart 3: hsm_hart_start(hartid=3, pc=_entry_sec, opaque=1) = -3. waiting for hart online
skipped for hart 3
System has 1 cpus online

UART inited.
[INFO  0,-1] kpgmgrinit: page allocator init: base: 0xffffffc080411000, stop: 0xffffffc084000000
[INFO  0,-1] allocator_init: allocator mm inited base 0xfffffffd00000000
[INFO  0,-1] allocator_init: allocator vma inited base 0xfffffffd01000000
[INFO  0,-1] allocator_init: allocator proc inited base 0xfffffffd02000000
[INFO  0,-1] allocator_init: allocator kstrbuf inited base 0xfffffffd03000000
applist:
        init
        sh
        test_arg
        test_malloc
[INFO  0,-1] load_init_app: load init proc init
[INFO  0,-1] bootcpu_init: start scheduler!
init: starting sh

```
