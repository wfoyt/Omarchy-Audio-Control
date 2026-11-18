import QtQuick
import QtTest
import "../Artwork.js" as Artwork

TestCase {
  name: "ArtworkImage"
  property var activePlayer: null

  Image {
    id: albumArt
    asynchronous: true
    source: Artwork.localSource(activePlayer ? activePlayer.trackArtUrl : "")
  }

  function test_playerChanges() {
    activePlayer = { trackArtUrl: "https://art.example/cover.jpg" }
    compare(albumArt.source.toString(), "")
    compare(albumArt.status, Image.Null)

    var localUrl = Qt.resolvedUrl("../preview.png").toString()
    activePlayer = { trackArtUrl: localUrl }
    tryCompare(albumArt, "status", Image.Ready)
    compare(albumArt.source.toString(), localUrl)

    activePlayer = { trackArtUrl: "http://127.0.0.1:8080/private" }
    compare(albumArt.source.toString(), "")
    compare(albumArt.status, Image.Null)

    activePlayer = null
    compare(albumArt.source.toString(), "")
  }
}
