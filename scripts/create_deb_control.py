"""Generate a Debian package control file for resolve-rpc.

Usage:
    python scripts/create_deb_control.py <version> <output_path>

Example:
    python scripts/create_deb_control.py 1.0.42 pkg/DEBIAN/control
"""

import sys


def generate_control(version: str) -> str:
    """Return the content of a valid Debian control file.

    Args:
        version: Package version string (e.g. ``"1.0.42"``).

    Returns:
        Formatted control file content.
    """
    return (
        "Package: resolve-rpc\n"
        f"Version: {version}\n"
        "Architecture: amd64\n"
        "Maintainer: DaVinciRPC <noreply@github.com>\n"
        "Description: DaVinci Resolve Discord Rich Presence\n"
        " Displays the active editing page, project name, and\n"
        " elapsed session time in Discord Rich Presence.\n"
    )


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <version> <output_path>", file=sys.stderr)
        sys.exit(1)

    version, output_path = sys.argv[1], sys.argv[2]
    content = generate_control(version)

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(content)

    print(f"Written: {output_path}")


if __name__ == "__main__":
    main()
