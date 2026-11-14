
# Computes the mean, median and standard deviation of times of day that cluster around
# midnight, read from a file with one 24-hour HH:MM time per line. Times at or after a
# cutoff (12:00 by default, or an HH:MM value given before the filename) count as the
# day before, so 23:48 and 00:07 average across midnight instead of landing near noon.
# The mean and median are printed as clock times (HH:MM:SS, rounded down), and the
# sample standard deviation as a length of time (HHh MMm SSs, rounded to the nearest
# second) that is left out when the file holds only one time.
#
# Example: given a file named times.txt containing
#
#     23:50
#     23:55
#     00:05
#     00:20
#
# running "python midnight_stats.py times.txt" prints
#
#     avg: 00:02:30
#     med: 00:00:00
#     sd : 00h 13m 14s
#
# A plain average of the same four times would give 12:02:30.

import math
import sys

SECS_PER_MINUTE = 60
SECS_PER_HOUR = SECS_PER_MINUTE * 60
SECS_PER_DAY = 24 * SECS_PER_HOUR
CUTOFF_DEFAULT = SECS_PER_DAY // 2

def is_day_before(cutoff:int, seconds:int) -> bool:
    """Report whether a time belongs to the day before midnight.

    Args:
        cutoff: Seconds since midnight; times at or after this count as the day before.
        seconds: The time to classify, in seconds since midnight.

    Returns:
        True if seconds is at or after cutoff, otherwise False.
    """
    return seconds >= cutoff

def median_of_sorted(sorted_all_secs:list[int]) -> int:
    """Return the median of an already sorted list of seconds.

    Args:
        sorted_all_secs: The values to evaluate, sorted in ascending order.

    Returns:
        The middle value as an int when the length is odd, or the mean of the
        two middle values (rounded down) as an int when the length is even.

    Raises:
        ValueError: If sorted_all_secs is empty.
    """
    count = len(sorted_all_secs)
    if not count:
        raise ValueError("cannot take the median of an empty list")
    if count % 2 == 1:
        return sorted_all_secs[count // 2]
    a = sorted_all_secs[count // 2]
    b = sorted_all_secs[(count // 2) - 1]
    return (a+b)//2

def mean(all_seconds:list[int]) -> float:
    """Return the exact mean of a list of seconds.

    The result is not rounded, so variance() can measure differences from the true
    mean. Round it only when printing.

    Args:
        all_seconds: The values to average, such as shifted offsets from midnight.

    Returns:
        The mean as a float.

    Raises:
        ValueError: If all_seconds is empty.
    """
    if not all_seconds:
        raise ValueError("cannot take the mean of an empty list")
    mean_seconds = sum(all_seconds) / len(all_seconds)
    return mean_seconds

def variance(all_seconds:list[int], mean_all_seconds:float) -> float:
    """Return the sample variance of a list of seconds.

    This is the average of the squared differences from the mean, divided by
    n - 1 rather than n, because the values are treated as a sample (for example,
    some days standing in for a person's usual habit). For 2, 4, 4, 4, 5, 5, 7, 9
    with a mean of 5, it returns 32 / 7, or about 4.57.

    Args:
        all_seconds: The values to measure, such as shifted offsets from midnight.
        mean_all_seconds: The exact, unrounded mean of all_seconds.

    Returns:
        The variance in seconds squared.

    Raises:
        ValueError: If all_seconds has fewer than two values.
    """
    if len(all_seconds) <= 1:
        raise ValueError("cannot take the variance of an empty or single item list")
    diff_seconds = [(n-mean_all_seconds)**2 for n in all_seconds]
    return sum(diff_seconds) / (len(diff_seconds)-1)

def standard_deviation(all_seconds:list[int], mean_all_seconds:float) -> float:
    """Return the sample standard deviation of a list of seconds.

    This is the square root of variance(), which turns seconds squared back into
    plain seconds. It describes how far a typical value lies from the mean.

    Args:
        all_seconds: The values to measure, such as shifted offsets from midnight.
        mean_all_seconds: The exact, unrounded mean of all_seconds.

    Returns:
        The standard deviation in seconds.

    Raises:
        ValueError: If all_seconds has fewer than two values.
    """
    return math.sqrt(variance(all_seconds, mean_all_seconds))

def wall_time(input_seconds:int) -> str:
    """Convert a signed offset from midnight into a 24-hour clock time.

    Offsets wrap around the day, so negative values count back from midnight
    and values of a day or more start over.

    Args:
        input_seconds: The offset from midnight in seconds, which may be negative.

    Returns:
        The time formatted as HH:MM:SS. For example, 76 returns "00:01:16" and
        -76 returns "23:58:44".
    """
    second_of_the_day = input_seconds % SECS_PER_DAY
    hours, seconds_since_start_of_hour = divmod(second_of_the_day, SECS_PER_HOUR)
    minutes, seconds = divmod(seconds_since_start_of_hour, SECS_PER_MINUTE)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def convert_hhmm_to_secs(hhmm_str: str) -> int:
    """Convert a 24-hour HH:MM time into seconds since midnight.

    Single-digit hours and minutes are accepted, so "7:05" is the same as "07:05".
    Surrounding whitespace, including a trailing newline, is ignored.

    Args:
        hhmm_str: The time to convert, such as "23:48".

    Returns:
        Seconds since midnight. For example, "00:07" returns 420 and "23:48"
        returns 85680.

    Raises:
        ValueError: If hhmm_str is not two numbers separated by a colon, or the
            hour or minute is out of range.
    """
    hhmm_str = hhmm_str.strip()
    parts = hhmm_str.split(":")
    if len(parts) != 2 or not all(part.isdecimal() for part in parts):
        raise ValueError(f"not an HH:MM time: {hhmm_str!r}")
    hh = int(parts[0])
    mm = int(parts[1])
    if hh > 23:
        raise ValueError(f"hour must be 00 to 23: {hhmm_str!r}")
    if mm > 59:
        raise ValueError(f"minute must be 00 to 59: {hhmm_str!r}")

    secs = hh * SECS_PER_HOUR
    secs += (mm * SECS_PER_MINUTE)
    return secs

def length_of_time(input_seconds:int) -> str:
    """Format a length of time, as opposed to a time of day.

    Unlike wall_time(), this does not wrap around the day, so 25 hours stays 25h.

    Args:
        input_seconds: The length of time in whole seconds, zero or more.

    Returns:
        The length formatted as HHh MMm SSs. For example, 754 returns "00h 12m 34s"
        and 3725 returns "01h 02m 05s".
    """
    hours, seconds_since_start_of_hour = divmod(input_seconds, SECS_PER_HOUR)
    minutes, seconds = divmod(seconds_since_start_of_hour, SECS_PER_MINUTE)
    return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

def read_times(fname: str) -> list[int]:
    """Read one HH:MM time per line from a file, skipping blank lines.

    Args:
        fname: The path of the file to read.

    Returns:
        Each time as seconds since midnight, in file order. The list is empty if
        the file holds no times.

    Raises:
        ValueError: If a line is not a valid HH:MM time. The message names the
            file and the line number.
        OSError: If the file can't be opened or read.
    """
    all_seconds = []
    with open(fname) as fp:
        for line_number, line in enumerate(fp, start=1):
            if not line.strip():
                continue
            try:
                all_seconds.append(convert_hhmm_to_secs(line))
            except ValueError as err:
                raise ValueError(f"{fname}, line {line_number}: {err}") from err
    return all_seconds


def usage() -> None:
    """Print the command-line usage message to stdout.

    It goes to stdout both when help was requested and when the arguments were
    wrong, so "midnight_stats.py -h | less" works. A caller tells the two apart by
    the exit status that main() returns.
    """
    default_cutoff = wall_time(CUTOFF_DEFAULT)[:5]  # drop ":SS" to show HH:MM
    print(f"""usage: midnight_stats.py [CUTOFF] FILE

Print the mean, median and standard deviation of the times of day in FILE.
The standard deviation needs at least two times.

  CUTOFF  HH:MM; times at or after this count as before midnight
          (default: {default_cutoff})
  FILE    text file with one 24-hour HH:MM time per line""")


def main() -> int:
    """Read the times from the file named on the command line and print their statistics.

    Prints the mean and median as clock times, then the standard deviation as a
    length of time. The standard deviation line is skipped when the file holds only
    one time.

    Returns:
        The exit status: 0 on success or when help was shown, 1 for a wrong
        number of arguments, an invalid cutoff, a file that can't be read, an
        invalid line or an empty file. Each error prints one message to stderr.
    """
    if len(sys.argv) == 1 or "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
        usage()
        return 0

    if len(sys.argv) != 2 and len(sys.argv) != 3:
        usage()
        return 1

    fname = sys.argv[-1]
    try:
        cutoff = convert_hhmm_to_secs(sys.argv[1]) if len(sys.argv) == 3 else CUTOFF_DEFAULT
    except ValueError as err:
        print(f"Error: cutoff: {err}", file=sys.stderr)
        return 1

    try:
        all_seconds = read_times(fname)
    except (ValueError, OSError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    if not all_seconds:
        print(f"Error: no times in {fname}", file=sys.stderr)
        return 1

    # Turn seconds since midnight into signed offsets from midnight, so all the times
    # form one continuous range: negative before midnight, positive after. Each value
    # has a day subtracted if it's at or after the cutoff, and is kept as is otherwise;
    # the "A if condition else B" before the "for" keeps every value. With the default
    # 12:00 cutoff, [85800, 600] (23:50, 00:10) becomes [-600, 600].
    # All statistics below are calculated from offsets, never from all_seconds.
    offsets = [secs - SECS_PER_DAY if is_day_before(cutoff, secs) else secs for secs in all_seconds]
    mean_seconds = mean(offsets)
    print(f"avg: {wall_time(math.floor(mean_seconds))}")

    sorted_offsets = sorted(offsets)
    median = median_of_sorted(sorted_offsets)
    print(f"med: {wall_time(median)}")

    if len(offsets) <= 1:
        return 0
    sd_secs = standard_deviation(offsets,mean_seconds)
    sd = length_of_time(round(sd_secs))
    print(f"sd : {sd}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
