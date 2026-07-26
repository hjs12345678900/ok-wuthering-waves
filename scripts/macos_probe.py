#!/usr/bin/env python3
"""Validate macOS permissions, game-window discovery, capture, and input."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load_ok_script():
    try:
        from ok.platform.macos.helper import MacOSHelper, MacOSHelperError
        return MacOSHelper, MacOSHelperError
    except ImportError:
        sibling = Path(__file__).resolve().parents[2] / "ok-script"
        if sibling.is_dir():
            sys.path.insert(0, str(sibling))
            from ok.platform.macos.helper import MacOSHelper, MacOSHelperError
            return MacOSHelper, MacOSHelperError
        raise


MacOSHelper, MacOSHelperError = _load_ok_script()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Probe the native macOS OK-WW capture and input backend."
    )
    parser.add_argument(
        "--prompt-permissions",
        action="store_true",
        help="ask macOS for Screen Recording and Accessibility access",
    )
    parser.add_argument("--window-id", type=int, help="use a specific CG/SC window id")
    parser.add_argument(
        "--owner",
        action="append",
        default=["Wuthering Waves", "鸣潮"],
        help="accepted owner application name (repeatable)",
    )
    parser.add_argument("--snapshot", type=Path, help="write one window PNG")
    parser.add_argument("--key", help="send one key press after activating the game")
    parser.add_argument(
        "--click-point",
        nargs=2,
        metavar=("X", "Y"),
        type=float,
        help="click a point relative to the window, in macOS points",
    )
    parser.add_argument(
        "--scroll",
        nargs=3,
        metavar=("X", "Y", "AMOUNT"),
        type=float,
        help=(
            "scroll at a point relative to the window; AMOUNT is an integer "
            "Quartz line-wheel delta"
        ),
    )
    parser.add_argument(
        "--swipe",
        nargs=5,
        metavar=("X1", "Y1", "X2", "Y2", "MILLISECONDS"),
        type=float,
        help="drag between two window-relative points using the left button",
    )
    return parser.parse_args()


def select_window(windows, window_id, owners):
    if window_id:
        return next(
            (window for window in windows if window.get("windowID") == window_id),
            None,
        )
    accepted = {owner.casefold() for owner in owners}
    candidates = [
        window
        for window in windows
        if str(window.get("ownerName") or "").casefold() in accepted
        and float(window.get("width") or 0) > 100
        and float(window.get("height") or 0) > 100
    ]
    candidates.sort(
        key=lambda item: (
            bool(item.get("active")),
            bool(item.get("onScreen")),
            float(item.get("width", 0)) * float(item.get("height", 0)),
        ),
        reverse=True,
    )
    return candidates[0] if candidates else None


def main():
    args = parse_args()
    helper = MacOSHelper()
    permissions = helper.permissions(prompt=args.prompt_permissions)
    print("Permissions:", json.dumps(permissions, ensure_ascii=False))
    if not permissions.get("screenRecording"):
        print(
            "Screen Recording is not authorized. Grant it in System Settings, "
            "then restart this terminal/application.",
            file=sys.stderr,
        )
        return 2

    windows = helper.list_windows(on_screen_only=False)
    selected = select_window(windows, args.window_id, args.owner)
    if selected is None:
        visible = [
            {
                "windowID": item.get("windowID"),
                "ownerName": item.get("ownerName"),
                "title": item.get("title"),
                "size": [item.get("width"), item.get("height")],
            }
            for item in windows
            if item.get("onScreen")
        ]
        print("No matching game window. Visible windows:")
        print(json.dumps(visible, ensure_ascii=False, indent=2))
        return 3

    print("Selected window:")
    print(json.dumps(selected, ensure_ascii=False, indent=2))
    window_id = selected["windowID"]

    if args.snapshot:
        output = args.snapshot.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        helper.run("snapshot", window_id, output, timeout=15)
        print(f"Snapshot: {output}")

    if args.key or args.click_point or args.scroll or args.swipe:
        if not permissions.get("accessibility"):
            print(
                "Accessibility is not authorized; input tests were skipped.",
                file=sys.stderr,
            )
            return 4
        helper.run("activate", selected["pid"])
        if args.key:
            helper.run("key", "press", args.key, 20)
            print(f"Key sent: {args.key}")
        if args.click_point:
            x = float(selected["x"]) + args.click_point[0]
            y = float(selected["y"]) + args.click_point[1]
            helper.run("mouse", "click", x, y, "left", 20)
            print(f"Click sent at global point: {x}, {y}")
        if args.scroll:
            x = float(selected["x"]) + args.scroll[0]
            y = float(selected["y"]) + args.scroll[1]
            amount = int(args.scroll[2])
            helper.run("mouse", "scroll", x, y, amount)
            print(
                f"Scroll sent at global point: {x}, {y}; "
                f"amount: {amount}"
            )
        if args.swipe:
            x1 = float(selected["x"]) + args.swipe[0]
            y1 = float(selected["y"]) + args.swipe[1]
            x2 = float(selected["x"]) + args.swipe[2]
            y2 = float(selected["y"]) + args.swipe[3]
            milliseconds = int(args.swipe[4])
            helper.run(
                "mouse",
                "swipe",
                x1,
                y1,
                x2,
                y2,
                milliseconds,
            )
            print(
                f"Swipe sent from ({x1}, {y1}) to ({x2}, {y2}); "
                f"duration: {milliseconds} ms"
            )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MacOSHelperError as exc:
        print(f"Probe failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
