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
    if (*s == '+') {
        s++;
    } else if (*s == '-') {
        sign = -1;
        s++;
    }

    if (*s == '\0' || !isdigit((unsigned char)*s))
        return 0;

    /* parse digits */
    int32_t acc = 0;
    int32_t const hi = sign > 0 ? INT32_MAX : INT32_MIN;
    int32_t const lo = hi / 10;
    int32_t const rem = hi % 10;

    while (isdigit((unsigned char)*s)) {
        int digit = *s - '0';

        /* overflow / underflow check before multiply + add */
        if (acc > lo || (acc == lo && digit > rem))
            return 0;

        acc = acc * 10 + digit;
        s++;
    }

    /* reject trailing non-whitespace */
    while (isspace((unsigned char)*s))
        s++;

    if (*s != '\0')
        return 0;

    *out = sign > 0 ? acc : -acc;
    return 1;
}
