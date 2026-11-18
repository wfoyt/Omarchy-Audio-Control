# Artwork safety fix and validation

The follow-up on [submission #15167](https://github.com/omacom/omarchy-plugin-marketplace/issues/15167#issuecomment-6991768572) correctly identified that filtering URL schemes alone does not protect Qt's shared image worker from blocking local files.

## Implementation

- Player paths never reach `Image.source`. `Artwork.qml` launches a fixed Python helper with an argument array, without a shell. Qt receives only bounded PNG/JPEG data URLs.
- The helper accepts hostless absolute local file URLs, validates URL decoding, and rejects network schemes, authorities, query/fragment suffixes, and control characters.
- Linux `O_PATH` pins an inode without opening it for I/O. `fstat` must identify a nonempty regular file no larger than 8 MiB. The helper reopens the pinned descriptor through `/proc/self/fd`, not the original pathname. Path replacement cannot switch the read to a FIFO or device after validation.
- The read has an 8 MiB limit plus one overflow-detection byte. Supported raster headers must declare at most 8192 pixels per side and 16 megapixels. SVG and other formats use the fallback. Qt performs the final image decode with a 256-pixel source size; malformed images use the fallback.
- A three-second helper alarm and independent 3.5-second QML watchdog limit stalls outside the shell. Only one reader runs at a time. URL changes clear artwork immediately and discard obsolete results. The widget requests artwork only while the popup is open. A 100 ms debounce limits rapid metadata changes. No artwork cache is written to disk.
- Visible metadata uses plain text. Metadata sent to the shared shell OSD is length-limited and has markup delimiters neutralized for shells whose OSD uses automatic text detection.

Python uses only its standard library. `/usr/bin/python3`, Linux `/proc`, and the current Omarchy `Commons.Translations` API are required for the corresponding features. Missing artwork support fails to the music-note fallback.

## Checks performed

Tested with Omarchy 4.5.0-3, Quickshell 0.3.2, and Qt 6.12.0:

- `node --test tests/*.test.js`: six tests passed, covering URL gates, previous/restart, state-dependent playback capabilities, missing controls, and markup-shaped OSD metadata.
- `python -B -m unittest discover -s tests -v`: ten tests passed, covering real PNG/JPEG input, encoded filenames, FIFOs, Unix sockets, devices, directories, symlinks, pathname replacement, oversized/growing files, malformed URLs and headers, dimension limits, missing files, and non-image input.
- `python -B tests/run_integration.py`: passed with the actual Quickshell I/O plugin. Loads the full widget and service against copies of the installed Omarchy components in a disposable Wayland configuration. Verifies PNG/JPEG decoding, FIFO/device/network fallback, another image loading independently, recovery, rapid changes, service play/pause dispatch, and termination of a deliberately stalled helper, cancellation of an already-running reader, rejection of obsolete output, and fallback when the helper is missing. Also tests a plugin path containing spaces and a percent sign. A separate run uses two simulated players to verify source selection, playback routing, and handling of a player that disappears.
- `omarchy plugin validate .` and `git diff --check`: passed.
- Local analysis of the working tree with the marketplace's `isSecurityScanPath`, `detectUnsafeRemoteExecution`, and `detectElevatedCapabilities` implementations: eight runtime/documentation files scanned, no findings or review capabilities. This is a local static precheck, not an official commit-bound marketplace scan.

## Guidelines reviewed

Reviewed the installed Omarchy skill's plugin UI safety, native UI/motion, and translation guidance, plus the marketplace [submission guide](https://github.com/omacom/omarchy-plugin-marketplace/blob/main/SUBMISSION.md) and [security policy](https://github.com/omacom/omarchy-plugin-marketplace/blob/main/SECURITY.md).

The root manifest uses the existing nonreserved plugin ID, retains clone compatibility and entry points, and is versioned 1.0.1. The repository has a root license, preview, and README describing installation, updates, removal, dependencies, and artwork limits. UI strings have an English catalog with Omarchy language fallback, and directional playback glyphs follow RTL layout. No installed desktop configuration or packaged Omarchy files were modified.

The official marketplace validation and automated security baseline passed for published commit `63c196e`. The marketplace subsequently published the plugin and closed the submission. These checks cover the reported bug and related regressions; they cannot prove that all possible defects are absent or replace the marketplace's review.
