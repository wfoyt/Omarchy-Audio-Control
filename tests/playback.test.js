const assert = require('node:assert/strict')
const { test } = require('node:test')
const Playback = require('../Playback.js')
const Media = require('../MediaModel.js')

test('previous restarts seekable tracks after three seconds', () => {
  let skipped = 0
  const player = { canSeek: true, positionSupported: true, canGoPrevious: true, position: 12, previous() { skipped++ } }
  Playback.previousOrRestart(player)
  assert.equal(player.position, 0)
  assert.equal(skipped, 0)
  Playback.previousOrRestart(player)
  assert.equal(skipped, 1)
})

test('nonseekable players and missing controls', () => {
  let skipped = 0
  const player = { canGoPrevious: true, previous() { skipped++ } }
  Playback.previousOrRestart(player)
  assert.equal(skipped, 1)
  assert.equal(Playback.canGoBack({}), false)
  assert.equal(Playback.canGoBack(null), false)
  Playback.previousOrRestart(null)
})

test('OSD metadata cannot become rich text', () => {
  const raw = Media.osdMessage({ trackTitle: '<img src="https://example.invalid/tracker">', trackArtist: '&lt;b&gt;' }, 'Play')
  const safe = Media.safeDisplayText(raw)
  assert.ok(!/[<>&]/.test(safe))
  assert.equal(Media.safeDisplayText('Normal title - Artist'), 'Normal title - Artist')
  assert.equal(Media.safeDisplayText('x'.repeat(10000)).length, 4096)
})

test('playback capability follows the current playback state', () => {
  const player = { isPlaying: true, canPlay: true }
  assert.equal(Media.canHandleAction(player, 'playPause'), false)
  player.isPlaying = false
  assert.equal(Media.canHandleAction(player, 'playPause'), true)

  const toggleOnly = { canTogglePlaying: true, isPlaying: false }
  assert.equal(Media.canHandleAction(toggleOnly, 'play'), true)
  assert.equal(Media.canHandleAction(toggleOnly, 'pause'), false)
  toggleOnly.isPlaying = true
  assert.equal(Media.canHandleAction(toggleOnly, 'play'), false)
  assert.equal(Media.canHandleAction(toggleOnly, 'pause'), true)
})
