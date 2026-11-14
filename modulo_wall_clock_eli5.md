# ELI5: Why `%` Turns an Offset Into a Clock Time

## The short version

A day is a circle, not a line. `%` tells you where you land on that circle, however far you walk and in whichever direction.

## The clock picture

Imagine a clock with 86,400 ticks, one for each second of the day. Tick 0 is midnight, and you start there.

- **Walk forward 76 ticks:** you land on tick 76, which is just after midnight.
- **Walk backward 76 ticks:** you pass midnight going the other way and land on tick 86,324, which is late the night before.

That is what the two expressions do:

```python
76 % ONE_DAY_IN_SECS   # 76
-76 % ONE_DAY_IN_SECS  # 86324
```

Tick 86,324 reads as `23:58:44`, which is 76 seconds before midnight.

## Why the answer is always a valid time

The clock has no tick below 0 and no tick above 86,399, so you can't land anywhere that isn't a real time. Walking all the way around just brings you back to where you were:

| Offset | Result | Clock time |
|---|---|---|
| `0` | `0` | `00:00:00` |
| `76` | `76` | `00:01:16` |
| `-76` | `86324` | `23:58:44` |
| `86400` | `0` | `00:00:00` |
| `86476` | `76` | `00:01:16` |

This is why the `24:00` results went away. Nothing needs to decide whether to add a day, because `%` handles both directions the same way.

## The math behind it

Python's `a % n` answers this question: after taking away as many whole `n`s as you can, rounding down, what's left?

For `-76 % 86400`:

1. `-76 / 86400` is about `-0.0009`.
2. Rounding down gives `-1`, so that's one whole day.
3. One whole day backward is `-1 * 86400 = -86400`.
4. What's left is `-76 - (-86400) = 86324`.

In Python, when `n` is positive, the result is always between `0` and `n - 1`.

## Language difference

This behavior is specific to languages that round down, such as Python. In Go, C, Java and JavaScript, `%` rounds toward zero and keeps the sign of the left side, so `-76 % 86400` is `-76` there.

To get the same result in Go:

```go
((x % 86400) + 86400) % 86400
```

## Understanding the Go expression

Go's `%` can return a negative number, so the expression is a workaround with three steps, each fixing what the previous one leaves behind:

| Step | What it does | Range after this step | `x = -76` | `x = 76` | `x = -100000` |
|---|---|---|---|---|---|
| `x % 86400` | Removes whole days, but keeps the sign | `-86399` to `86399` | `-76` | `76` | `-13600` |
| `+ 86400` | Adds one day, so the number can't be negative | `1` to `172799` | `86324` | `86476` | `72800` |
| `% 86400` | Removes the extra day if there is one | `0` to `86399` | `86324` | `76` | `72800` |

Each `%` is needed:

- **Without the first `%`:** adding one day isn't enough for far-off values. `-100000 + 86400` is `-13600`, which is still negative.
- **Without the last `%`:** positive inputs overshoot. `76 + 86400` is `86476`, which isn't a valid time.

The one-day addition is what forces the last step: it's needed for negative values, but it's also applied to positive ones, so it has to be removed from those.

### A clearer way to write it

The one-liner is a common idiom, but an `if` says what it means:

```go
r := x % 86400
if r < 0 {
    r += 86400
}
```

This gives the same results: only a negative remainder gets a day added, so there's no extra day to remove. None of this is needed in `midnight_stats.py`, because Python's `%` already does it.
