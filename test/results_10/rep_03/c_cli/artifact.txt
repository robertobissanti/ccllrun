#include <stdint.h>
#include <stddef.h>
#include <ctype.h>

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

    /* parse digits as unsigned to avoid signed overflow UB */
    uint32_t acc = 0;
    uint32_t const hi = (uint32_t)INT32_MAX / 10;
    uint32_t const lo = (uint32_t)INT32_MAX % 10;

    while (*s != '\0') {
        /* reject any non-digit (trailing whitespace, garbage, etc.) */
        if (!isdigit((unsigned char)*s))
            return 0;

        int digit = *s - '0';

        /* unsigned overflow check */
        if (acc > hi || (acc == hi && digit > lo)) {
            if (sign == 1)
                return 0;
            /* negative: INT32_MIN = -(INT32_MAX+1), so we allow digit 1
               when acc == hi (i.e. 214748364), giving 2147483648 */
            if (acc > hi || (acc == hi && digit > lo + 1))
                return 0;
        }

        acc = acc * 10 + digit;
        s++;
    }

    *out = sign * (int32_t)acc;
    return 1;
}
