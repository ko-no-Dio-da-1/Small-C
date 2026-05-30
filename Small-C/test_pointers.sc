int main() {
    int x = 42;
    int *p;
    int arr[3];
    int *ap;
    
    p = &x;
    printf("x=%d, *p=%d\n", x, *p);
    
    *p = 99;
    printf("x=%d, *p=%d\n", x, *p);
    
    arr[0] = 10;
    arr[1] = 20;
    arr[2] = 30;
    
    ap = arr;
    printf("ap[0]=%d, ap[1]=%d, ap[2]=%d\n", *ap, *(ap + 1), *(ap + 2));
    
    *(ap + 1) = 200;
    printf("arr[1]=%d\n", arr[1]);
    
    return 0;
}
