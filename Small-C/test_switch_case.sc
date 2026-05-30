int run_switch(int val) {
    int res = 0;
    switch (val) {
        case 1:
            res = 10;
            break;
        case 2:
            res = 20;
            // fall through
        case 3:
            res += 5;
            break;
        default:
            res = 999;
    }
    return res;
}

int main() {
    printf("case 1: %d\n", run_switch(1));
    printf("case 2: %d\n", run_switch(2));
    printf("case 3: %d\n", run_switch(3));
    printf("case 4: %d\n", run_switch(4));
    return 0;
}
