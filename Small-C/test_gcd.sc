int gcd(int a, int b) {
    int temp;
    while (b != 0) {
        temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

int main() {
    printf("GCD(48, 18) = %d\n", gcd(48, 18));
    printf("GCD(100, 35) = %d\n", gcd(100, 35));
    return 0;
}
