// MPRIS metadata is player-controlled. Never let it make the shell fetch
// artwork from the network. Accept only absolute file URLs without a host;
// relative URLs and other schemes must not reach Qt Quick's Image loader.
function localSource(url) {
  if (typeof url !== "string" || /[\\\x00-\x1f\x7f]/.test(url)) return ""
  return /^file:\/\/\/[^/]/i.test(url) ? url : ""
}

if (typeof module !== "undefined")
  module.exports = { localSource }
