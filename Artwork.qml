import QtQuick
import Quickshell.Io
import "Artwork.js" as Artwork

Item {
  id: root
  property string url: ""
  property string source: ""
  property string requestedUrl: ""
  property bool discarded: false
  readonly property bool loading: reader.running || debounce.running

  function refresh() {
    source = ""
    requestedUrl = ""
    discarded = true
    debounce.stop()
    if (reader.running) reader.signal(9)
    else if (Artwork.localSource(url)) debounce.restart()
  }
  onUrlChanged: refresh()
  Component.onCompleted: refresh()

  Timer {
    id: debounce
    interval: 100
    onTriggered: {
      // Keep at most one reader, including on a stalled filesystem.
      if (reader.running || !Artwork.localSource(root.url)) return
      root.requestedUrl = root.url
      root.discarded = false
      reader.command = ["/usr/bin/python3", "-I", decodeURIComponent(Qt.resolvedUrl("artwork_loader.py").toString().substring(7)), root.url]
      reader.running = true
      deadline.restart()
    }
  }
  Timer {
    id: deadline
    interval: 3500
    onTriggered: {
      root.discarded = true
      reader.signal(9)
    }
  }
  Process {
    id: reader
    stdout: StdioCollector {
      onStreamFinished: {
        if (!root.discarded && root.requestedUrl === root.url
            && text.length <= 11184840
            && /^data:image\/(png|jpeg);base64,[A-Za-z0-9+/=]+$/.test(text))
          root.source = text
      }
    }
    onExited: function(exitCode, exitStatus) {
      deadline.stop()
      if (exitCode !== 0) root.source = ""
      if (root.requestedUrl !== root.url && Artwork.localSource(root.url)) debounce.restart()
    }
  }
}
