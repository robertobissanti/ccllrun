#include <stdint.h>
#include <ctype.h>

int parse_int32(const char *s, int32_t *out) {
    if (s == NULL || out == NULL)
        return 0;

    /* skip leading whitespace */
    while (isspace((unsigned char)*s))
        s++;

    if (*s == '\0')
        return 0;

    /* detect sign */
    int sign = 1;
    if (*s == '-') {
        sign = -1;
        s++;
    } else if (*s == '+') {
        s++;
    }

    if (*s == '\0')
        return 0;

    /* parse digits */
    int32_t acc = 0;
    int32_t limit = (sign == 1) ? INT32_MAX : -(INT32_MAX + 1);

    while (isdigit((unsigned char)*s)) {
        int digit = *s - '0';
        /* check overflow before multiplying and adding */
        if (acc > limit / 10 || (acc == limit / 10 && digit > limit % 10))
            return 0;
        acc = acc * 10 + digit;
        s++;
    }

    /* reject trailing non-whitespace */
    while (*s != '\0') {
        if (!isspace((unsigned char)*s))
            return 0;
        s++;
    }

    *out = sign * acc;
    return 1;
}
