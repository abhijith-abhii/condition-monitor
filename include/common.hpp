#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>
namespace core {
inline uint32_t elapsed(uint32_t now, uint32_t then) {
    return now - then;
}
inline uint32_t crc32(const void *data, size_t n) {
    auto p = static_cast<const uint8_t *>(data);
    uint32_t c = 0xffffffffu;
    for (size_t i = 0; i < n; ++i) {
        c ^= p[i];
        for (int b = 0; b < 8; ++b)
            c = (c >> 1) ^ (0xedb88320u & (0u - (c & 1u)));
    }
    return ~c;
}
template <typename T, size_t N> struct Ring {
    T data[N]{};
    uint32_t head = 0, count = 0, drops = 0;
    bool push(const T &v) {
        if (count == N) {
            ++drops;
            return false;
        }
        data[(head + count) % N] = v;
        ++count;
        return true;
    }
    const T *front() const {
        return count ? &data[head] : nullptr;
    }
    bool pop() {
        if (!count)
            return false;
        head = (head + 1) % N;
        --count;
        return true;
    }
    bool valid() const {
        return head < N && count <= N;
    }
};
// Fixed capacity; an oversized line is discarded through its next newline.
template <size_t N> struct Line {
    char data[N]{};
    size_t used = 0;
    bool overflow = false;
    bool feed(char c) {
        if (c == '\r')
            return false;
        if (c == '\n') {
            if (overflow) {
                reset();
                return false;
            }
            data[used] = 0;
            used = 0;
            return true;
        }
        if (static_cast<unsigned char>(c) < 32 || static_cast<unsigned char>(c) > 126) {
            overflow = true;
        }
        if (!overflow) {
            if (used + 1 < N)
                data[used++] = c;
            else
                overflow = true;
        }
        return false;
    }
    void reset() {
        used = 0;
        overflow = false;
        data[0] = 0;
    }
};
inline bool parse_u32(const char *s, uint32_t &out) {
    if (!s || !*s)
        return false;
    uint32_t v = 0;
    for (; *s; ++s) {
        if (*s < '0' || *s > '9')
            return false;
        unsigned d = *s - '0';
        if (v > (UINT32_MAX - d) / 10)
            return false;
        v = v * 10 + d;
    }
    out = v;
    return true;
}
} // namespace core
