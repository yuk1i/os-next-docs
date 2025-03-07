# macOS + VMware Fusion 

## 安装 VMware Fusion

在 https://dl.cra.moe/CS302-OS-2025-Spring/ 下载 VMware-funsion-macOS.zip。打开 Finder，解压该 zip 后在 payload 文件夹下有一个 "VMware Fusion"，将它拖到左侧"应用程序"后即可。

用 Spotlight 打开 VMware fusion，同意所有权限要求。

你可以选择直接导入 OVF，或者手动创建 Debian 虚拟机。


请你先确认你的 macOS 系统的 CPU 类型是 Intel 还是 Apple Silicon (Apple M系列处理器)。目前，我们只提供对 Apple M系列处理器的支持，不提供 Intel 系列处理器的支持。

## 导入已安装好的镜像

在 https://dl.cra.moe/CS302-OS-2025-Spring/ 下载 `OSLab-2025S-macOS-arm64 的克隆.zip`，下载后解压。

打开 VMware Fusion。在菜单栏中： 窗口 -> 虚拟机资源库。打开虚拟机列表。

![alt text](<../../assets/env/2025-02-17 20.52.31.png>)

将解压出来的 `OSLab-2025S-macOS-arm64 的克隆` 直接拖到虚拟机列表中。

![alt text](<../../assets/env/2025-02-17 20.52.37.png>)

双击启动，并验证环境。