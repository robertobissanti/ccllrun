#include <stdint.h>
#include <ctype.h>

int parse_int32(const char *s, int32_t *out)
{
    if (!s || !out)
        return 0;

    /* Skip leading whitespace */
    while (*s && isspace((unsigned char)*s))
        s++;

    /* Reject empty string */
    if (*s == '\0')
        return 0;

    /* Optional sign */
    int negative = 0;
    if (*s == '-') {
        negative = 1;
        s++;
    } else if (*s == '+') {
        s++;
    }

    /* Reject if no digits follow sign */
    if (*s == '\0' || !isdigit((unsigned char)*s))
        return 0;

    /*
     * Parse digits with overflow/underflow guards.
     *
     * INT32_MAX =  2147483647  (max_prefix = 214748364, max_digit = 7)
     * INT32_MIN = -2147483648  (min_prefix = -214748364, min_digit = 8)
     *
     * For negative: result < -214748364  OR  (result == -214748364 && digit > 8)
     * For positive: result >  214748364  OR  (result ==  214748364 && digit > 7)
     */
    int32_t result = 0;
    const int32_t max_prefix =  214748364;
    const int32_t min_prefix = -214748364;

    while (isdigit((unsigned char)*s)) {
        int digit = *s - '0';

        if (negative) {
            if (result < min_prefix ||
                (result == min_prefix && digit > 8))
                return 0;
        } else {
            if (result > max_prefix ||
                (result == max_prefix && digit > 7))
                return 0;
        }

        result = result * 10 - digit;
        s++;
    }

    /* Skip trailing whitespace */
    while (*s && isspace((unsigned char)*s))
        s++;

    /* Reject trailing non-whitespace */
    if (*s != '\0')
        return 0;

    *out = result;
    return 1;
}
