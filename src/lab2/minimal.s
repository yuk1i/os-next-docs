.section .data
    hello_msg: .asciz "Hello, World!\n"   # 定义字符串，末尾自动加 '\0'

.section .text
    .globl _start

_start:
    # 使用 write 系统调用 (syscall number: 1)
    movq $1, %rax           # 系统调用号 1 = sys_write
    movq $1, %rdi           # 文件描述符 1 = stdout
    leaq hello_msg(%rip), %rsi  # 要写入的字符串地址
    movq $14, %rdx          # 字符串长度 (包括换行符)
    syscall                 # 调用系统调用

    # 使用 exit 系统调用 (syscall number: 60)
    movq $60, %rax          # 系统调用号 60 = sys_exit
    xorq %rdi, %rdi         # 退出状态码 0
    syscall                 # 调用系统调用
