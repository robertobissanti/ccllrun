#include <stdint.h>
#include <ctype.h>

int parse_int32(const char *s, int32_t *out) {
    if (!s || !out)
        return 0;

    const char *p = s;

    /* skip leading whitespace */
    while (*p && isspace((unsigned char)*p))
        p++;

    /* empty string */
    if (*p == '\0')
        return 0;

    /* optional sign */
    int neg = 0;
    if (*p == '-') {
        neg = 1;
        p++;
    } else if (*p == '+') {
        p++;
    }

    /* must have at least one digit */
    if (*p < '0' || *p > '9')
        return 0;

    /*
     * Accumulate magnitude as uint32_t to avoid signed overflow UB.
     * limit is the positive magnitude of the bound:
     *   INT32_MAX  for positive numbers
     *   INT32_MIN+1 for negative numbers (2147483648)
     */
    uint32_t limit = (uint32_t)INT32_MAX + neg;
    uint32_t result = 0;

    while (*p >= '0' && *p <= '9') {
        uint32_t digit = (uint32_t)(*p - '0');

        /* check: result * 10 + digit > limit  <=>  result > (limit - digit) / 10 */
        if (result > (limit - digit) / 10)
            return 0;

        result = result * 10 + digit;
        p++;
    }

    /* no extra characters allowed (only trailing whitespace) */
    while (*p && isspace((unsigned char)*p))
        p++;
    if (*p != '\0')
        return 0;

    /* apply sign — cast is safe because result <= limit <= INT32_MIN+1 */
    *out = (neg) ? -(int32_t)result : (int32_t)result;
    return 1;
}
