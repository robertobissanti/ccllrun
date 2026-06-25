#include <stdint.h>
#include <ctype.h>

int parse_int32(const char *s, int32_t *out)
{
    if (s == NULL || out == NULL)
        return 0;

    /* Skip leading whitespace */
    while (isspace((unsigned char)*s))
        s++;

    if (*s == '\0')
        return 0;

    /* Detect sign */
    int negative = 0;
    if (*s == '-') {
        negative = 1;
        s++;
    } else if (*s == '+') {
        s++;
    }

    if (*s == '\0')
        return 0;

    /* Parse digits */
    int32_t abs_max = 2147483647;
    int32_t acc = 0;

    while (isdigit((unsigned char)*s)) {
        int digit = *s - '0';

        /* Check overflow before multiplying and adding */
        if (acc > abs_max / 10 || (acc == abs_max / 10 && digit > abs_max % 10 + negative)) {
            return 0;
        }

        acc = acc * 10 + digit;
        s++;
    }

    /* Skip trailing whitespace */
    while (isspace((unsigned char)*s))
        s++;

    if (*s != '\0')
        return 0; /* trailing non-whitespace */

    if (negative)
        acc = -acc;

    *out = acc;
    return 1;
}
