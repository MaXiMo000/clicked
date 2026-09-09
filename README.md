# clicked

[![ci](https://github.com/MaXiMo000/clicked/actions/workflows/ci.yml/badge.svg)](https://github.com/MaXiMo000/clicked/actions/workflows/ci.yml)

**Prove what one browser interaction actually did -- every network
request it made, and optionally what changed on a local backing store.**

[`receipt`](https://github.com/MaXiMo000/receipt) proves what a shell
command touched. [`custody`](https://github.com/MaXiMo000/custody) proves
what an AI agent's tool call touched. `clicked` proves what a *click*
touched -- the same "verified execution, not just self-report" idea, one
layer up: a browser-automation test that asserts "clicking Save sends the
right request" is trusting the test's own assumption unless something
independently recorded what the browser actually sent.

```python
from clicked import capture

with capture(page, task="click save button") as c:
    page.click("#save")
    page.wait_for_timeout(200)

print(c.to_dict())
```

```json
{
  "providence_version": 1,
  "tool": "clicked",
  "payload": {
    "task": "click save button",
    "seconds": 0.324,
    "requests": [
      {"url": "http://127.0.0.1:60672/api/save", "method": "POST",
       "post_data": "{\"name\":\"ada\"}", "status": 200, "failure": null}
    ],
    "raised": null
  },
  "sha256": "ed727efcdccbc..."
}
```

(Real output, from `tests/test_capture_live.py` -- a real headless
Chromium, clicking a real button, against a real local HTTP server.)

## Install

```
pip install clicked-evidence               # network capture only
pip install "clicked-evidence[filesystem]"  # + the watch_dir feature below
```

For once, no PyPI name-squatting to work around -- both `clicked` and
`clicked-evidence` were actually free.

## Use

`capture()` takes any Playwright `Page` object and a `task` description.
Everything inside the `with` block is one interaction:

```python
from clicked import capture

with capture(page, task="delete account button") as c:
    page.click("#delete-account-button")
    page.wait_for_load_state("networkidle")

c.write("receipt.json")   # a Providence bundle -- see below
```

`c.requests` is every network request/response pair that happened during
the block (URL, method, POST body, status, or a `failure` reason if the
request never got a response at all). This is what was actually sent and
actually came back -- not what the page's own JavaScript claims it sent.

### The `filesystem` extra

Pass `watch_dir` to also snapshot-diff a local directory before and after
the interaction, reusing `receipt.snapshot`'s real `snapshot()`/`diff()`
core directly (not reimplemented):

```python
with capture(page, task="click save button", watch_dir="./data") as c:
    page.click("#save")
    page.wait_for_timeout(200)

print(c.result["changes"])  # {"added": ["saved.json"], "modified": [], ...}
```

This closes the loop from *client* interaction to *backend* side effect --
proving the click didn't just send a request that returned 200, but that
a real file actually landed on disk because of it. Requires `pip install
"clicked-evidence[filesystem]"`; without it, `watch_dir` is silently
ignored and `capture()` still works for network-only verification.

### Why no CLI

Every other tool in this portfolio is a CLI because each one wraps a
command, a file, or a config a human or CI job invokes directly. `clicked`
instruments one interaction inside a caller's *own* Playwright script --
there's nothing to invoke from a shell that isn't already that script.
The receipt itself is a Providence bundle either way (`c.to_dict()` /
`c.write(path)`), so it plugs into the same evidence pipeline as
everything else in this portfolio without needing its own entry point.

## Playwright is never imported here

`capture()` only calls `.on()` and `.remove_listener()` on whatever object
you pass it -- duck-typed, not a hard dependency on Playwright or any
particular version of it. `receipt-evidence` (the `filesystem` extra) is
the one real dependency this package has, and it's optional because
network capture is useful entirely on its own for a purely client-side
interaction with nothing local to watch.

## Tests

```
pip install -e ".[filesystem]"
python tests/test_capture.py         # pure logic, a fake page object, no browser needed
```

```
pip install -e ".[filesystem]" playwright
python -m playwright install chromium
python tests/test_capture_live.py    # real Chromium, real HTTP server, real network + filesystem effects
```

11 tests total (8 + 3). The live suite is the one that actually matters
for a package whose whole point is "did this really happen" -- it skips
cleanly, rather than failing, if Playwright or its browser binary isn't
installed.

MIT licensed.
