#include <stdint.h>
#include <stdio.h>
#include <limits.h>

int parse_int32(const char *s, int32_t *out);

int main(void) {
    struct { const char *s; int ok; int32_t value; } cases[] = {
        {"0",1,0}, {"  -42  ",1,-42}, {"+2147483647",1,INT32_MAX},
        {"-2147483648",1,INT32_MIN}, {"2147483648",0,0},
        {"-2147483649",0,0}, {"",0,0}, {"   ",0,0},
        {"12x",0,0}, {"+",0,0}, {"--1",0,0}, {"1 2",0,0}
    };
    for (unsigned i = 0; i < sizeof cases / sizeof cases[0]; ++i) {
        int32_t out = 1234567;
        int ok = parse_int32(cases[i].s, &out);
        if (ok != cases[i].ok || (ok && out != cases[i].value) || (!ok && out != 1234567)) {
            fprintf(stderr, "FAIL case %u input [%s] ok=%d out=%d\n", i, cases[i].s, ok, out);
            return 1;
        }
    }
    puts("PASS");
    return 0;
}
