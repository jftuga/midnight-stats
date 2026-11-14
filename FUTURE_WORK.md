# Midnight Stats: Future Work

This plan lists statistics that could be added to `midnight_stats.py`, in the recommended order, along with the design rules they depend on.

## Current state

`midnight_stats.py` reads a file of 24-hour `HH:MM` times, one per line, and prints three statistics:

```
avg: 08:59:37
med: 08:59:00
sd : 00h 14m 44s
```

Before calculating, it converts each time to seconds since midnight and subtracts one day from any time at or after a cutoff (12:00 by default). This turns times on both sides of midnight into one continuous range of signed numbers, so 23:50 becomes -600 and 00:10 stays at 600.

- **Mean and median:** printed as clock times, rounded down to whole seconds and converted back with `%`, which wraps negative values back to the previous evening.
- **Standard deviation:** the sample standard deviation (dividing by n - 1), calculated from the exact mean, rounded to the nearest second and printed as a length of time by `length_of_time()`. It's left out when the file holds only one time.

The method requires every time to be within 12 hours of the point opposite the cutoff. With the default cutoff, that means within 12 hours of midnight.

`check_midnight_stats.py` checks all three statistics for each `test*.txt` file against an independent calculation that uses Python's `statistics` module.

## Done

- **Formatter for lengths of time:** `length_of_time()` prints a length as `HHh MMm SSs`, separately from `wall_time()`, which prints clock times. Design rule 2 depends on it.
- **Standard deviation:** `variance()` and `standard_deviation()`, written from scratch rather than with the `statistics` module. They divide by n - 1 because the times are treated as a sample of a person's usual habit.
- **Test for negative mean rounding:** `test0.txt` (six `00:00` entries and one `23:59` entry) has a negative average that isn't a whole number of seconds. It checks that the mean is rounded down with `math.floor`, giving 23:59:51. Rounding toward zero with `int()` would give 23:59:52.

## Design rules

These rules apply to every item below.

1. **Shift before calculating anything.** Once each time is a signed offset, it's an ordinary number, and most standard statistics apply without changes. A statistic calculated on the raw values is wrong whenever the data crosses midnight. For example, the raw minimum of 23:50 and 00:10 is 00:10.
2. **Keep positions separate from lengths of time.** Results come in two kinds, and they must be formatted differently.
   - **A position on the clock**, such as the mean, median, earliest, latest or a percentile, is converted with `wall_time()` and printed as `HH:MM:SS`.
   - **A length of time**, such as the standard deviation, IQR, range or MAD, is printed with `length_of_time()`. Never pass one to `wall_time()`: a standard deviation of 12 minutes would print as `00:12:00`, which reads as a time just after midnight.
3. **Use the exact mean in calculations.** `mean()` returns an unrounded float. Round only when printing, so later statistics measure from the true center.
4. **Add a test with every new statistic.** Each one needs a reference calculation in `check_midnight_stats.py` and at least one test file whose times cross midnight.
5. **Keep output labels aligned.** Each label is three characters followed by `: `, as in `avg:`, `med:` and `sd :`. The checker strips the spaces from labels before matching them.

## Phase 1: Statistics that need no new input

These fit the current input format and give the most information for the least work.

| Statistic | Kind | Notes |
|---|---|---|
| Earliest and latest | Position | Take the minimum and maximum of the shifted values. Label them "earliest" and "latest" rather than min and max, so nobody reads them as raw values. |
| Range | Length of time | Latest minus earliest. |
| Percentiles (p10, p25, p75, p90) | Position | For logins, p90 means "on the latest 10% of days, the login came after X". It's more informative than the latest time, which reflects only one day. |
| IQR | Length of time | p75 minus p25. Unlike the range, a single extreme day doesn't affect it. |

`median_of_sorted()` is already a 50th-percentile function, so a general percentile function could replace it.

## Phase 2: Distribution shape

These also fit the current input, but they're less useful or need a choice made first.

- **Binned mode.** An exact mode is weak for minute-level data. Twenty-one logins spread over an hour rarely repeat a minute, so there's often no mode or several. Count the times in 5- or 15-minute bins instead and report the busiest bin. Bins must be built from shifted values, or a bin from 23:55 to 00:05 splits in two. Needs a bin-size option with a sensible default.
- **Outliers.** Use the IQR method or a MAD-based modified Z-score on the shifted values. MAD is better for small sets, because one extreme value can't inflate it enough to hide itself. A Z-score method can reuse `standard_deviation()`. A known limit: a time past the cutoff, such as a 21:00 entry in morning login data, gets shifted to the previous day. It's still flagged as an outlier, but the time it reports is wrong.

## Phase 3: Comparison with a target time

Add an optional target time as input, such as `--target 09:00`, and report:

- The percentage of times after the target, for example "38% of logins after 09:00".
- The average difference from the target, for example "average 6m late". This is a length of time with a sign, so `length_of_time()` would need to handle negative values.

This answers the practical question for logins and bedtimes: how often the goal is missed, and by how much.

## Phase 4: Dated input

Today, the program has to assume the file holds one line per day with no gaps. That's true for a clean log, but weekends and days off break it for logins. Adding a date to each line, such as `2026-11-09 08:52`, makes these possible:

- **Day of the week:** weekday and weekend averages. Probably the most useful result for bedtimes.
- **Trend:** the slope of a line fitted through the shifted times against the dates, reported as something like "drifting 2 minutes later per week".
- **Moving averages:** a 7-day rolling mean or an exponential moving average (EMA), to show recent changes. Without dates these could still use the line order, but gaps would distort them.
- **Lag-1 autocorrelation:** whether one late day tends to follow another.

Open question: whether to keep accepting plain `HH:MM` files alongside the dated format, or require dates.

## Alternative: circular statistics

Circular statistics would remove the cutoff completely, along with its 12-hour limit.

- **Circular mean:** treat each time as an angle on a 24-hour circle, average the sine and cosine of the angles, and convert back with `atan2`.
- **Mean resultant length (R):** a value from 0 to 1 that measures how tightly the times cluster. It could replace the standard deviation as the consistency measure.

The downsides:

- For tight clusters, the result is almost the same as the current method.
- It's harder to explain and to check by hand.
- There's no simple equivalent of the median or percentiles.
- For times spread around the whole clock, it still gives an average, but that average doesn't describe anything.

Recommendation: keep the cutoff method, and consider circular statistics only if real data regularly breaks the 12-hour limit.

## Alternative: hand off to go-stats-calculator

[go-stats-calculator](https://github.com/jftuga/go-stats-calculator) already calculates most of Phases 1 and 2, plus skewness, kurtosis, MAD, trimmed mean, EMA and autocorrelation, and can print JSON with `-j`. The only clock-specific steps are the shift and the formatting, so `midnight_stats.py` could:

1. Shift the times and print the signed seconds.
2. Send them to `go-stats-calculator -j`.
3. Read the JSON and format each result as a position or a length of time (design rule 2).

This avoids writing the statistics a second time, at the cost of depending on a separate program. It suits this project if `midnight_stats.py` is meant to stay small. It doesn't suit it if the script has to run on its own with no extra tools, or if the point is to write the statistics by hand, as was done for the standard deviation.

## Known test gaps

- **Median rounding.** With whole-minute input, this can't happen. The midpoint of two whole-minute values is always a multiple of 30 seconds, so `(a+b)//2` never has a remainder. It would only matter if the input format gained seconds.
- **Non-default cutoff.** The checker's reference always uses a 12:00 cutoff, so `--cutoff` runs check `midnight_stats.py` against the correct answer, not against what that cutoff should produce. No test confirms that a custom cutoff shifts exactly the times it should.

## Recommended order

1. Phase 1: earliest, latest, range, percentiles and IQR.
2. Phase 3: comparison with a target time.
3. Phase 2: binned mode and outliers.
4. Phase 4: dated input, if the data gains dates.

Circular statistics and handing off to go-stats-calculator are separate design choices, so neither is a step in this order.
