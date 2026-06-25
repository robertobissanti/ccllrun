#include <stdint.h>
#include <ctype.h>

int parse_int32(const char *s, int32_t *out) {
    if (!s || !out)
        return 0;

    const char *p = s;

    while (*p && isspace((unsigned char)*p))
        p++;

    if (!*p)
        return 0;

    int neg = 0;
    if (*p == '-') {
        neg = 1;
        p++;
    } else if (*p == '+') {
        p++;
    }

    if (!*p || !isdigit((unsigned char)*p))
        return 0;

    int32_t limit = 214748364;
    int32_t rem   = 7;
    int32_t acc   = 0;
    int d         = 0;

    while (*p && isdigit((unsigned char)*p)) {
        d = *p - '0';
        if (acc > limit || (acc == limit && d > rem))
            return 0;
        acc = acc * 10 + d;
        p++;
    }

    while (*p && isspace((unsigned char)*p))
        p++;

    if (*p)
        return 0;

    if (neg) {
        int32_t min_rem = 8;
        if (acc > limit || (acc == limit && d > min_rem))
            return 0;
        *out = -(int32_t)acc;
    } else {
        *out = (int32_t)acc;
    }

    return 1;
}
