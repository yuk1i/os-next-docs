在这部分内容中，我们将引导同学们在windows系统中安装VMware Workstation Pro, 并在VMware中配置Ubuntu虚拟机

### 安装 VMware Workstation Pro 16

同学们可以通过以下链接下载VMware Workstation Pro 17，并将其安装在自己的计算机中。

> https://dl.cra.moe/CS302-OS-2025-Spring/

[Download VMware Workstation Pro](https://dl.cra.moe/CS302-OS-2025-Spring/)

![alt text](../../assets/env/1739626473455.png)

接下来，关于安装 Ubuntu 24.04，我们提供两种选择，大家可以选择下载已经搭载实验环境的 Ubuntu 系统镜像 (OVF) 导入进虚拟机，或者 Ubuntu 官方原版镜像。

### 安装Ubuntu24.04

**1. 导入已搭载实验环境的系统镜像**

此步骤为在VMware中导入已经搭载实验环境的系统镜像。如你已经拥有一个现有环境，例如你自己的用的 Linux 虚拟机/物理机环境，可参考 `手动环境配置` 的步骤在系统中配置实验环境，不过我们更加推荐使用我们提供的环境以防止系统版本导致的实验差异。

首先通过以下链接下载Ubuntu24.04的ovf格式（Open Virtualization Format）文件并进行解压。

![image](https://github.com/user-attachments/assets/cdabcc01-f4c5-4259-8a59-4e6f8e7a7bf8)

之后，打开VMware选择`文件`->`打开`，找到ovf文件选择打开，输入虚拟机名称后等待导入完成即可。

![alt text](../../assets/env/1739636121752.png)

![image](https://github.com/user-attachments/assets/fca4c76a-e2bc-46a9-9f2a-d97c382c70f6)

**2. 安装官方ubuntu 24.04并配置实验环境**

同学们可以通过以下链接下载原版Ubuntu24.04镜像，并将其安装在自己的虚拟机中。

[Download Ubuntu 24.04](https://dl.cra.moe/CS302-OS-2025-Spring/)

![alt text](../../assets/env/1739626789598.png)

下载好镜像后，打开VMware workstation，选择`创建新的虚拟机`：

![alt text](../../assets/env/1739626866726.png)

根据以下指引完成虚拟机配置：

!!! note

    请同学们在安装系统时尽量满足以下要求：

    1. 语言尽量选择英文，中文路径可能导致实验内容无法顺利完成
    
    2. CPU尽量选择4核或以上
    
    3. 虚拟机硬盘空间建议选择30G以上

![alt text](../../assets/env/1739626927161.png)

![alt text](../../assets/env/1739626967069.png)

![alt text](../../assets/env/1739627013900.png)

![alt text](../../assets/env/1739627469200.png)

![alt text](../../assets/env/1739627842844.png)

![alt text](../../assets/env/1739627870793.png)

![alt text](../../assets/env/1739627924557.png)

![alt text](../../assets/env/1739628024569.png)

![alt text](../../assets/env/1739628041415.png)

![alt text](../../assets/env/1739628052406.png)

![alt text](../../assets/env/1739628065758.png)

![alt text](../../assets/env/1739628131052.png)

![alt text](../../assets/env/1739628156200.png)

![alt text](../../assets/env/1739628170685.png)

之后运行虚拟机完成虚拟机安装即可。

另外，由于原版Ubuntu系统不包含本课程实验的开发环境，还需要参考`环境配置`完成实验开发环境配置。除此之外，我们还推荐安装vscode用于代码的阅读与编写。


