int main() {
    char buf[50];
    strcpy(buf, "Hello");
    printf("strcpy: %s (len=%d)\n", buf, strlen(buf));
    
    strcat(buf, " World");
    printf("strcat: %s (len=%d)\n", buf, strlen(buf));
    
    printf("strcmp(apple, banana) = %d\n", strcmp("apple", "banana"));
    printf("strcmp(apple, apple) = %d\n", strcmp("apple", "apple"));
    printf("strcmp(banana, apple) = %d\n", strcmp("banana", "apple"));
    
    return 0;
}
