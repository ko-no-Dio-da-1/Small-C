int g = 0;

int incr() {
    g = g + 1;
    return 1;
}

int main() {
    int x;
    
    // Short circuit AND: 0 && incr() -> incr() is NOT evaluated
    x = 0 && incr();
    printf("AND 1: x=%d, g=%d\n", x, g);
    
    // Non short circuit AND: 1 && incr() -> incr() IS evaluated
    x = 1 && incr();
    printf("AND 2: x=%d, g=%d\n", x, g);
    
    // Short circuit OR: 1 || incr() -> incr() is NOT evaluated
    x = 1 || incr();
    printf("OR 1: x=%d, g=%d\n", x, g);
    
    // Non short circuit OR: 0 || incr() -> incr() IS evaluated
    x = 0 || incr();
    printf("OR 2: x=%d, g=%d\n", x, g);
    
    return 0;
}
