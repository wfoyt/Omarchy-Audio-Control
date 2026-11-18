import QtQuick
import Quickshell
import "." as Plugin

ShellRoot {
  Item {
    id: root
    QtObject {
      id: radio
      property string dbusName: "org.mpris.MediaPlayer2.radio"
      property string identity: "Radio"
      property bool isPlaying: true
      property bool canPause: false
    }
    QtObject {
      id: music
      property string dbusName: "org.mpris.MediaPlayer2.music"
      property string identity: "Music"
      property bool isPlaying: false
      property bool canPlay: true
      property bool canPause: true
      function play() { isPlaying = true }
      function pause() { isPlaying = false }
    }
    Plugin.Service { id: service }

    Component.onCompleted: Qt.callLater(checkRouting)

    function checkRouting() {
      service.testPlayers = [radio, music]
      if (service.activePlayer !== radio
          || !service.selectPlayer(music.dbusName)
          || service.activePlayer !== music
          || service.runAction("play", false, "missing-player")
          || music.isPlaying
          || !service.runAction("playPause", false)
          || !music.isPlaying
          || !service.runAction("pause", false)
          || music.isPlaying) {
        console.error("FAIL: player selection or playback dispatch")
        Qt.exit(1)
        return
      }
      service.testPlayers = [radio]
      if (service.activePlayer !== radio || service.selectedPlayerKey) {
        console.error("FAIL: selected player removal")
        Qt.exit(1)
        return
      }
      console.log("PASS: source selection, targeted commands, capable player dispatch and removal")
      Qt.quit()
    }
  }
}
