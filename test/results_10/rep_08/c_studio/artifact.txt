#include <stdint.h>
#include <ctype.h>

int parse_int32(const char *s, int32_t *out) {
    if (!s || !out)
        return 0;

    /* Skip leading whitespace */
    while (*s && isspace((unsigned char)*s))
        s++;

    /* Reject empty string */
    if (!*s)
        return 0;

    /* Parse optional sign */
    int negative = 0;
    if (*s == '-') {
        negative = 1;
        s++;
    } else if (*s == '+') {
        s++;
    }

    /* Must have at least one digit after sign */
    if (!*s || !isdigit((unsigned char)*s))
        return 0;

    /* Parse digits, checking overflow/underflow at each step */
    int32_t result = 0;
    while (isdigit((unsigned char)*s)) {
        int digit = *s - '0';

        if (negative) {
            /* INT32_MIN = -2147483648; result is <= 0 */
            if (result < -214748364 ||
                (result == -214748364 && digit > 8))
                return 0;
        } else {
            /* INT32_MAX = 2147483647; result is >= 0 */
            if (result > 214748364 ||
                (result == 214748364 && digit > 7))
                return 0;
        }

        result = result * 10 + (negative ? -digit : digit);
        s++;
    }

    /* Skip trailing whitespace */
    while (*s && isspace((unsigned char)*s))
        s++;

    /* Reject extra non-whitespace characters */
    if (*s)
        return 0;

    *out = result;
    return 1;
}
