# C 语言基础

!!! warning "C 语言基础"

    如果你没有学习过 C 语言，我们 **非常建议** 你提前观看于老师的 C/C++ 课程 https://www.bilibili.com/video/BV1Vf4y1P7pq ，观看到第 6.5 章节有助于你了解基本的 C 语言语法。

!!! warning "RISC-V 汇编"

    我们期望你已经完成了《计算机组成原理》课程，并了解 RISC-V 汇编的基础知识。

    此外，请常备 《The RISC-V Instruction Set Manual, Volume I: User-Level ISA, Version 2.1》(riscv-spec-v2.1.pdf) 与 《The RISC-V Instruction Set Manual, Volume II: Privileged Architecture, Document Version 20211203》(riscv-privileged-20211203.pdf) 作为参考 RISC-V 汇编的参考手册。

## 类型

在 C 语言中，整数类型有 long, int, short, char 等。
在绝大多数情况下，int 类型为 32 位长，而 long 类型的长度取决于 ABI（Application Binary Interface，在编译时由用户指定）。
为了避免编译目标架构的不同而导致 long、int 等类型实际长度与我们预想的不一致，在系统编程中，我们会使用定长的整形，如 uint64_t, int32_t 等。
在不同的ABI/编译器环境下，使用这一些类型保证了它们绝对是指定长度的。

例如，在 `os/types.h` 中：

```c title="os/types.h"
typedef unsigned int uint;
typedef unsigned short ushort;
typedef unsigned char uchar;
typedef unsigned char uint8;
typedef unsigned short uint16;
typedef unsigned int uint32;
typedef unsigned long uint64;
```

我们定义了 `uint64`, `uint32` 等类型分别为 `unsigned long` 和 `unsigned int`。
由于我们面向 riscv64 架构进行编程，我们可以确保在我们的 XV6 中，它们是 64 / 32 位的。

!!! warning "unsigned"

    注意在C语言中值在int类型取值范围内的整数字面量的默认类型是int。
    
    当unsigned int与有符号整数（如int）比较时，有符号整数会被提升为unsigned int。如果常数为负数，提升后可能变成一个非常大的无符号值，导致比较结果与预期不符。

    可以尝试执行以下代码，观察结果：
    ![image](https://github.com/user-attachments/assets/7abc8a00-e968-424e-93be-d489d28392c4)


## 编译系统

在计算机组成原理课程中，我们简要的介绍了 C 语言的编译系统。通常来说，编译一个程序分为以下几步：

![image](../assets/lab1/lab1-compilation-system.png)

- 源代码 .c 文件经过 Pre-processor 预处理 cpp 得到 .i 文件

  .i 文件是 GCC 预处理阶段生成的中间文件，包含了展开的头文件、宏定义和条件编译后的代码。使用 gcc -E 可以生成 .i 文件。
  
- .i 文件通过编译器 cc1 编译器得到汇编文件 .s

  编译器对.i文件进行语法检查，检查无误后将.i文件转换成机器可以理解的汇编代码（人类可阅读形式的机器代码），在此过程中优化器可以对代码进行优化。

- .s 文件通过汇编器 as 得到 Relocatable objects (可重定位文件) .o

  在此过程中，汇编器将汇编代码转换为目标代码（机器代码-直接在机器上执行的代码，人类不可读）。
  
- 链接器 ld 链接所有 .o 文件得到最终的可执行文件 

在 Linux 系统上，目标文件及可执行文件通常以 **ELF (Executable and Linkable Format)** 文件格式存储。
ELF 文件分为不同的段 **Section**，用于存储特定类型的数据，如代码（.text）、数据（.data）和符号表（.symtab），每个段都有其专门的用途和属性。
我们可以通过 binutils 中的 readelf 工具来分析 ELF 文件。

通常来说，我们会用"编译器"来指代整个编译与链接过程中用到的所有工具，尽管编译器和链接器是两个不同的程序。特别的，当我们讨论编译器和链接器时，我们会将进行 预处理、汇编、编译 等步骤的工具集合统称为编译器；将最后的链接步骤所用的工具称为链接器。

<h2 style="color: orange;">实验步骤1：观察C语言编译过程</h2>

下面是一个简单的C语言代码示例，适合用于观察GCC编译过程中的 `.i`、`.s`、`.o` 文件：

```c
// main.c
#include <stdio.h>

int main() {
    int a = 10;
    int b = 20;
    int sum = a + b;
    printf("Sum: %d\n", sum);
    return 0;
}
```

#### 观察编译过程

1. **预处理（Preprocessing）**：生成 `.i` 文件
   ```bash
   gcc -E main.c -o main.i
   ```
   这会生成 `main.i` 文件，其中包含了预处理后的代码（宏展开、头文件包含等），可以通过 `cat main.i` 查看其内容。

2. **编译（Compilation）**：生成 `.s` 文件
   ```bash
   gcc -S main.i -o main.s
   ```
   这会生成 `main.s` 文件，其中包含了汇编代码，可以通过 `cat main.s` 查看其内容

4. **汇编（Assembly）**：生成 `.o` 文件
   ```bash
   gcc -c main.s -o main.o
   ```
   这会生成 `main.o` 文件，其中包含了目标代码（机器代码），可以通过 `objdump` 工具来分析 `main.o` 的内容。例如使用 `objdump -d hello.o` 可以查看机器码及其对应的汇编指令。 

5. **链接（Linking）**：生成可执行文件
   ```bash
   gcc main.o -o main
   ```
   这会生成可执行文件 `main`，可以通过 `objdump` 工具来分析其内容。

## Definition 和 Declaration

Definition (定义) 和 Declaration (声明) 是 C 语言中非常容易混淆的两个概念。

Declaration 声明了一个符号（变量、函数等），和它的的一些基础信息（如变量类型、函数参数类型、函数返回类型等）。这使得编译器在编译阶段能找到这些符号。
而 Definition 实际上会为该符号分配地址。在链接阶段，链接器会为这些符号分配地址（如函数地址、全局变量地址）。

!!! info "Symbol (符号)"

    在 C 语言中，符号（Symbol）是编译器用来表示程序中各种实体（如变量、函数、宏、类型名等）的名称。每个符号在编译过程中被关联到特定的内存地址或其他资源。当程序被编译时，编译器会为这些符号创建符号表 (Symbol Table)，记录它们的名称、类型、作用域以及对应的内存地址或值。

    简而言之，符号是程序中代表实体的名字，编译器通过符号表来管理和解析这些名字。

通常，我们会在头文件中 (如 a.h, header file) 中使用 `extern int a` 来 **声明** 一个变量 `a`，这使得所有引用该头文件 (`#include "a.h"`) 的 .c 文件都能找到 `a` 这个符号。并且在 a.c 中 **定义** 这个变量，这使得链接器为该变量分配内存地址。

额外的，当编译器遇到了声明 (Declaration) 过但是没有定义 (Definition) 过的符号时 (如 printf)，编译器会假定该符号会在其他 Object 文件中被定义，留下一些信息后交给链接器寻找这个符号。

在定义全局变量时，我们要确保变量名是唯一的。

如果我们希望定义一些仅局部可见的变量，我们可以在 .c 文件中使用 static 关键字。

现在，你是否理解了链接中常出现的两种错误：multiple definition 和 undefined reference 的原因？

- `riscv64-unknown-elf-ld: build/os/proc.o:os/proc.c:14: multiple definition of 'idle'; build/os/main.o:os/main.c:7: first defined here`
    - 在不同的 .c 文件中定义了多次 `idle` 变量。
- `riscv64-unknown-elf-ld: build/os/proc.o: in function 'proc_init': os/proc.c:38:(.text+0xd0): undefined reference to 'idle'`
    - 在头文件中声明了 `idle` 变量，但是没有定义它。
