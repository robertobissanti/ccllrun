#include <stdio.h>
#include <stdint.h>

int parse_int32(const char *s, int32_t *out);

int main(void) {
    int32_t v;
    int r;
    r = parse_int32("  -2147483648  ", &v); printf("'%s' => %d, %d\n", "  -2147483648  ", v, r);
    r = parse_int32("  2147483647  ", &v); printf("'%s' => %d, %d\n", "  2147483647  ", v, r);
    r = parse_int32("2147483648", &v);     printf("'%s' => %d, %d\n", "2147483648", v, r);
    r = parse_int32("-2147483649", &v);    printf("'%s' => %d, %d\n", "-2147483649", v, r);
    r = parse_int32("", &v);               printf("'%s' => %d, %d\n", "", v, r);
    r = parse_int32("  ", &v);             printf("'%s' => %d, %d\n", "  ", v, r);
    r = parse_int32("123abc", &v);         printf("'%s' => %d, %d\n", "123abc", v, r);
    r = parse_int32("+42", &v);            printf("'%s' => %d, %d\n", "+42", v, r);
    r = parse_int32("0", &v);              printf("'%s' => %d, %d\n", "0", v, r);
    r = parse_int32("-0", &v);             printf("'%s' => %d, %d\n", "-0", v, r);
    r = parse_int32("-00042", &v);         printf("'%s' => %d, %d\n", "-00042", v, r);
    r = parse_int32("  +0  ", &v);         printf("'%s' => %d, %d\n", "  +0  ", v, r);
    r = parse_int32("-", &v);              printf("'%s' => %d, %d\n", "-", v, r);
    r = parse_int32("+", &v);              printf("'%s' => %d, %d\n", "+", v, r);
    r = parse_int32("  -  ", &v);          printf("'%s' => %d, %d\n", "  -  ", v, r);
    return 0;
}
