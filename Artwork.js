// Cheap URL gate before launching the reader, NOT file validation. Only
// Artwork.qml + artwork_loader.py may turn this input into an Image source.
function localSource(url) {
  if (typeof url !== "string" || url.length > 16384 || /[\\\x00-\x1f\x7f]/.test(url)) return ""
  return /^file:\/\/\/[^/]/i.test(url) ? url : ""
}

if (typeof module !== "undefined")
  module.exports = { localSource }
