#include <stdint.h>
#include <ctype.h>
#include <stddef.h>

int parse_int32(const char *s, int32_t *out)
{
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

    while (isdigit((unsigned char)*s)) {
        int digit = *s - '0';

        if (sign == 1) {
            /* acc * 10 + digit <= INT32_MAX */
            if (acc > (INT32_MAX - digit) / 10)
                return 0;
            acc = acc * 10 + digit;
        } else {
            /* acc * 10 + digit <= 2147483648 (one more than INT32_MAX) */
            if (acc > 214748364 ||
               (acc == 214748364 && digit > 8))
                return 0;
            acc = acc * 10 + digit;
        }

        s++;
    }

    if (sign == -1)
        acc = -acc;

    /* reject trailing non-whitespace */
    while (isspace((unsigned char)*s))
        s++;
    if (*s != '\0')
        return 0;

    *out = acc;
    return 1;
}
