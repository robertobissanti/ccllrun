#include <stdint.h>
#include <ctype.h>

int parse_int32(const char *s, int32_t *out)
{
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

    int64_t val = 0;

    while (isdigit((unsigned char)*s)) {
        val = val * 10 + (*s - '0');
        s++;
    }

    while (isspace((unsigned char)*s))
        s++;

    if (*s != '\0')
        return 0;

    if (neg)
        val = -val;

    if (val < INT32_MIN || val > INT32_MAX)
        return 0;

    *out = (int32_t)val;
    return 1;
}
