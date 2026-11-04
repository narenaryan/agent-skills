"""Original deterministic model; not a Kafka client or durable scheduler.

Trusted events represent validated full-state rebuilds and durable sink writes.
A whole-consumer generation reset models lost ownership. Real sink fencing,
partial/cooperative rebalances, leader epochs and commit failures are not modeled.
"""
from dataclasses import dataclass
from itertools import permutations
import unittest


@dataclass(frozen=True)
class Ticket:
    generation: int
    partition: str
    offset: int
    key: str
    revision: int


@dataclass(frozen=True)
class Job:
    generation: int
    attempt: int
    key: str
    members: tuple

    @property
    def required_revision(self):
        return max(t.revision for t in self.members)


class Coordinator:
    def __init__(self, starts):
        self.generation = 0
        self.sequence = 0
        self.reset(starts)

    def reset(self, starts):
        """Trusted reassignment/start positions. Discards volatile completions."""
        self.generation += 1
        self.starts = dict(starts)
        self.next_positions = dict(starts)
        self.delivered = {p: [] for p in starts}
        self.done = set()
        self.inflight = {}
        self.queued = {}

    def poll(self, partition, rows, next_position):
        """Rows are (offset, key, revision), delivered in partition order."""
        previous_position = self.next_positions[partition]
        offsets = [r[0] for r in rows]
        if (offsets != sorted(set(offsets)) or
                any(o < previous_position for o in offsets) or
                next_position < previous_position or
                (offsets and next_position <= offsets[-1])):
            raise ValueError('not a forward-only poll result')
        for offset, key, revision in rows:
            t = Ticket(self.generation, partition, offset, key, revision)
            self.delivered[partition].append(t)
            self.queued.setdefault(key, []).append(t)
        self.next_positions[partition] = next_position

    def start(self, key):
        if key in self.inflight:
            raise ValueError('one in-flight build per key')
        members = tuple(self.queued.pop(key))
        self.sequence += 1
        job = Job(self.generation, self.sequence, key, members)
        self.inflight[key] = job
        return job

    def current(self, job):
        return job.generation == self.generation and self.inflight.get(job.key) == job

    def failed(self, job):
        if not self.current(job):
            return False
        del self.inflight[job.key]
        self.queued[job.key] = list(job.members) + self.queued.get(job.key, [])
        return True

    def succeeded(self, job, durable, built_revision):
        if not self.current(job) or not durable or built_revision < job.required_revision:
            return False
        self.done.update(job.members)
        del self.inflight[job.key]
        return True

    def frontier(self, partition):
        # Ordered delivered records, not every integer offset.
        for t in self.delivered[partition]:
            if t not in self.done:
                return t.offset
        return self.next_positions[partition]

    def replay_after(self, partition, committed):
        return [t for t in self.delivered[partition] if t.offset >= committed]


class Contracts(unittest.TestCase):
    def test_out_of_order_completion_cannot_skip_earlier(self):
        c=Coordinator({'p':10});c.poll('p',[(10,'A',1),(11,'B',1),(12,'C',1)],13)
        a,b,d=[c.start(k) for k in 'ABC']
        c.succeeded(d,True,1);c.succeeded(b,True,1)
        self.assertEqual(c.frontier('p'),10)
        # Faulty max-completed+1=13 loses A after restart.
        bad=max(t.offset for t in c.done)+1
        self.assertEqual(c.replay_after('p',bad),[])
        self.assertEqual(c.replay_after('p',c.frontier('p'))[0].key,'A')
        c.succeeded(a,True,1);self.assertEqual(c.frontier('p'),13)

    def test_sparse_offsets_are_not_missing_work(self):
        c=Coordinator({'p':10});c.poll('p',[(10,'A',1),(14,'B',1),(19,'C',1)],23)
        for k in 'AB':c.succeeded(c.start(k),True,1)
        self.assertEqual(c.frontier('p'),19)
        c.succeeded(c.start('C'),True,1);self.assertEqual(c.frontier('p'),23)
        # An integer-adjacency tracker would stall at nonexistent offset 11.
        self.assertNotEqual(c.frontier('p'),11)

    def test_one_build_preserves_every_ack_obligation(self):
        c=Coordinator({'p':0});c.poll('p',[(0,'A',1),(2,'A',2),(3,'A',3)],4)
        j=c.start('A');self.assertEqual(len(j.members),3)
        self.assertFalse(c.succeeded(j,True,2));self.assertEqual(c.frontier('p'),0)
        self.assertTrue(c.succeeded(j,True,3));self.assertEqual(c.frontier('p'),4)

    def test_new_arrival_does_not_join_running_job(self):
        c=Coordinator({'p':0});c.poll('p',[(0,'A',1)],1);j=c.start('A')
        c.poll('p',[(1,'A',2)],2)
        with self.assertRaises(ValueError):c.start('A')
        c.succeeded(j,True,1);self.assertEqual(c.frontier('p'),1)
        c.succeeded(c.start('A'),True,2);self.assertEqual(c.frontier('p'),2)

    def test_retry_retains_members_and_rejects_old_attempt(self):
        c=Coordinator({'p':0});c.poll('p',[(0,'A',1)],1);old=c.start('A')
        c.poll('p',[(1,'A',2)],2);self.assertTrue(c.failed(old))
        new=c.start('A');self.assertEqual(len(new.members),2)
        self.assertFalse(c.succeeded(old,True,2));self.assertEqual(c.frontier('p'),0)
        c.succeeded(new,True,2);self.assertEqual(c.frontier('p'),2)

    def test_durability_is_separate_from_compute_success(self):
        c=Coordinator({'p':0});c.poll('p',[(0,'A',1)],1);j=c.start('A')
        self.assertFalse(c.succeeded(j,False,1));self.assertEqual(c.frontier('p'),0)
        self.assertTrue(c.succeeded(j,True,1));self.assertEqual(c.frontier('p'),1)

    def test_partition_frontiers_are_independent(self):
        c=Coordinator({'p':10,'q':100})
        c.poll('p',[(10,'A',1)],11);c.poll('q',[(100,'B',1)],105)
        c.succeeded(c.start('B'),True,1)
        self.assertEqual(c.frontier('p'),10);self.assertEqual(c.frontier('q'),105)

    def test_coalesced_members_can_span_partitions(self):
        c=Coordinator({'p':10,'q':100})
        c.poll('p',[(10,'A',1)],11);c.poll('q',[(100,'A',2)],105)
        c.succeeded(c.start('A'),True,2)
        self.assertEqual(c.frontier('p'),11);self.assertEqual(c.frontier('q'),105)

    def test_stale_generation_callback_is_not_new_completion(self):
        c=Coordinator({'p':0});c.poll('p',[(0,'A',1)],1);old=c.start('A')
        c.reset({'p':0});c.poll('p',[(0,'A',1)],1);new=c.start('A')
        self.assertFalse(c.succeeded(old,True,1));self.assertEqual(c.frontier('p'),0)
        c.succeeded(new,True,1);self.assertEqual(c.frontier('p'),1)

    def test_crash_after_write_before_commit_replays(self):
        c=Coordinator({'p':0});c.poll('p',[(0,'A',1)],1)
        c.succeeded(c.start('A'),True,1)
        # Simulate no durable Kafka commit: restart from old committed position.
        c.reset({'p':0});c.poll('p',[(0,'A',1)],1)
        self.assertEqual(c.frontier('p'),0)
        self.assertEqual(c.start('A').required_revision,1)
        # This models repeated work, not actual sink idempotency.

    def test_all_three_job_completion_orders(self):
        for order in permutations('ABC'):
            c=Coordinator({'p':10});c.poll('p',[(10,'A',1),(14,'B',1),(19,'C',1)],23)
            jobs={k:c.start(k) for k in 'ABC'};completed=set()
            for k in order:
                c.succeeded(jobs[k],True,1);completed.add(k)
                expected=next((o for o,key in [(10,'A'),(14,'B'),(19,'C')] if key not in completed),23)
                self.assertEqual(c.frontier('p'),expected)

    def test_bad_poll_is_atomic_rejection(self):
        for rows,end in [([(2,'A',1),(1,'B',1)],3),([(0,'A',1),(0,'B',1)],1),([(0,'A',1)],0)]:
            c=Coordinator({'p':0})
            with self.assertRaises(ValueError):c.poll('p',rows,end)
            self.assertEqual(c.delivered['p'],[]);self.assertEqual(c.frontier('p'),0)

    def test_duplicate_success_does_not_complete_later_work(self):
        c=Coordinator({'p':0});c.poll('p',[(0,'A',1)],1);old=c.start('A');c.succeeded(old,True,1)
        c.poll('p',[(1,'A',2)],2);new=c.start('A')
        self.assertFalse(c.succeeded(old,True,2));self.assertEqual(c.frontier('p'),1)
        c.succeeded(new,True,2);self.assertEqual(c.frontier('p'),2)


if __name__=='__main__':
    unittest.main(verbosity=2)
