---
name: python-descriptors-mro
description: Use when designing Python attribute protocols, multiple inheritance, or metaclasses — descriptor precedence, __set_name__, __slots__ interaction, C3 linearization rules, super() order, "MRO conflict" TypeError; applies when building validators, ORM fields, property-like wrappers, or debugging surprising attribute lookups
---

# Python Descriptors & MRO

Attribute access walks `type(obj).__mro__` via `__getattribute__`. Data descriptors win over instance `__dict__`; non-data descriptors lose to it. `super()` follows the MRO of `type(self)`, not the syntactic parent.

## Attribute lookup order

| # | Source | Condition |
|---|--------|-----------|
| 1 | Data descriptor from MRO | defines `__set__` or `__delete__` |
| 2 | `obj.__dict__[name]` | instance variable |
| 3 | Non-data descriptor / class var | defines only `__get__` |
| 4 | `__getattr__` | steps 1–3 all miss |

`vars(cls)[name]` returns the descriptor object itself — bypasses the protocol.

## Descriptor protocol

```python
class D:
    def __set_name__(self, owner, name):  # fires once at class creation
        self.private = f'_{name}'
    def __get__(self, obj, objtype=None):
        if obj is None: return self        # access via class
        return getattr(obj, self.private)
    def __set__(self, obj, value):         # presence → DATA descriptor
        setattr(obj, self.private, value)
```

Descriptors must live on the class. Assigning after definition (`setattr(cls, 'x', D())`) skips `__set_name__` — call it manually.

## Functions as descriptors

| Wrapper | `__get__` returns |
|---------|-------------------|
| plain function | `MethodType(f, obj)` |
| `@classmethod` | `MethodType(f, cls)` |
| `@staticmethod` | the raw function |
| `@property` | result of `fget(obj)` |

## `__slots__`

Each slot is a data descriptor into a fixed C array. ~35% faster attribute access, ~3× less memory. Incompatible with `functools.cached_property`. A subclass without `__slots__` re-adds `__dict__`, erasing the saving.

## C3 linearization

`L[C(B1..Bn)] = C + merge(L[B1], …, L[Bn], [B1, …, Bn])`

**Merge rule:** take the head of the first list whose head does not appear in the tail of any other list; remove from all; repeat. If none qualifies, raise `TypeError: MRO conflict`.

```python
class A(X, Y): ...   # L[A] forces X before Y
class B(Y, X): ...   # L[B] forces Y before X
class C(A, B): ...   # TypeError — irreconcilable
```

## Pitfalls

- **Non-data descriptor shadowed by instance attr:** `obj.m = 5` silently overrides a method-like descriptor. Define `__set__` (raise, or accept) to stop it.
- **`__set_name__` never fires for post-hoc assignment:** `setattr(cls, 'x', D())` — call `D().__set_name__(cls, 'x')` yourself.
- **`vars()` / `obj.__dict__` bypasses descriptors:** useful for introspection, dangerous for writes.
- **`super()` bare form requires a class cell:** fails in nested functions or when copied to a class without `__class__` closure.
- **"Diamond" inheritance order matters:** list the more specific parent first; `class G(F, E)` fails if `E` extends `F`.
- **Redundant bases break C3:** `class B(A, O)` when `A` already inherits from `O` — raises `TypeError`.
