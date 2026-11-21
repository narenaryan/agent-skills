"""Original capability-lifetime model. No crypto, credentials, cloud calls or erasure.

The model intentionally assumes a retained handle works independently of its provider.
It illustrates why a provider-denial-only closure rule is insufficient, not an SDK clone.
"""
from dataclasses import dataclass, field, replace
import unittest


class Denied(Exception):
    pass


@dataclass
class Provider:
    allowed: bool = True
    calls: int = 0

    def acquire(self):
        self.calls += 1
        if not self.allowed:
            raise Denied("acquisition blocked")
        return object()  # Opaque capability marker, not key material.


@dataclass
class Holder:
    provider: Provider
    generation: str
    cached: object = None
    expires_at: int = 0
    handles: dict = field(default_factory=dict)
    next_handle: int = 0

    def begin(self, now, age=10):
        if self.cached is None or now >= self.expires_at:
            self.cached = None
            self.cached = self.provider.acquire()
            self.expires_at = now + age
        self.next_handle += 1
        self.handles[self.next_handle] = self.cached
        return self.next_handle

    def use(self, handle):
        return handle in self.handles

    def finish(self, handle):
        self.handles.pop(handle, None)

    def retire_cache(self):
        self.cached = None  # Does not revoke handles already returned.


@dataclass(frozen=True)
class Observation:
    generation: str
    acquisition_denied: bool
    cache_retired: bool
    active_handles: int
    permitted_control: bool
    fresh: bool = True
    key_version: str = "key-v1"


def can_close_continued_use(expected_generations, observations, key_version="key-v1"):
    """Conservative fixture oracle over trusted synthetic observations, not an adapter.

    Production evidence must establish scope, freshness, identity, no alternate holder,
    and a stable retirement boundary. This function cannot authenticate those facts.
    """
    if not expected_generations or not key_version or set(expected_generations) != set(observations):
        return False
    return all(
        o.generation == expected_generations[asset]
        and o.key_version == key_version
        and o.fresh
        and o.acquisition_denied
        and o.cache_retired
        and o.active_handles == 0
        and o.permitted_control
        for asset, o in observations.items()
    )


class KeyRetentionTests(unittest.TestCase):
    def setUp(self):
        self.provider = Provider()
        self.holder = Holder(self.provider, "g1")

    def test_provider_denial_does_not_stop_existing_handle(self):
        h = self.holder.begin(0)
        self.provider.allowed = False
        with self.assertRaises(Denied):
            self.provider.acquire()
        self.assertTrue(self.holder.use(h))

    def test_warm_cache_avoids_new_provider_request(self):
        self.holder.finish(self.holder.begin(0))
        self.provider.allowed = False
        h = self.holder.begin(5)
        self.assertTrue(self.holder.use(h))
        self.assertEqual(self.provider.calls, 1)

    def test_expired_entry_denies_new_use_but_not_old_handle(self):
        h = self.holder.begin(0)
        self.provider.allowed = False
        with self.assertRaises(Denied):
            self.holder.begin(10)
        self.assertIsNone(self.holder.cached)
        self.assertTrue(self.holder.use(h))

    def test_elapsed_age_without_lookup_is_not_retirement(self):
        h = self.holder.begin(0)
        now = 100
        self.assertGreater(now, self.holder.expires_at)
        self.assertIsNotNone(self.holder.cached)
        self.assertTrue(self.holder.use(h))

    def test_cache_retirement_requires_handle_completion(self):
        h = self.holder.begin(0)
        self.holder.retire_cache()
        self.assertTrue(self.holder.use(h))
        self.holder.finish(h)
        self.assertFalse(self.holder.use(h))

    def test_new_generation_does_not_retire_old_generation(self):
        h = self.holder.begin(0)
        self.provider.allowed = False
        new = Holder(self.provider, "g2")
        with self.assertRaises(Denied):
            new.begin(1)
        self.assertTrue(self.holder.use(h))

    def test_complete_remedy_and_control(self):
        h = self.holder.begin(0)
        self.provider.allowed = False
        self.holder.retire_cache()
        self.holder.finish(h)
        with self.assertRaises(Denied):
            self.holder.begin(20)
        control = Holder(Provider(), "control")
        self.assertTrue(control.use(control.begin(20)))
        observed = Observation("g1", True, True, len(self.holder.handles), True)
        self.assertTrue(can_close_continued_use({"a": "g1"}, {"a": observed}))

    def test_closure_evidence_counterexamples(self):
        good = Observation("g1", True, True, 0, True)
        cases = {
            "generation mismatch": replace(good, generation="g0"),
            "wrong key version": replace(good, key_version="key-v2"),
            "stale observation": replace(good, fresh=False),
            "acquisition permitted": replace(good, acquisition_denied=False),
            "cache retained": replace(good, cache_retired=False),
            "in-flight holder": replace(good, active_handles=1),
            "invalid count": replace(good, active_handles=-1),
            "service unavailable": replace(good, permitted_control=False),
        }
        for label, observation in cases.items():
            with self.subTest(label=label):
                self.assertFalse(can_close_continued_use({"a": "g1"}, {"a": observation}))

    def test_population_not_silently_reduced(self):
        good = Observation("g1", True, True, 0, True)
        self.assertFalse(can_close_continued_use({}, {}))
        self.assertFalse(can_close_continued_use({"a": "g1"}, {"a": good}, ""))
        self.assertFalse(can_close_continued_use({"a": "g1", "b": "g1"}, {"a": good}))
        self.assertFalse(can_close_continued_use({"a": "g1"}, {"a": good, "b": good}))
        self.assertTrue(can_close_continued_use({"a": "g1", "b": "g1"}, {"a": good, "b": good}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
