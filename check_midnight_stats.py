# Compares midnight_stats.py output against an independent calculation for each
# test*.txt file of HH:MM times, checking the mean, median and standard deviation.
# The reference treats any time at or after noon as belonging to the previous day,
# which assumes every value lies within 12 hours of midnight. It uses the datetime,
# statistics and time modules instead of midnight_stats.py's own helpers, so a shared
# bug can't hide.

import argparse
import datetime
import math
import pathlib
import statistics
import subprocess
import sys
import time

DAY = 86400
NOON = DAY // 2
NO_SD = "-"


def clock(seconds: int) -> str:
    """Format a signed offset from midnight as HH:MM:SS.

    Args:
        seconds: Offset from midnight, which may be negative.

    Returns:
        The wall-clock time as HH:MM:SS.
    """
    return time.strftime("%H:%M:%S", time.gmtime(seconds % DAY))


def duration(seconds: float) -> str:
    """Format a length of time, rounded to the nearest second, as HHh MMm SSs.

    Only valid below 24 hours. A standard deviation of times that all lie within one
    24-hour window never reaches that.

    Args:
        seconds: The length of time in seconds.

    Returns:
        The length of time as HHh MMm SSs, such as "00h 12m 34s".
    """
    return time.strftime("%Hh %Mm %Ss", time.gmtime(round(seconds)))


def to_seconds(hhmm: str) -> int:
    """Convert an HH:MM string into seconds since midnight.

    Args:
        hhmm: A 24-hour time such as "23:48".

    Returns:
        Seconds since midnight.
    """
    t = datetime.datetime.strptime(hhmm.strip(), "%H:%M")
    return t.hour * 3600 + t.minute * 60


def expected(values: list[int]) -> tuple[str, str, str]:
    """Compute the reference mean, median and sample standard deviation.

    The mean and median are rounded down to whole seconds. The standard deviation
    divides by n - 1 and is rounded to the nearest second.

    Args:
        values: Seconds since midnight, one per input line.

    Returns:
        The (mean, median, standard deviation). The mean and median are HH:MM:SS
        strings. The standard deviation is an HHh MMm SSs string, or NO_SD when there
        are fewer than two values.
    """
    shifted = [v - DAY if v >= NOON else v for v in values]
    mean = math.floor(sum(shifted) / len(shifted))
    median = math.floor(statistics.median(shifted))
    sd = duration(statistics.stdev(shifted)) if len(shifted) >= 2 else NO_SD
    return clock(mean), clock(median), sd


def actual(script: pathlib.Path, path: pathlib.Path, cutoff: str | None) -> tuple[str, str, str]:
    """Run midnight_stats.py on one file and parse its avg, med and sd lines.

    Args:
        script: Path to midnight_stats.py.
        path: Path to the input file.
        cutoff: An HH:MM cutoff to pass to midnight_stats.py, or None to use its default.

    Returns:
        The (avg, med, sd) values that midnight_stats.py printed, with NO_SD for sd
        when it printed no sd line.

    Raises:
        subprocess.CalledProcessError: If midnight_stats.py exits with an error.
    """
    cutoff_args = [cutoff] if cutoff else []
    out = subprocess.run([sys.executable, "-B", str(script), *cutoff_args, str(path)], capture_output=True, text=True, check=True).stdout
    lines = {label.strip(): value for label, value in (line.split(": ", 1) for line in out.splitlines() if ": " in line)}
    return lines["avg"], lines["med"], lines.get("sd", NO_SD)


def parse_args() -> argparse.Namespace:
    """Parse the command line.

    Returns:
        The parsed arguments, with folder and cutoff attributes.
    """
    parser = argparse.ArgumentParser(description="Check midnight_stats.py against an independent calculation for every test*.txt file.")
    parser.add_argument("folder", nargs="?", type=pathlib.Path, default=pathlib.Path(__file__).parent, help="folder holding midnight_stats.py and test*.txt (default: this script's folder)")
    parser.add_argument("--cutoff", help="HH:MM cutoff to pass to midnight_stats.py (default: midnight_stats.py's own default)")
    return parser.parse_args()


def main() -> int:
    """Check every test*.txt file and print one PASS, FAIL or ERROR row per file.

    Returns:
        The exit status: 0 if every file passed, 1 if any file failed or errored,
        or if no test*.txt files were found.
    """
    args = parse_args()
    script = args.folder / "midnight_stats.py"
    paths = sorted(args.folder.glob("test*.txt"))
    if not paths:
        print(f"Error: no test*.txt files in {args.folder}", file=sys.stderr)
        return 1

    print(f"cutoff: {args.cutoff or 'default'}")
    print(f"{'file':<10} {'avg got':<8} {'avg want':<8} {'med got':<8} {'med want':<8} {'sd got':<11} {'sd want':<11} result")
    all_passed = True
    for path in paths:
        values = [to_seconds(line) for line in path.read_text().splitlines()]
        want = expected(values)
        try:
            got = actual(script, path, args.cutoff)
        except subprocess.CalledProcessError as err:
            last_line = (err.stderr.strip().splitlines() or ["no error output"])[-1].removeprefix("Error: ")
            print(f"{path.name:<10} ERROR: {last_line}")
            all_passed = False
            continue
        result = "PASS" if got == want else "FAIL"
        all_passed = all_passed and result == "PASS"
        print(f"{path.name:<10} {got[0]:<8} {want[0]:<8} {got[1]:<8} {want[1]:<8} {got[2]:<11} {want[2]:<11} {result}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
