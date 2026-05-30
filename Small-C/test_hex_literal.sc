int main() {
    int a = 0xAB;
    int b = 0x0F;
    printf("a = %d, b = %d\n", a, b);
    printf("a & b = %d\n", a & b);
    printf("a | b = %d\n", a | b);
    printf("a ^ b = %d\n", a ^ b);
    printf("~a = %d\n", ~a);
    printf("b << 4 = %d\n", b << 4);
    printf("a >> 2 = %d\n", a >> 2);
    return 0;
}
