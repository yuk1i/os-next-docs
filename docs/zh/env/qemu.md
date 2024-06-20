# Qemu

qemu是一个硬件模拟器，可以模拟不同架构的CPU。
它甚至可以模拟不同架构的 CPU，比如说在使用 Intel X86 的 CPU 的电脑中模拟出一个 ARM 的电脑或 RISC-V 的电脑。
qemu 同时也是一个非常简单的虚拟机，给它一个硬盘镜像就可以启动一个虚拟机，并且可以定制虚拟机的配置，比如要使用的CPU 、显卡、网络配置等，指定相应的命令行参数就可以了。

Qemu支持许多格式的磁盘镜像，包括 VirtualBox 创建的磁盘镜像文件。
它同时也提供一个创建和管理磁盘镜像的工具qemu-img。

如果你想查看 QEMU 所使用的命令行参数，直接查看其文档即可。

- 在线文档：https://www.qemu.org/docs/master/about/index.html
- 本地文档：`qemu-system-x86_64 --help`

我们需要使用 Qemu 5.0.0 版本进行实验，而很多 Linux 发行版的软件包管理器默认软件源中的 Qemu版本过低。因此，我们需要从源码手动编译安装 Qemu 模拟器。

```sh linenums="1" hl_lines="2 3" title="example"
# 安装编译所需的依赖包
sudo apt install autoconf automake autotools-dev curl libmpc-dev libmpfr-dev libgmp-dev gawk build-essential bison flex texinfo gperf libtool patchutils bc zlib1g-dev libexpat-dev pkg-config libglib2.0-dev libpixman-1-dev git tmux python3 python3-pip
```

```c
int main() {
    int a = 1;
} 
```

