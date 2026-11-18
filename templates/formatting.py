import re

# Precompiled patterns (compiled once at import time)
_CODE = re.compile(r"```.*?```|~~~.*?~~~|`[^`\n]+`", re.DOTALL)
_ENV = re.compile(r"\\begin\{((?:[bpvBV]|small)?matrix\*?|array|cases)\}(.*?)\\end\{\1\}", re.DOTALL)
_ROW_BREAK = re.compile(r"(?<!\\)\\(?=\s|$)")
_BARE_BLOCK = re.compile(r"^[ \t]*\[[ \t]*\n?([^\[\]]*?)\n?[ \t]*\][ \t]*$", re.MULTILINE)
_DISPLAY = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)
_EMPTY_INLINE = re.compile(r"(?<!\$)\$[ \t]+\$(?!\$)")
_INLINE = re.compile(r"(?<![\\$])\$(?!\$)([^$\n]+?)(?<!\\)\$(?!\$)")
_PAREN = re.compile(r"(?<![\w\]])\(((?:[^()\n]|\([^()\n]*\))+)\)")
_CMD = re.compile(r"\\[a-zA-Z]+")
_SUBSUP = re.compile(r"[A-Za-z0-9}'][_^]")
_PROSE = re.compile(r"\b[A-Za-z]{3,}\s+[A-Za-z]{3,}\b")
_REL = re.compile(r"[A-Za-z0-9')}\]]\s*[=<>+\-*/]\s*[A-Za-z0-9\\(]")
_PLACEHOLDER = re.compile(r"\x00(\d+)\x00")

# Bare (undelimited) math runs such as  T_s - T_\infty  or  R_1 = 3 \, \Omega
_ATOM = (r"(?:\\[a-zA-Z]+(?:\{[^{}]*\})*"
         r"|[A-Za-z0-9.]+'*(?:[_^](?:\{[^{}]*\}|\\[a-zA-Z]+|[A-Za-z0-9](?![A-Za-z0-9])))*"
         r"|\([^()\n$\x00]*\))")
_JOIN = r"(?:[ \t]*[=+\-*/<>][ \t]*|[ \t]*\\[,;:!][ \t]*)"
_BARE_RUN = re.compile(rf"(?<![\w\\$\x00]){_ATOM}(?:{_JOIN}{_ATOM})*")


def sanitize_latex_output(text: str) -> str:
    """
    Robustly fixes and normalizes LLM LaTeX formatting errors into standard Markdown.
    Handles block math, inline math (parenthesized, padded, or undelimited), matrix row
    breaks, and empty math wrappers. Never raises: on any error the original text is returned.
    """
    if not text or not isinstance(text, str):
        return str(text or "")

    try:
        stash = []

        def hold(s):
            stash.append(s)
            return f"\x00{len(stash) - 1}\x00"

        def is_math(c):
            if "$" in c:
                return False
            if _CMD.search(c) or _SUBSUP.search(c):
                return True
            return not _PROSE.search(c) and bool(_REL.search(c))

        def inline(m):
            c = m[1]
            # "$ x $" -> "$x$"; leave currency like "$5 and $6" alone
            if c != c.strip() and not is_math(c.strip()):
                return m[0]
            return hold(f"${c.strip()}$")

        def bare(m):
            r = m[0]
            return hold(f"${r}$") if (_CMD.search(r) or _SUBSUP.search(r)) else r

        # 0. Protect code blocks / inline code
        text = _CODE.sub(lambda m: hold(m[0]), text)

        # 1. Matrix/array row breaks: lone "\" before whitespace/end -> "\\"
        text = _ENV.sub(lambda m: f"\\begin{{{m[1]}}}{_ROW_BREAK.sub(lambda _: chr(92) * 2, m[2])}\\end{{{m[1]}}}", text)

        # 2. \[ ... \] -> $$ ... $$ ; \( ... \) -> $ ... $ ; bare [ \cmd ... ] lines -> $$ ... $$
        text = re.sub(r"\\\[(.*?)\\\]", lambda m: f"$${m[1]}$$", text, flags=re.DOTALL)
        text = re.sub(r"\\\((.*?)\\\)", lambda m: f"${m[1]}$", text, flags=re.DOTALL)
        text = _BARE_BLOCK.sub(lambda m: f"$${m[1].strip()}$$" if _CMD.search(m[1]) else m[0], text)

        # 3. Stash display math on its own lines (drop empty), then clean/stash inline math
        text = _DISPLAY.sub(lambda m: hold(f"\n\n$$\n{m[1].strip()}\n$$\n\n") if m[1].strip() else "", text)
        text = _EMPTY_INLINE.sub("", text)
        text = _INLINE.sub(inline, text)

        # 4. ( math ) -> $math$ for anything still unwrapped
        text = _PAREN.sub(lambda m: hold(f"${m[1].strip()}$") if is_math(m[1].strip()) else m[0], text)

        # 5. Undelimited math runs (T_s - T_\infty, \alpha + \beta) -> $...$
        text = _BARE_RUN.sub(bare, text)

        # 6. Restore stashed segments (nesting is possible, so loop)
        for _ in range(3):
            text = _PLACEHOLDER.sub(lambda m: stash[int(m[1])], text)

        return re.sub(r"\n{3,}", "\n\n", text)

    except Exception as e:
        print(f"LaTeX Sanitization Error: {e}")
        return text