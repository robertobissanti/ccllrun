#include <stdint.h>
#include <ctype.h>

int parse_int32(const char *s, int32_t *out)
{
    if (!s || !out)
        return 0;

    while (*s && *s <= ' ')
        s++;
    if (!*s)
        return 0;

    int neg = 0;
    if (*s == '-') {
        neg = 1;
        s++;
    } else if (*s == '+') {
        s++;
    }

    if (!*s || !isdigit((unsigned char)*s))
        return 0;

    int64_t acc = 0;
    while (isdigit((unsigned char)*s)) {
        acc = acc * 10 + (*s++ - '0');
    }

    while (*s && *s <= ' ')
        s++;
    if (*s != '\0')
        return 0;

    if (neg)
        acc = -acc;

    if (acc < (int64_t)INT32_MIN || acc > (int64_t)INT32_MAX)
        return 0;

    *out = (int32_t)acc;
    return 1;
}
