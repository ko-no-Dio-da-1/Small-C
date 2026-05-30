int main() {
    int i = 1;
    printf("while-continue: ");
    while (i <= 5) {
        if (i == 3) {
            i += 1;
            continue;
        }
        printf("%d ", i);
        i += 1;
    }
    printf("\n");
    
    printf("for-break: ");
    for (i = 1; i <= 10; i = i + 1) {
        if (i == 6) break;
        printf("%d ", i);
    }
    printf("\n");
    
    printf("do-while-break: ");
    i = 10;
    do {
        printf("%d ", i);
        i += 1;
        if (i == 13) break;
    } while (i < 20);
    printf("\n");
    
    return 0;
}
