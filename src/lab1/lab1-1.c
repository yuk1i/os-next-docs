#include <stdio.h>

int a = 0;

void recursive(int depth) {
    int c;
    if (depth == 5) return;
    printf("[%d] c is at: %p\n", depth, &c);
    recursive(depth + 1);
}

int main() {
    int b;
    printf("main is at: %p\n", &main);
    printf("a is at: %p\n", &a);
    printf("b is at: %p\n", &b);
    recursive(0);
}