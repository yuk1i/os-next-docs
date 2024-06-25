# 开发环境配置

在这部分内容中，我们将向同学们介绍 Linux 发行版 和 Linux 容器，以备后续实验。

Linux是一个免费可用的操作系统，非常适用于操作系统开发。容器是一种轻量级的虚拟化技术，允许将应用程序及其所有运行时环境打包到一个独立的可移植的单元中。

在操作系统实验课程中，我们使用 Ubuntu 24.04 LTS 作为标准的实验环境。

!!! warning

    即便部分同学们已经拥有一个运行着 Linux 发行版的物理机或虚拟机环境，我们依然要求诸位同学参照下述文档为这门课准备一个新的标准环境，以减少可能出现的问题。
    
    此外，我们要求各位同学在系统名中设置自己的学号，以备Lab实验或课程作业需要提交截图。

#### 选择一个合适的 Linux 发行版

如果你恰好有兴趣，并且拥有足够的资源配置一台运行Linux发行版的物理机，那么选择什么样的Linux 发行版是一个十分自然的问题。

不存在最好的 Linux 发行版。当你尝试从众多可选项中选择一个时(Ubuntu, Debian, CentOS, Fedora, openSUSE, ArchLinux...)，这在相当程度上取决于你的个人兴趣。

如果你此前完全不了解 Linux，那么 Ubuntu 是我们所最为推荐的，我们在后续实验中所展示的命令及实验均针对 Ubuntu。
当然，你也可以考虑 Fedora 或者 openSUSE。我们在下面列出的文档将向同学们介绍如何 **在物理机上** 安装这些Linux发行版。

- **Install Ubuntu Desktop：** https://ubuntu.com/tutorials/install-ubuntu-desktop#1-overview
- **Install openSUSE Tumbleweed：** https://www.opensuse.org/
- **Install Fedora Workstation：** https://fedoraproject.org/

不同的 Linux 发行版有不同的包管理工具和系统管理界面。
不过，他们大多遵守类似的“哲学”和设计理念，因而将你在一个Linux 发行版上学到的东西应用到另一个上并非难事。

为了应对后续的实验，我们推荐同学们选择 Ubuntu Desktop、openSUSE Tumbleweed 或者 Fedora workstation。
你也可以选择安装 Ubuntu server、openSUSE Leap 和 Fedora server，但要记得安装一个相应的图形化操作界面。

## 搭建 Linux 虚拟环境

在Windows或者Mac上运行一个Linux虚拟机同样是一个不错的选择，我们在这里向同学们推荐两个相关软件。他们都可以满足我们的需要。

- **VMware：** https://www.vmware.com/products/desktop-hypervisor.html
- **Virtual Box：** https://www.virtualbox.org/wiki/Downloads

在安装好具体的软件后，同学们可以自由选择相应教程以在软件中安装心仪的 Linux 发行版。
由于种类繁杂且相应资源在互联网上十分丰富，因此我们在这里不做推荐。

为应对后续实验，在具体安装虚拟机时，2 vCPU/4G RAM/20G Disk就可以满足需要了。

此外，我们提供了一份已经安装好环境的 Ubuntu 24.04 LTS 虚拟机镜像：

!!! note

    请同学们在安装系统时额外满足如下要求：

    1. 在设定的系统名中包含你的学号。
    2. 语言尽量选择英文，中文路径可能导致部分实验内容无法顺利完成。

> Maybe we can add a simple tutorial like installing Ubuntu after installing VMware on Windows?

## 使用容器构建开发环境

同学们也可以尝试在 Windows 或者 MacOS 上通过运行容器来完成实验，但我们需要事先提醒各位，后续文档中所提供的指令在这类情境下不一定有效。

我们也提供了基于 Windows WSL 2.0 的方案：
