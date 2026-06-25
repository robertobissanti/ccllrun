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

    /*
     * Accumulate in negative space.  This avoids signed overflow UB
     * because INT32_MIN is representable but -INT32_MAX is not.
     * neg_limit is the most-negative value acc may reach.
     */
    int32_t acc = 0;
    int32_t const neg_limit = sign > 0 ? -INT32_MAX : INT32_MIN;

    while (isdigit((unsigned char)*s)) {
        int digit = *s - '0';

        /*
         * Check: would acc*10 - digit < neg_limit?
         *   acc < neg_limit/10  =>  definitely too small
         *   acc == neg_limit/10 =>  need digit > |neg_limit%10|
         *   acc > neg_limit/10  =>  safe
         */
        int32_t const threshold = neg_limit / 10;
        int32_t const max_digit = neg_limit % 10;  /* negative or zero */

        if (acc < threshold || (acc == threshold && digit > -max_digit))
            return 0;

        acc = acc * 10 - digit;
        s++;
    }

    /* skip trailing whitespace */
    while (isspace((unsigned char)*s))
        s++;

    if (*s != '\0')
        return 0;  /* extra non-whitespace characters */

    *out = sign > 0 ? -acc : acc;
    return 1;
}
