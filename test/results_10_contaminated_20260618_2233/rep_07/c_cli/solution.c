#include <stdint.h>
#include <ctype.h>

int parse_int32(const char *s, int32_t *out)
{
    if (!s || !out)
        return 0;

    /* skip leading whitespace */
    while (isspace((unsigned char)*s))
        s++;

    if (*s == '\0')
        return 0;

    /* detect sign */
    int neg = 0;
    if (*s == '-') {
        neg = 1;
        s++;
    } else if (*s == '+') {
        s++;
    }

    if (*s == '\0')
        return 0;

    /* parse digits, checking overflow/underflow */
    int32_t acc = 0;
    int32_t lim = 0x7fffffff;

    while (isdigit((unsigned char)*s)) {
        int digit = *s - '0';

        /* For negative numbers, INT32_MIN magnitude = INT32_MAX+1, so remainder is one higher. */
        int32_t threshold = lim / 10;
        int32_t remainder = lim % 10 + neg;

        if (acc > threshold || (acc == threshold && digit > remainder))
            return 0;

        acc = acc * 10 + digit;
        s++;
    }

    /* skip trailing whitespace */
    while (isspace((unsigned char)*s))
        s++;

    if (*s != '\0')
        return 0; /* extra non-whitespace characters */

    if (neg)
        acc = -acc;

    *out = acc;
    return 1;
}
