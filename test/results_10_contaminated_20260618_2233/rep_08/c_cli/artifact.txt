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
    int negative = 0;
    if (*s == '-') {
        negative = 1;
        s++;
    } else if (*s == '+') {
        s++;
    }

    if (*s == '\0' || !isdigit((unsigned char)*s))
        return 0;

    /*
     * Parse digits with overflow/underflow guard.
     *
     * We keep acc positive throughout and negate at the end.
     *
     *   limit = INT32_MAX / 10  = 214748364
     *   bound = INT32_MAX % 10  = 7
     *
     * For negative numbers the last digit can be 8 (INT32_MIN = -2147483648),
     * so we use bound + 1 when negative.
     */
    const int32_t limit = INT32_MAX / 10;
    const int32_t bound = INT32_MAX % 10 + (negative ? 1 : 0);
    int32_t acc = 0;

    while (isdigit((unsigned char)*s)) {
        int digit = *s - '0';
        if (acc > limit || (acc == limit && digit > bound))
            return 0;
        acc = acc * 10 + digit;
        s++;
    }

    /* skip trailing whitespace */
    while (isspace((unsigned char)*s))
        s++;

    if (*s != '\0')
        return 0;

    if (negative)
        acc = -acc;

    *out = acc;
    return 1;
}
