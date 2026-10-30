// MPRIS positions use seconds. Prefer restarting after the opening three
// seconds, while a second press near the beginning goes to the previous track.
function canRestart(player) {
  return !!(player && player.canSeek && player.positionSupported)
}

function canGoBack(player) {
  return !!(player && (player.canGoPrevious || canRestart(player)))
}

function previousOrRestart(player) {
  if (!player) return
  if (canRestart(player) && (player.position > 3 || !player.canGoPrevious))
    player.position = 0
  else if (player.canGoPrevious)
    player.previous()
}

if (typeof module !== "undefined")
  module.exports = { canRestart, canGoBack, previousOrRestart }
