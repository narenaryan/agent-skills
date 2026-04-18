---
name: python-unicode-gotchas
description: Use when handling Python text encoding — UnicodeDecodeError/EncodeError, mojibake, filesystem names with non-UTF-8 bytes, combining-character mismatches, case-insensitive string compare, regex \w/\d unexpected behavior, or round-tripping unknown-encoding files; covers error handlers (surrogateescape, backslashreplace), normalization (NFC/NFD/NFKC/NFKD), BOM handling, and open()'s encoding vs errors
---

# Python Unicode Gotchas

`str` = code points, `bytes` = encoded output. Visually identical strings can differ in length (precomposed vs combining). `str + bytes` → `TypeError`; decode at input, encode at output.

## Error handlers

| Handler | dec | enc | Effect |
|---------|:---:|:---:|--------|
| `strict` (default) | ✓ | ✓ | raises UnicodeError |
| `ignore` | ✓ | ✓ | drops offending char |
| `replace` | ✓ | ✓ | `U+FFFD` / `?` |
| `backslashreplace` | ✓ | ✓ | `\x80`, `\uXXXX` |
| `xmlcharrefreplace` | — | ✓ | `&#NNN;` |
| `namereplace` | — | ✓ | `\N{NAME}` |
| `surrogateescape` | ✓ | ✓ | lossless round-trip of unknown bytes |
| `surrogatepass` | ✓ | ✓ | allows lone surrogates in UTF-8/16/32 |

`surrogateescape` maps bytes `0x80–0xFF` ↔ `U+DC80–U+DCFF`. Use for read-then-write-back of files with unknown encoding.

## File I/O

```python
open(p, encoding='utf-8-sig')                      # strip UTF-8 BOM on read
open(p, encoding='ascii', errors='surrogateescape') # round-trip unknown bytes
```

`utf-16` auto-detects endianness + writes BOM; `utf-16-le`/`-be` skip BOM. Default encoding on Py3.15+ is UTF-8; on 3.10–3.14 it follows `locale.getpreferredencoding()` unless `PYTHONUTF8=1`.

## Normalization

Four forms. Same visual character can be **one** code point or **base + combining**:

```python
import unicodedata
s1 = 'ê'                                   # len 1  — precomposed
s2 = 'e\N{COMBINING CIRCUMFLEX ACCENT}'    # len 2  — decomposed
s1 == s2                                   # False
unicodedata.normalize('NFC', s1) == unicodedata.normalize('NFC', s2)  # True
```

| Form | Decomposes? | Compat map? | Use for |
|------|-------------|-------------|---------|
| NFC | recomposed | no | storage, equality after input |
| NFD | fully split | no | searching / regex on base chars |
| NFKC | recomposed | yes (`ﬁ` → `fi`) | loose matching, search keys |
| NFKD | fully split | yes | aggressive normalization |

## Case-insensitive compare

```python
def eq_ci(a, b):
    n = unicodedata.normalize
    return n('NFD', n('NFD', a).casefold()) == n('NFD', n('NFD', b).casefold())
```

`casefold()` handles cases `lower()` misses (`ß → ss`, Greek final sigma). Double NFD because casefolding may introduce combining sequences.

## Regex

| Pattern | `\d` | `\w` | `\s` |
|---------|------|------|------|
| `str` (default) | any Unicode digit | letters+digits+`_` (Unicode) | Unicode whitespace |
| `bytes` | `[0-9]` | `[A-Za-z0-9_]` | ASCII whitespace |
| `str` + `re.ASCII` | `[0-9]` | `[A-Za-z0-9_]` | ASCII whitespace |

Thai `๕๗` matches `\d+` in a str pattern but not with `re.ASCII`.

## Pitfalls

- **`len(s)` ≠ grapheme count:** normalize first, or use a grapheme library.
- **Undecodable filenames:** `os.listdir('.')` can raise — use `surrogateescape` or pass `bytes`.
- **UTF-8 BOM from Excel/Notepad:** breaks naive `encoding='utf-8'`; use `utf-8-sig`.
- **Python <3.15 on non-UTF-8 locale:** `open()` default is cp1252 etc. Set `PYTHONUTF8=1` or always pass `encoding=`.
- **`casefold()` still needs normalization:** `ss` ≠ `ß` without it; `ﬁ` ≠ `fi` without NFKC.
- **Lone surrogates only encode under `surrogatepass`:** a `str` holding `U+DC80` errors on plain UTF-8 encode.
