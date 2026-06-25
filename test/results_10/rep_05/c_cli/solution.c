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

    /* parse digits using unsigned accumulator */
    uint32_t acc = 0;
    uint32_t const hi = 214748364u;   /* INT32_MAX / 10 */

    while (*s != '\0') {
        if (!isdigit((unsigned char)*s))
            return 0;

        uint32_t digit = (uint32_t)(*s - '0');

        /* overflow guard: acc * 10 + digit > INT32_MAX */
        if (acc > hi || (acc == hi && digit > 7))
            return 0;

        acc = acc * 10 + digit;
        s++;
    }

    /* skip trailing whitespace */
    while (isspace((unsigned char)*s))
        s++;

    if (*s != '\0')
        return 0;

    /* apply sign; reject if magnitude exceeds INT32_MIN */
    if (sign < 0 && acc > 2147483648u)
        return 0;

    *out = sign * (int32_t)acc;
    return 1;
}
