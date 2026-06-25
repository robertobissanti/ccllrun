#include <stdint.h>

int parse_int32(const char *s, int32_t *out)
{
    if (!s || !out)
        return 0;

    const char *p = s;

    /* skip leading spaces */
    while (*p == ' ')
        p++;

    /* reject empty or spaces-only string */
    if (*p == '\0')
        return 0;

    /* optional sign */
    int sign = 1;
    if (*p == '-') {
        sign = -1;
        p++;
    } else if (*p == '+') {
        p++;
    }

    /* must have at least one digit */
    if (*p < '0' || *p > '9')
        return 0;

    /* parse digits using int64_t to avoid overflow during accumulation */
    int64_t result = 0;
    while (*p >= '0' && *p <= '9') {
        int digit = *p - '0';
        result = result * 10 + digit;
        p++;
    }

    /* skip trailing spaces */
    while (*p == ' ')
        p++;

    /* reject extra characters */
    if (*p != '\0')
        return 0;

    /* check range after full parse */
    int64_t val = sign * result;
    if (val < -2147483648LL || val > 2147483647LL)
        return 0;

    *out = (int32_t)val;
    return 1;
}
