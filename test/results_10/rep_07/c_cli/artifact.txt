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
    int sign = 1;
    if (*s == '-') {
        sign = -1;
        s++;
    } else if (*s == '+') {
        s++;
    }

    if (*s == '\0')
        return 0;

    /* parse digits, accumulating as negative to handle INT32_MIN safely */
    int32_t acc = 0;

    while (isdigit((unsigned char)*s)) {
        int digit = *s - '0';

        if (sign == 1) {
            if (acc > INT32_MAX / 10 || (acc == INT32_MAX / 10 && digit > INT32_MAX % 10))
                return 0;
            acc = acc * 10 + digit;
        } else {
            if (acc < INT32_MIN / 10 || (acc == INT32_MIN / 10 && digit > -(INT32_MIN % 10)))
                return 0;
            acc = acc * 10 - digit;
        }

        s++;
    }

    /* skip trailing whitespace */
    while (isspace((unsigned char)*s))
        s++;

    if (*s != '\0')
        return 0; /* extra non-whitespace characters */

    *out = acc;
    return 1;
}
