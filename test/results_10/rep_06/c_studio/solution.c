#include <stdint.h>
#include <ctype.h>

int parse_int32(const char *s, int32_t *out)
{
    if (!s || !out)
        return 0;

    const char *p = s;

    /* skip leading whitespace */
    while (*p && isspace((unsigned char)*p))
        p++;

    if (!*p)
        return 0;

    /* optional sign */
    int neg = 0;
    if (*p == '-') {
        neg = 1;
        p++;
    } else if (*p == '+') {
        p++;
    }

    if (!*p || !isdigit((unsigned char)*p))
        return 0;

    /* Use uint32_t for accumulation to avoid signed overflow UB.
       INT32_MAX = 2147483647, INT32_MIN = -2147483648. */
    uint32_t acc = 0;
    const uint32_t hi = neg ? 214748364U : 214748364U;  /* INT32_MAX / 10 */
    const uint32_t lo = neg ? 8U : 7U;                  /* abs(INT32_MIN % 10) / abs(INT32_MAX % 10) */

    while (isdigit((unsigned char)*p)) {
        uint32_t digit = (uint32_t)(*p - '0');

        /* skip leading zeros */
        if (acc == 0 && digit == 0) {
            p++;
            continue;
        }

        if (acc > hi || (acc == hi && digit > lo))
            return 0;

        acc = acc * 10 + digit;
        p++;
    }

    /* skip trailing whitespace */
    while (*p && isspace((unsigned char)*p))
        p++;

    if (*p)
        return 0;

    /* Convert to int32_t, applying sign.
       acc fits in int32_t range because hi/lo guard against overflow. */
    int32_t val = (int32_t)acc;
    if (neg)
        val = -val;

    *out = val;
    return 1;
}
