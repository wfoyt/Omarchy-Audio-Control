"""Run the real Quickshell I/O plugin in a disposable configuration."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='audio control %-tests-') as folder:
    config = Path(folder)
    for name in ('Artwork.qml', 'Artwork.js', 'artwork_loader.py', 'preview.png'):
        shutil.copy2(ROOT / name, config / name)
    shutil.copy2(ROOT / 'docs/images/now-playing.png', config / 'other.png')
    os.mkfifo(config / 'pipe.png')
    shutil.copy2(ROOT / 'tests/fixtures/cover.jpg', config / 'cover.jpg')
    for name in ('Ui', 'Commons'):
        shutil.copytree(Path('/usr/share/omarchy/shell') / name, config / name)
    for name in ('MusicWidget.qml', 'Playback.js', 'Service.qml', 'MediaModel.js'):
        shutil.copy2(ROOT / name, config / name)
    shutil.copytree(ROOT / 'i18n', config / 'i18n')
    source = (ROOT / 'tests/integration/shell.qml').read_text()
    source = source.replace('"../.." as Plugin', '"." as Plugin').replace('../../preview.png', 'preview.png').replace('../../docs/images/now-playing.png', 'other.png')
    (config / 'shell.qml').write_text(source)
    result = subprocess.run(['quickshell', '-p', str(config / 'shell.qml'), '--no-color'],
                            env={**os.environ, 'QT_QPA_PLATFORM': 'wayland'},
                            capture_output=True, text=True, timeout=12)
    print(result.stdout, result.stderr)
    if result.returncode or 'PASS:' not in result.stdout + result.stderr or 'FAIL:' in result.stdout + result.stderr or ' ERROR:' in result.stdout + result.stderr:
        raise SystemExit(1)

    # A deliberately stalled helper exercises the QML watchdog, independently
    # of the helper's own three-second deadline.
    (config / 'artwork_loader.py').write_text('import time; time.sleep(30)')
    (config / 'shell.qml').write_text('''
import QtQuick
import Quickshell
import "." as Plugin
ShellRoot {
  Item {
    Plugin.Artwork { id: art; url: "file:///unused.png" }
    Timer {
      interval: 4100; running: true
      onTriggered: {
        if (art.loading || art.source !== "") { console.error("FAIL: watchdog"); Qt.exit(1) }
        console.log("PASS: stalled helper killed; fallback retained")
        Qt.quit()
      }
    }
  }
}
''')
    result = subprocess.run(['quickshell', '-p', str(config / 'shell.qml'), '--no-color'],
                            env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen'},
                            capture_output=True, text=True, timeout=8)
    print(result.stdout, result.stderr)
    if result.returncode or 'PASS:' not in result.stdout + result.stderr or 'FAIL:' in result.stdout + result.stderr or ' ERROR:' in result.stdout + result.stderr:
        raise SystemExit(1)

    # Cancellation must discard an already running reader, rather than only
    # handling rapid changes before the debounce timer has started it.
    (config / 'artwork_loader.py').write_text('import time; time.sleep(0.7); print("data:image/png;base64,AAAA", end="")')
    (config / 'shell.qml').write_text('''
import QtQuick
import Quickshell
import "." as Plugin
ShellRoot {
  Item {
    Plugin.Artwork { id: art; url: "file:///unused.png" }
    Timer {
      interval: 350; running: true
      onTriggered: art.url = "https://example.invalid/blocked"
    }
    Timer {
      interval: 1200; running: true
      onTriggered: {
        if (art.loading || art.source !== "") { console.error("FAIL: obsolete reader result"); Qt.exit(1) }
        console.log("PASS: running reader cancelled and obsolete output discarded")
        Qt.quit()
      }
    }
  }
}
''')
    result = subprocess.run(['quickshell', '-p', str(config / 'shell.qml'), '--no-color'],
                            env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen'},
                            capture_output=True, text=True, timeout=5)
    print(result.stdout, result.stderr)
    if result.returncode or 'PASS:' not in result.stdout + result.stderr or 'FAIL:' in result.stdout + result.stderr or ' ERROR:' in result.stdout + result.stderr:
        raise SystemExit(1)

    # Missing helper: a packaging/runtime failure must leave a usable fallback.
    (config / 'artwork_loader.py').unlink()
    source = (config / 'shell.qml').read_text().replace('interval: 350; running: true', 'interval: 350; running: false')
    source = source.replace('PASS: running reader cancelled and obsolete output discarded', 'PASS: missing helper fails to fallback')
    (config / 'shell.qml').write_text(source)
    result = subprocess.run(['quickshell', '-p', str(config / 'shell.qml'), '--no-color'],
                            env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen'},
                            capture_output=True, text=True, timeout=5)
    print(result.stdout, result.stderr)
    if result.returncode or 'PASS:' not in result.stdout + result.stderr or 'FAIL:' in result.stdout + result.stderr or ' ERROR:' in result.stdout + result.stderr:
        raise SystemExit(1)
