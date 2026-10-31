// Original contract fixture, not a production hash generator or benchmark.
#include <array>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <memory>
#include <string>
#include <string_view>

constexpr std::array<std::string_view, 4> keys{"GET", "PUT", "POST", "DELETE"};
int oracle(std::string_view s) {
  for (int i = 0; i < 4; ++i) if (s == keys[i]) return i;
  return -1;
}
int lookup(std::string_view s) {
  if (s.size() < 3 || s.size() > 6) return -1;
  const unsigned char first = static_cast<unsigned char>(s[0]);
  const auto slot = (s.size() + (first == 'P' ? 1u : 0u)) & 7u;
  constexpr std::array<int, 8> slots{-1, -1, -1, 0, 1, 2, 3, -1};
  const int i = slots[slot];
  if (i < 0) return -1;
#ifdef MUTANT_SLOT_ONLY
  return i;
#endif
  const auto key = keys[i];
#ifndef MUTANT_PREFIX
  if (s.size() != key.size()) return -1;
#endif
  std::array<char, 16> input{};
  std::array<char, 16> expected{};
  std::memcpy(input.data(), s.data(), s.size());
  std::memcpy(expected.data(), key.data(), key.size());
#ifdef MUTANT_PREFIX
  return std::memcmp(input.data(), expected.data(), 1) == 0 ? i : -1;
#else
  return input == expected ? i : -1;
#endif
}

volatile unsigned sink = 0;
__attribute__((noinline)) void invalid_wide_read(const char* p) {
  // Intentionally invalid fixture: same-page is not same-allocation.
  std::array<unsigned char, 16> block{};
  std::memcpy(block.data(), p, block.size());
  for (auto x : block) sink = sink + x;
}
int main(int argc, char**) {
  if (argc > 1) {
    auto p = std::make_unique<char[]>(3);
    std::memcpy(p.get(), "GET", 3);
    const auto address = reinterpret_cast<std::uintptr_t>(p.get());
    if ((address & 4095u) > 4080u) return 77;
    invalid_wide_read(p.get());
    return 0;
  }
  std::size_t count = 0;
  auto check = [&](std::string_view s) {
    if (s.size() > 64) std::exit(2); // This bounded fixture generates only short tokens.
    // Exact-size independent allocation; no hidden std::string capacity.
    auto p = std::make_unique<char[]>(s.size());
    if (!s.empty()) std::memcpy(p.get(), s.data(), s.size());
    const std::string_view copy(p.get(), s.size());
    ++count;
    if (lookup(copy) != oracle(s)) {
      std::cerr << "oracle mismatch: length " << s.size() << '\n';
      std::exit(1);
    }
  };
  check({});
  for (auto key : keys) {
    check(key);
    for (std::size_t i = 0; i < key.size(); ++i) {
      for (unsigned c = 0; c < 256; ++c) {
        std::string s(key); s[i] = static_cast<char>(c); check(s);
      }
      check(key.substr(0, i));
    }
    for (unsigned c = 0; c < 256; ++c) {
      std::string s(key); s.push_back(static_cast<char>(c)); check(s);
    }
  }
  for (auto s : {"PATCH", "GARBAG", "DELET", "POSTER", "GETGET", ""}) check(s);
  std::cout << "passed " << count << " differential cases\n";
}
