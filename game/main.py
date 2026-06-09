#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║          K A N I S T R A   A B Y S S        ║
║      A Roguelike of Darkness and Glory       ║
╚══════════════════════════════════════════════╝

Run with:   python game/main.py
Controls:   WASD/Arrows=Move  1-4=Skills  i=Inventory
            g=Pickup  >=Descend  TAB=Target  q=Quit
"""
from __future__ import annotations
import sys
import os

# Ensure the game directory is importable regardless of cwd
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)


def _check_terminal_size() -> bool:
    """Warn if terminal is too small."""
    try:
        import shutil
        cols, rows = shutil.get_terminal_size(fallback=(80, 24))
        if cols < 84 or rows < 30:
            print(f"\n⚠  Terminal too small! Current: {cols}x{rows}")
            print("   Please resize to at least 84 columns × 30 rows for best experience.")
            print("   (Recommended: 120×50 or larger)")
            ans = input("   Continue anyway? [y/N]: ").strip().lower()
            return ans == 'y'
    except Exception:
        pass
    return True


def _install_colorama() -> None:
    """Try to install colorama if not present (optional)."""
    try:
        import colorama  # noqa: F401
    except ImportError:
        try:
            import subprocess
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "colorama", "-q"],
                check=False, capture_output=True
            )
        except Exception:
            pass


def main() -> None:
    """Main entry point."""
    # On Windows, try to install windows-curses if needed
    if sys.platform == "win32":
        try:
            import curses  # noqa: F401
        except ImportError:
            try:
                import subprocess
                print("Installing windows-curses...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "windows-curses", "-q"],
                    check=True
                )
            except Exception as e:
                print(f"Could not install windows-curses: {e}")
                print("Please run: pip install windows-curses")
                sys.exit(1)

    _install_colorama()

    if not _check_terminal_size():
        print("Aborted.")
        return

    try:
        import curses
        from engine import run_game
        curses.wrapper(run_game)
    except KeyboardInterrupt:
        print("\nGame interrupted. Farewell, brave adventurer!")
    except curses.error as e:
        print(f"\nCurses error: {e}")
        print("Try resizing your terminal to at least 84x30 and running again.")
        sys.exit(1)
    except Exception as e:
        # Clean up curses state if it was partially initialised
        try:
            import curses as _c
            _c.endwin()
        except Exception:
            pass
        import traceback
        print(f"\nFatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Ensure terminal is restored
        try:
            import curses as _c
            _c.endwin()
        except Exception:
            pass


if __name__ == "__main__":
    main()
