# Midnight Stats

Computes the mean, median and standard deviation of times of day that cluster around midnight, such as bedtimes. A plain average of 23:50 and 00:10 gives 12:00. This gives 00:00.

Requires Python 3.10 or later, with no third-party packages.

## Usage

```
python3 midnight_stats.py [CUTOFF] FILE
```

- `FILE`: a text file with one 24-hour `HH:MM` time per line.
- `CUTOFF`: optional `HH:MM`. Times at or after the cutoff count as the day before midnight. The default is `12:00`.
- `-h`, `--help` or no arguments prints the usage.

## Example

Given `times.txt`:

```
23:50
23:55
00:05
00:20
```

Running `python3 midnight_stats.py times.txt` prints:

```
avg: 00:02:30
med: 00:00:00
sd : 00h 13m 14s
```

`avg` and `med` are clock times. `sd` is a length of time: a typical time in this file is about 13 minutes from the mean. A file with only one time prints no `sd` line.

## How it works

Each time is converted to seconds since midnight. Times at or after the cutoff have one day subtracted, so 23:50 becomes -600 seconds and 00:10 stays at 600. The mean and median are calculated from these signed values, rounded down to whole seconds, and turned back into a clock time with `%`, which wraps negative values back to the previous evening.

The standard deviation is calculated from the same signed values: square each value's difference from the exact mean, add the squares up, divide by n - 1, and take the square root. Dividing by n - 1 rather than n treats the times as a sample, such as a few weeks of logins standing in for a person's usual habit. The result is a length of time, rounded to the nearest second, so it's printed as hours, minutes and seconds rather than as a clock time.

With the default cutoff, every time must be within 12 hours of midnight. If the times center on a different hour, set the cutoff 12 hours away from that hour.

## Testing

```
python3 check_midnight_stats.py [--cutoff HH:MM]
```

This runs `midnight_stats.py` on every `test*.txt` file and compares its mean, median and standard deviation with an independent calculation that uses Python's `statistics` module. It prints PASS, FAIL or ERROR for each file.

## References

- [midnight_stats.py](midnight_stats.py): the program.
- [check_midnight_stats.py](check_midnight_stats.py): the test checker.
- [modulo_wall_clock_eli5.md](modulo_wall_clock_eli5.md): why `%` turns a signed offset into a clock time.
- [FUTURE_WORK.md](FUTURE_WORK.md): statistics that could be added next.
