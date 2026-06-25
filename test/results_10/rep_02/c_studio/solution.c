#include <stdint.h>
#include <ctype.h>

int parse_int32(const char *s, int32_t *out) {
    if (!s || !out)
        return 0;

    while (isspace((unsigned char)*s))
        s++;

    if (*s == '\0')
        return 0;

    int neg = 0;
    if (*s == '-') {
        neg = 1;
        s++;
    } else if (*s == '+') {
        s++;
    }

    if (*s == '\0')
        return 0;

    int32_t val = 0;

    while (*s >= '0' && *s <= '9') {
        int digit = *s - '0';
        if (neg) {
            if (val < -INT32_MAX / 10 ||
               (val == -INT32_MAX / 10 && digit > -INT32_MAX % 10))
                return 0;
            val = val * 10 - digit;
        } else {
            if (val > INT32_MAX / 10 ||
               (val == INT32_MAX / 10 && digit > INT32_MAX % 10))
                return 0;
            val = val * 10 + digit;
        }
        s++;
    }

    while (isspace((unsigned char)*s))
        s++;

    if (*s != '\0')
        return 0;

    *out = val;
    return 1;
}
