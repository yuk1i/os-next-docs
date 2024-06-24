# 在 Ubuntu 中配置开发环境

到这一步时，请确保你已经配置好 Linux 环境，能打开一个 Terminal 执行命令。

!!! warning

    请使用尽可能新的发行版本。以下代码均已 Ubuntu 24.04 LTS 为基准。

## 安装 gcc 工具链以及 QEMU

使用包管理器 apt 安装依赖：

```sh
sudo apt update && sudo apt install gcc-riscv64-unknown-elf qemu-system-misc git make cmake python3-pip elfutils gdb-multiarch
```

安装完成后，运行 `riscv64-unknown-elf-gcc --version`，`qemu-system-riscv64 --version` 和 `gdb-multiarch --version` 检查版本：

```shell
$ riscv64-unknown-elf-gcc --version
riscv64-unknown-elf-gcc (13.2.0-11ubuntu1+12) 13.2.0
Copyright (C) 2023 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

$ qemu-system-riscv64 --version
QEMU emulator version 8.2.2 (Debian 1:8.2.2+ds-0ubuntu1)
Copyright (c) 2003-2023 Fabrice Bellard and the QEMU Project developers

$ gdb-multiarch --version
GNU gdb (Ubuntu 15.0.50.20240403-0ubuntu1) 15.0.50.20240403-git
Copyright (C) 2024 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
```

请确保 gcc 版本 >= 13.0.0，qemu-system-riscv64 版本 >= 8.0.0，gdb-multiarch 版本 >= 15

如果你均安装好了以上依赖，请尝试编译并运行 [Hello World](helloworld.md)