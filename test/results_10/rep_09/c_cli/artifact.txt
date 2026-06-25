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

    /* optional sign */
    int sign = 1;
    if (*s == '+') {
        s++;
    } else if (*s == '-') {
        sign = -1;
        s++;
    }

    if (*s == '\0')
        return 0;

    /*
     * Parse digits into an unsigned accumulator to avoid undefined
     * behaviour on signed overflow.  INT32_MAX = 214748364,
     * |INT32_MIN| = 2147483648.
     */
    uint32_t acc = 0;
    uint32_t const max_hi = 214748364u;   /* INT32_MAX / 10 == |INT32_MIN| / 10 */
    int32_t  const max_lo = 4;            /* INT32_MAX % 10 */
    int32_t  const min_lo = 8;            /* |INT32_MIN| % 10 */

    while (*s != '\0') {
        if (isspace((unsigned char)*s)) {
            /* trailing whitespace: only OK if the rest is whitespace or EOS */
            const char *p = s + 1;
            while (isspace((unsigned char)*p))
                p++;
            if (*p != '\0')
                return 0;
            break;
        }

        if (*s < '0' || *s > '9')
            return 0;

        int digit = *s - '0';

        /* overflow / underflow guard */
        if (acc > max_hi ||
            (acc == max_hi &&
             (sign > 0 ? digit > max_lo : digit > min_lo)))
            return 0;

        acc = acc * 10u + (uint32_t)digit;
        s++;
    }

    if (sign < 0)
        *out = -(int32_t)acc;
    else
        *out = (int32_t)acc;

    return 1;
}
