#include <stdint.h>
#include <ctype.h>

int parse_int32(const char *s, int32_t *out)
{
    if (!s || !out)
        return 0;

    /* skip leading whitespace */
    while (isspace((unsigned char)*s))
        s++;

    if (!*s)
        return 0;

    int sign = 1;
    if (*s == '-') {
        sign = -1;
        s++;
    } else if (*s == '+') {
        s++;
    }

    if (!*s)
        return 0;

    /*
     * Accumulate as unsigned to avoid undefined behaviour on signed
     * overflow.  Compare against the appropriate absolute limit.
     * INT32_MAX  =  2147483647
     * |INT32_MIN| = 2147483648  (one more than INT32_MAX)
     */
    uint32_t acc = 0;
    uint32_t hi  = 214748364u;   /* abs(limit) / 10 */
    int        lo  = 7;           /* abs(limit) % 10  (default for INT32_MAX) */

    if (sign < 0)
        lo = 8;   /* INT32_MIN = -2147483648 */

    while (isdigit((unsigned char)*s)) {
        int digit = *s - '0';

        if (acc > hi || (acc == hi && digit > lo))
            return 0;

        acc = acc * 10 + digit;
        s++;
    }

    /* skip trailing whitespace */
    while (isspace((unsigned char)*s))
        s++;

    if (*s != '\0')
        return 0;

    *out = sign * (int32_t)acc;
    return 1;
}
