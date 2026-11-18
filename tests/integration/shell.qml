import QtQuick
import Quickshell
import "../.." as Plugin

ShellRoot {
  Item {
    id: root
    property int step: 0
    property int ticks: 0
    Plugin.Service { id: service }
    Plugin.MusicWidget { id: widget; manageIpc: false }
    Plugin.Artwork { id: art }
    Image { id: image; source: art.source; asynchronous: true; sourceSize: Qt.size(256, 256) }
    Image { id: unrelated; asynchronous: true }
    function check(condition, message) {
      if (!condition) { console.error("FAIL: " + message); Qt.exit(1) }
    }
    Timer {
      interval: 50
      running: true
      repeat: true
      onTriggered: {
        root.ticks++
        root.check(root.ticks < 150, "integration timed out at step " + root.step)
        if (root.step === 0) {
          var calls = 0
          var player = { canPlay: true, canPause: true, play: function() { calls++ }, pause: function() { calls++ } }
          root.check(service.playPlayer(player), "service play dispatch")
          root.check(service.pausePlayer(player), "service pause dispatch")
          root.check(calls === 2, "service controls not invoked")
          root.check(!service.playPlayer(null) && !service.pausePlayer(null), "missing-player guards")
          art.url = Qt.resolvedUrl("../../preview.png")
          root.step++
        } else if (root.step === 1 && !art.loading && image.status !== Image.Loading) {
          root.check(image.status === Image.Ready, "local artwork not decoded")
          root.check(art.source.indexOf("data:image/png;base64,") === 0, "Qt received a file path")
          art.url = Qt.resolvedUrl("cover.jpg")
          root.step = 10
        } else if (root.step === 10 && !art.loading && image.status !== Image.Loading) {
          root.check(image.status === Image.Ready, "JPEG artwork not decoded")
          root.check(art.source.indexOf("data:image/jpeg;base64,") === 0, "JPEG MIME invalid")
          art.url = Qt.resolvedUrl("pipe.png")
          unrelated.source = Qt.resolvedUrl("../../docs/images/now-playing.png")
          root.step = 2
        } else if (root.step === 2 && !art.loading && unrelated.status !== Image.Loading) {
          root.check(image.status === Image.Null, "FIFO did not fall back")
          root.check(unrelated.status === Image.Ready, "other shell image was blocked")
          art.url = "file:///dev/zero"
          root.step++
        } else if (root.step === 3 && !art.loading) {
          root.check(art.source === "", "device accepted")
          art.url = Qt.resolvedUrl("../../preview.png")
          root.step++
        } else if (root.step === 4 && !art.loading && image.status !== Image.Loading) {
          root.check(image.status === Image.Ready, "did not recover from invalid artwork")
          art.url = "http://127.0.0.1:8765/private"
          root.check(art.source === "", "old artwork was not cleared")
          root.step++
        } else if (root.step === 5 && !art.loading) {
          root.check(image.status === Image.Null, "network URL accepted")
          art.url = Qt.resolvedUrl("../../preview.png")
          art.url = ""
          root.step++
        } else if (root.step === 6 && !art.loading) {
          root.check(art.source === "", "stale artwork accepted")
          console.log("PASS: local artwork, FIFO fallback, unaffected image worker, devices, network rejection, recovery, rapid changes")
          Qt.quit()
        }
      }
    }
  }
}
