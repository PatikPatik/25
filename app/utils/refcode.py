from __future__ import annotations

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def encode_ref(user_id: int) -> str:
    n = max(1, int(user_id))
    base = len(ALPHABET)
    out = ""
    while n:
        n, r = divmod(n, base)
        out = ALPHABET[r] + out
    return "R" + out

def decode_ref(code: str) -> int | None:
    if not code or not code.upper().startswith("R"):
        return None
    s = code[1:].upper()
    base = len(ALPHABET)
    n = 0
    for ch in s:
        if ch not in ALPHABET:
            return None
        n = n * base + ALPHABET.index(ch)
    return n if n > 0 else None
