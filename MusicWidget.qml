import QtQuick
import Quickshell
import qs.Ui
import qs.Commons
import qs.Commons as Commons
import "Playback.js" as Playback

Panel {
  id: root
  moduleName: "omarchy.media"
  ipcTarget: "wfo.music"

  Commons.Translations { id: strings; directory: Qt.resolvedUrl("i18n") }

  // The cloned media service keeps Omarchy's player selection and hotkeys.
  readonly property var mediaService: bar?.shell?.firstPartyServiceFor("omarchy.media")
  readonly property var activePlayer: mediaService ? mediaService.activePlayer : null
  readonly property var sourcePlayers: mediaService ? mediaService.sourcePlayers : []
  readonly property string title: activePlayer ? (activePlayer.trackTitle || strings.t("unknownTrack")) : strings.t("nothingPlaying")
  readonly property string artist: activePlayer ? (activePlayer.trackArtist || strings.t("unknownArtist")) : strings.t("startMusic")
  readonly property color detailColor: Commons.Color.popups.text

  function previousOrRestart() {
    Playback.previousOrRestart(root.activePlayer)
  }

  Artwork {
    id: artwork
    url: root.activePlayer ? root.activePlayer.trackArtUrl : ""
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  BarIconButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: "󰝚"
    tooltipText: strings.t("music")
    onPressed: function(mouseButton) {
      if (mouseButton === Qt.LeftButton) root.toggle()
    }
  }

  KeyboardPanel {
    id: popup
    anchorItem: button
    bar: root.bar
    owner: root
    open: root.opened
    focusTarget: column
    contentWidth: popup.fittedContentWidth(Style.space(360))
    contentHeight: popup.fittedContentHeight(column.implicitHeight)

    Column {
      id: column
      focus: true
      Keys.onEscapePressed: root.close()
      anchors.fill: parent
      spacing: Style.space(10)

      Row {
        spacing: Style.space(10)
        width: parent.width

        BorderSurface {
          width: Style.space(88)
          height: Style.space(88)
          radius: Style.cornerRadius
          color: Style.normalFillFor(root.detailColor, Commons.Color.accent)
          borderSpec: Border.controlSpec("normal", root.detailColor, Commons.Color.accent)

          Image {
            id: albumArt
            anchors.fill: parent
            anchors.margins: Style.space(2)
            fillMode: Image.PreserveAspectCrop
            asynchronous: true
            source: artwork.source
            sourceSize.width: 256
            sourceSize.height: 256
            cache: false
            visible: status === Image.Ready
          }

          Text {
            anchors.centerIn: parent
            visible: albumArt.status !== Image.Ready
            text: "󰝚"
            color: root.detailColor
            font.family: Style.font.family
            font.pixelSize: Style.font.displayLarge
          }
        }

        Column {
          spacing: Style.space(4)
          width: parent.width - Style.space(98)

          Text {
            textFormat: Text.PlainText
            text: root.title
            color: root.detailColor
            font.family: Style.font.family
            font.pixelSize: Style.font.subtitle
            font.bold: true
            wrapMode: Text.Wrap
            width: parent.width
          }

          Text {
            textFormat: Text.PlainText
            text: root.artist
            color: root.detailColor
            opacity: 0.75
            font.family: Style.font.family
            font.pixelSize: Style.font.bodySmall
            wrapMode: Text.Wrap
            width: parent.width
            visible: text !== ""
          }

          Text {
            textFormat: Text.PlainText
            text: root.activePlayer && root.activePlayer.trackAlbum ? root.activePlayer.trackAlbum : ""
            color: root.detailColor
            opacity: 0.6
            font.family: Style.font.family
            font.pixelSize: Style.font.caption
            elide: Text.ElideRight
            width: parent.width
            visible: text !== ""
          }
        }
      }

      Row {
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: Style.space(6)

        Button {
          objectName: "previousButton"
          iconText: Commons.I18n.rightToLeft ? "󰒭" : "󰒮"
          tooltipText: strings.t("previous")
          focusable: true
          foreground: root.detailColor
          horizontalPadding: Style.spacing.controlPaddingX
          verticalPadding: Style.spacing.controlPaddingY
          enabled: Playback.canGoBack(root.activePlayer)
          opacity: enabled ? 1.0 : 0.4
          onClicked: root.previousOrRestart()
        }

        Button {
          objectName: "playPauseButton"
          iconText: root.activePlayer && root.activePlayer.isPlaying ? "󰏤" : "󰐊"
          tooltipText: root.activePlayer && root.activePlayer.isPlaying ? strings.t("pause") : strings.t("play")
          focusable: true
          foreground: root.detailColor
          horizontalPadding: Style.spacing.panelGap
          verticalPadding: Style.spacing.controlPaddingY
          iconSize: Style.font.iconLarge
          enabled: root.activePlayer && (root.activePlayer.canTogglePlaying || (root.activePlayer.isPlaying ? root.activePlayer.canPause : root.activePlayer.canPlay))
          opacity: enabled ? 1.0 : 0.4
          onClicked: if (root.mediaService) root.mediaService.runAction("playPause", false, root.mediaService.playerKey(root.activePlayer))
        }

        Button {
          objectName: "nextButton"
          iconText: Commons.I18n.rightToLeft ? "󰒮" : "󰒭"
          tooltipText: strings.t("next")
          focusable: true
          foreground: root.detailColor
          horizontalPadding: Style.spacing.controlPaddingX
          verticalPadding: Style.spacing.controlPaddingY
          enabled: root.activePlayer && root.activePlayer.canGoNext
          opacity: enabled ? 1.0 : 0.4
          onClicked: if (root.mediaService) root.mediaService.runAction("next", false, root.mediaService.playerKey(root.activePlayer))
        }
      }

      PanelSeparator {
        visible: root.sourcePlayers.length > 1
        foreground: root.detailColor
      }

      Column {
        id: sourceList
        visible: root.sourcePlayers.length > 1
        width: parent.width
        spacing: Style.space(4)

        Repeater {
          model: root.sourcePlayers

          BorderSurface {
            id: sourceRow
            required property var modelData

            readonly property var player: modelData
            readonly property bool selected: root.activePlayer && player
              && root.mediaService.playerKey(root.activePlayer) === root.mediaService.playerKey(player)
            readonly property string sourceTitle: player ? (player.trackTitle || player.identity || player.desktopEntry || strings.t("mediaSource")) : strings.t("mediaSource")
            readonly property string sourceDetail: player && player.trackArtist ? player.trackArtist : (player && player.identity ? player.identity : "")

            width: sourceList.width
            height: sourceInner.implicitHeight + Style.space(10)
            radius: Style.cornerRadius
            color: selected ? Style.selectedFillFor(root.detailColor, Commons.Color.accent) : "transparent"
            borderSpec: selected ? Border.controlSpec("normal", root.detailColor, Commons.Color.accent) : Border.none()

            Row {
              id: sourceInner
              anchors.left: parent.left
              anchors.right: parent.right
              anchors.verticalCenter: parent.verticalCenter
              anchors.leftMargin: sourceRow.borderLeft + Style.space(8)
              anchors.rightMargin: sourceRow.borderRight + Style.space(8)
              spacing: Style.space(8)

              Text {
                textFormat: Text.PlainText
                text: sourceRow.player && sourceRow.player.isPlaying ? "󰏤" : "󰐊"
                color: root.detailColor
                font.family: Style.font.family
                font.pixelSize: Style.font.body
                width: Style.space(18)
                horizontalAlignment: Text.AlignHCenter
                anchors.verticalCenter: parent.verticalCenter
              }

              Column {
                width: parent.width - Style.space(26)
                spacing: Style.space(1)
                anchors.verticalCenter: parent.verticalCenter

                Text {
                  textFormat: Text.PlainText
                  text: sourceRow.sourceTitle
                  color: root.detailColor
                  font.family: Style.font.family
                  font.pixelSize: Style.font.bodySmall
                  font.bold: sourceRow.selected
                  elide: Text.ElideRight
                  width: parent.width
                }

                Text {
                  textFormat: Text.PlainText
                  text: sourceRow.sourceDetail
                  color: root.detailColor
                  opacity: 0.65
                  font.family: Style.font.family
                  font.pixelSize: Style.font.caption
                  elide: Text.ElideRight
                  width: parent.width
                  visible: text !== ""
                }
              }
            }

            MouseArea {
              anchors.fill: parent
              hoverEnabled: true
              cursorShape: Qt.PointingHandCursor
              onClicked: if (root.mediaService) root.mediaService.selectPlayer(root.mediaService.playerKey(sourceRow.player))
            }
          }
        }
      }
    }
  }
}
