# 使用自编译的工具链

!!! warning

    如有可能，请尽量使用发行版自带的工具链/QEMU 等。

如果你在使用发行版的 gcc/qemu 时遇到问题，并且你确定是环境不一致导致的问题，你可以参照该文档从零编译整个工具链。

## gcc

参照 https://github.com/riscv-collab/riscv-gnu-toolchain：

```shell
$ sudo -i
$ git clone https://github.com/riscv/riscv-gnu-toolchain
$ sudo apt-get install autoconf automake autotools-dev curl python3 python3-pip libmpc-dev libmpfr-dev libgmp-dev gawk build-essential bison flex texinfo gperf libtool patchutils bc zlib1g-dev libexpat-dev ninja-build git cmake libglib2.0-dev libslirp-dev
$ mkdir -p /opt/riscv
$ ./configure --prefix=/opt/riscv
$ make
```