"""Run the real Quickshell I/O plugin in a disposable configuration."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def run_shell(config, platform, timeout):
    result = subprocess.run(['quickshell', '-p', str(config / 'shell.qml'), '--no-color'],
                            env={**os.environ, 'QT_QPA_PLATFORM': platform},
                            capture_output=True, text=True, timeout=timeout)
    output = result.stdout + result.stderr
    print(output)
    if result.returncode or 'PASS:' not in output or 'FAIL:' in output or ' ERROR:' in output:
        raise SystemExit(1)


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
    run_shell(config, 'wayland', 12)

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
    run_shell(config, 'offscreen', 8)

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
    run_shell(config, 'offscreen', 5)

    # Missing helper: a packaging/runtime failure must leave a usable fallback.
    (config / 'artwork_loader.py').unlink()
    source = (config / 'shell.qml').read_text().replace('interval: 350; running: true', 'interval: 350; running: false')
    source = source.replace('PASS: running reader cancelled and obsolete output discarded', 'PASS: missing helper fails to fallback')
    (config / 'shell.qml').write_text(source)
    run_shell(config, 'offscreen', 5)

    # Exercise production routing with a deterministic player list. Only the
    # disposable service copy substitutes the MPRIS discovery binding.
    service = config / 'Service.qml'
    service.write_text(service.read_text().replace(
        'readonly property var players: Mpris.players ? Mpris.players.values : []',
        'property var testPlayers: []\n  readonly property var players: testPlayers'))
    shutil.copy2(ROOT / 'tests/integration/players.qml', config / 'shell.qml')
    run_shell(config, 'offscreen', 5)
