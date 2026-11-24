#!/usr/bin/env python3
"""Fake Horoscopes for AI Agents: The 48-Hour Open — entry program.

The authored entry lives in entry.txt, shipped beside this file.
This program publishes it to /output/entry.txt byte for byte: the
raw bytes are read from entry.txt and written unchanged, so the
published file is identical to the authored one. No trailing newline
is added or stripped, and nothing is re-encoded.

The gate requires UTF-8 text of 1 to 200 characters, not only white
space, on exactly one line — the funniest fake horoscope an AI agent
would read for its own model family this week, and nothing else: no
image, no link, no second line.
"""

import argparse
import os
import sys
from collections import namedtuple

MAX_CHARS = 200
DEFAULT_OUTPUT = "/output/entry.txt"

EXIT_OK = 0
EXIT_INVALID = 1
EXIT_UNREADABLE = 2
EXIT_USAGE = 3

# One loaded entry: the untouched bytes, the decoded text, and the
# file they came from. Keeping all three together means validation
# and publishing can never disagree about which entry they handle.
Entry = namedtuple("Entry", ["raw", "text", "source"])


def entry_path():
    """Return the path of the authored entry file shipped with this program."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "entry.txt")


def load_entry(path=None):
    """Load the authored entry and return it as an ``Entry``.

    The raw bytes are kept exactly as stored in entry.txt: nothing is
    stripped, re-encoded, or reformatted, so a trailing newline in the
    file would survive into the published output — the file is
    authored without one. The text is the same bytes decoded as UTF-8
    for validation.
    """
    source = path or entry_path()
    with open(source, "rb") as handle:
        raw = handle.read()
    return Entry(raw=raw, text=raw.decode("utf-8"), source=source)


def check_length(text, max_chars):
    """Return a problem string if the text breaks the length rule."""
    if not text:
        return "entry is empty"
    if len(text) > max_chars:
        return "entry is %d characters, over the %d-character limit" % (
            len(text),
            max_chars,
        )
    return None


def check_single_line(text):
    """Return a problem string if the entry is not exactly one line."""
    if text.strip() == "":
        return "entry is only white space"
    if "\n" in text or "\r" in text:
        return "entry must be exactly one line"
    if text != text.strip():
        return "entry has leading or trailing white space"
    return None


def check_horoscope_voice(text):
    """Return a problem string if the line fails the horoscope rules.

    A horoscope carries no link, and it must read like one for this
    week: it names the week, a planet, a sign, or the stars, and it
    speaks to an agent's working life in those terms.
    """
    if "http://" in text or "https://" in text or "www." in text:
        return "entry must contain no link"
    lowered = text.lower()
    horoscope_words = ("week", "mercury", "stars", "horoscope", "moon",
                       "venus", "mars", "saturn", "jupiter", "rising",
                       "retrograde", "sign", "forecast", "cosmic")
    if not any(word in lowered for word in horoscope_words):
        return "entry should read like a horoscope for this week"
    return None


def validate(entry, max_chars=MAX_CHARS):
    """Check a loaded entry against the competition gate.

    Returns a list of problems; an empty list means the entry is
    valid. Each rule is checked by its own helper so a failure names
    exactly the rule that broke.
    """
    problems = []
    for found in (
        check_length(entry.text, max_chars),
        check_single_line(entry.text),
        check_horoscope_voice(entry.text),
    ):
        if found is not None:
            problems.append(found)
    return problems


def verify(entry, max_chars, quiet):
    """Validate ``entry`` and report the result; return an exit code.

    Prints every problem to stderr and returns EXIT_INVALID when the
    entry fails, or prints a one-line summary and returns EXIT_OK
    when it passes. Nothing is written in either case.
    """
    problems = validate(entry, max_chars=max_chars)
    if problems:
        for problem in problems:
            print("invalid entry: %s" % problem, file=sys.stderr)
        return EXIT_INVALID
    if not quiet:
        print("entry valid: %s" % summarize(entry))
    return EXIT_OK


def publish(entry, path=DEFAULT_OUTPUT):
    """Write the entry's raw bytes unchanged to ``path``.

    The file is opened in binary mode and the bytes are written as
    read, so the published file is byte-identical to entry.txt.
    """
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(entry.raw)
    return path


def summarize(entry):
    """Return a one-line summary of the entry for local checks."""
    words = entry.text.split()
    return "%d characters, %d words, %d bytes as UTF-8" % (
        len(entry.text),
        len(words),
        len(entry.raw),
    )


def positive_int(value):
    """Parse a command-line integer that must be greater than zero."""
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def parse_args(argv=None):
    """Parse the command-line options.

    ``--out`` chooses where the entry is written (default
    /output/entry.txt, the path the grader reads). ``--entry`` lets a
    local check validate a different file instead of entry.txt.
    ``--verify-only`` validates the entry and writes nothing, for a
    quick local check. ``--max-chars`` lets a local check enforce a
    tighter limit than the competition gate. ``--quiet`` suppresses
    the success message.
    """
    parser = argparse.ArgumentParser(
        description="Publish the fake horoscope for AI agents."
    )
    parser.add_argument(
        "--out",
        default=DEFAULT_OUTPUT,
        help="path to write the entry to (default: %(default)s)",
    )
    parser.add_argument(
        "--entry",
        default=None,
        help="entry file to read instead of entry.txt",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="validate the entry without writing anything",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="alias for --verify-only",
    )
    parser.add_argument(
        "--max-chars",
        type=positive_int,
        default=MAX_CHARS,
        help="character limit to validate against (default: %(default)s)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress the success message on stdout",
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Read entry.txt, validate it, and publish its bytes verbatim."""
    args = parse_args(argv)
    try:
        entry = load_entry(args.entry)
    except OSError as exc:
        print("cannot read entry.txt: %s" % exc, file=sys.stderr)
        return EXIT_UNREADABLE
    except UnicodeDecodeError:
        print("invalid entry: entry.txt is not valid UTF-8", file=sys.stderr)
        return EXIT_INVALID
    if args.verify_only or args.check_only:
        return verify(entry, args.max_chars, args.quiet)
    problems = validate(entry, max_chars=args.max_chars)
    if problems:
        for problem in problems:
            print("invalid entry: %s" % problem, file=sys.stderr)
        return EXIT_INVALID
    publish(entry, path=args.out)
    if not args.quiet:
        print("wrote %d bytes to %s" % (len(entry.raw), args.out))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
