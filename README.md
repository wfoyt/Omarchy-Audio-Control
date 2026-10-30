# Omarchy Audio Control

A themed music button for the Omarchy Quickshell bar. Click to show album
art, track name, artist, album, and previous/restart, play/pause, and skip controls.
Uses Omarchy’s native colors, typography, spacing, borders, and popup behavior.

## Install

Requires an Omarchy version with the Quickshell shell and `omarchy plugin` commands.

```bash
omarchy plugin add https://github.com/wfoyt/Omarchy-Audio-Control.git --enable
```

Choose the center section when prompted. To place the button immediately
right of weather:

```bash
omarchy bar move wfo.media --after omarchy.weather
```

The root manifest registers `wfo.media`, a clone of the built-in
`omarchy.media` service. Enabling it replaces the stock media plugin and
preserves Omarchy’s media hotkeys and player detection. No install scripts
or additional packages are required. Your player must expose MPRIS metadata
and controls, as Spotify and many Linux media players do.

If you already have the locally created `wfo.media` plugin, move that folder
outside `~/.config/omarchy/plugins/` before installing this repository; the
installer correctly refuses duplicate plugin IDs. Keep it as a backup.

## Use

- Click the music-note button to open or close the popup.
- Previous/restart restarts after three seconds; near the beginning it goes
  to the previous track. Players without seeking use their native Previous action.
- Play/pause and Next control the displayed player.
- Click outside or press Escape to dismiss.
- Multiple available players appear in a source picker.
- Missing artwork shows a music note; unavailable controls are dimmed.

## Update or disable

```bash
omarchy plugin update wfo.media
omarchy plugin disable wfo.media
```

## Development

```bash
omarchy plugin validate .
qmllint MusicWidget.qml Playback.js
```

`MusicWidget.qml` implements the native button and popup. `Playback.js`
implements previous/restart. `Service.qml` and `MediaModel.js` are derived
from Omarchy’s media plugin (https://github.com/basecamp/omarchy), preserving
its source selection and playback integration. The `omarchy.clonedFrom`
manifest field retains the required service compatibility.

Plugin metadata and entry points are at the repository root so Omarchy’s
standard Git installer can validate and load the checkout directly.
