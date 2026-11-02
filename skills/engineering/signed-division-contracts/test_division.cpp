// Original isolated experiment: no fetched source code is executed.
#include <bit>
#include <cstdint>
#include <limits>
#include <iostream>
#include <stdexcept>
#include <array>
struct Plan { int shift; std::int64_t multiplier; };
constexpr Plan plan(std::int32_t divisor) {
  if (divisor <= 0 || std::has_single_bit(static_cast<std::uint32_t>(divisor)))
    throw std::invalid_argument("positive non-power-of-two divisor required");
  const int shift = 31 + std::bit_width(static_cast<std::uint32_t>(divisor)-1u);
  const std::uint64_t scale = std::uint64_t{1} << shift;
  const auto u = static_cast<std::uint32_t>(divisor);
  const std::uint64_t multiplier = scale/u + (scale%u != 0);
  if (multiplier >= (std::uint64_t{1} << 32)) throw std::logic_error("product bound");
  return {shift, static_cast<std::int64_t>(multiplier)};
}
constexpr std::int32_t evaluate(std::int32_t input, Plan p) {
  const std::int64_t product = static_cast<std::int64_t>(input) * p.multiplier;
  const std::int64_t floor_quotient = product >> p.shift;
  return static_cast<std::int32_t>(floor_quotient + (input < 0));
}
template<std::int32_t D>
  requires (D > 0 && !std::has_single_bit(static_cast<std::uint32_t>(D)))
std::int32_t constant_divide(std::int32_t input) {
  constexpr auto p=plan(D);
  return evaluate(input,p);
}
extern "C" std::int32_t native7(std::int32_t x) { return x/7; }
extern "C" std::int32_t widened7(std::int32_t x) { return constant_divide<7>(x); }
extern "C" std::int32_t native1000(std::int32_t x) { return x/1000; }
extern "C" std::int32_t widened1000(std::int32_t x) { return constant_divide<1000>(x); }
#ifndef ASSEMBLY_ONLY
std::uint64_t cases=0;
void check(std::int64_t x, std::int32_t d, Plan p) {
  if(x<std::numeric_limits<std::int32_t>::min() || x>std::numeric_limits<std::int32_t>::max()) return;
  auto input=static_cast<std::int32_t>(x);
  auto expected=static_cast<std::int64_t>(input)/static_cast<std::int64_t>(d);
  if(evaluate(input,p)!=expected) throw std::runtime_error("oracle mismatch");
  if (d == 7 && native7(input) != widened7(input)) throw std::runtime_error("template7 mismatch");
  if (d == 1000 && native1000(input) != widened1000(input)) throw std::runtime_error("template1000 mismatch");
  ++cases;
}
int main() {
  std::uint64_t state=0x719a478b5566ULL;
  auto next=[&] {state=state*6364136223846793005ULL+1442695040888963407ULL;return static_cast<std::uint32_t>(state>>32);};
  std::uint64_t divisors=0;
  auto exercise=[&](std::int32_t d) {
    if(d<=0 || std::has_single_bit(static_cast<std::uint32_t>(d)))return;
    const auto p=plan(d); ++divisors;
    for(std::int64_t x:std::array<std::int64_t,9>{INT32_MIN,INT32_MIN+1,-1000,-1,0,1,1000,INT32_MAX-1,INT32_MAX})check(x,d,p);
    // Quotient boundaries, including endpoints. All preparation uses 64 bits.
    for(std::int64_t q:std::array<std::int64_t,9>{INT32_MIN/static_cast<std::int64_t>(d),-100,-2,-1,0,1,2,100,INT32_MAX/static_cast<std::int64_t>(d)})
      for(int delta=-2;delta<=2;++delta)check(q*d+delta,d,p);
    for(int i=0;i<256;++i)check(static_cast<std::int64_t>(next())-(std::int64_t{1}<<31),d,p);
  };
  for(int d=3;d<=16384;++d)exercise(d);
  for(int k=2;k<31;++k)for(int delta=-3;delta<=3;++delta)exercise((std::int32_t{1}<<k)+delta);
  exercise(INT32_MAX);exercise(INT32_MAX-1);exercise(1000);
  for(int i=0;i<16384;++i)exercise(static_cast<std::int32_t>(next()&0x7fffffff));
  // Small exhaustive numerator domain with all signed 16-bit values, varied divisors.
  for(int d: {3,7,60,365,1000,65535,1073741825,INT32_MAX})
    for(std::int64_t x=-32768;x<=32767;++x)check(x,d,plan(d));
  int rejected=0;
  for(int d: {INT32_MIN,-7,-1,0,1,2,4,8,1024,1073741824})try{(void)plan(d);}catch(const std::invalid_argument&){++rejected;}
  if(rejected!=10)throw std::runtime_error("guard failed");
  const auto p=plan(7);
  const auto missing_correction=(std::int64_t{-7}*p.multiplier)>>p.shift;
  if(missing_correction==-1)throw std::runtime_error("mutant escaped");
  // Using truncating division instead of arithmetic right shift, then correcting,
  // double-adjusts the negative result.
  const auto wrong_rounding=(std::int64_t{-7}*p.multiplier)/(std::int64_t{1}<<p.shift)+1;
  if(wrong_rounding==-1)throw std::runtime_error("rounding mutant escaped");
  std::cout<<"PASS cases="<<cases<<" divisor_trials="<<divisors<<" rejected="<<rejected<<" mutants=2\n";
}
#endif
