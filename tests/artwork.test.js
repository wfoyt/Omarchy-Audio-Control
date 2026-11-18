const assert = require("node:assert/strict")
const { test } = require("node:test")
const { localSource } = require("../Artwork.js")

test("preserves local artwork file URLs", () => {
  for (const url of [
    "file:///tmp/cover.png",
    "file:///home/user/Music/Album%20Art.jpg",
    "file:///home/user/Music/Album Art.jpg",
    "FILE:///tmp/cover.png",
  ]) assert.equal(localSource(url), url)
})

test("blocks remote hosts, alternate schemes, and ambiguous URLs", () => {
  for (const url of [
    "https://art.example/cover.jpg",
    "http://127.0.0.1:8080/private",
    "http://192.168.1.1/",
    "http://[::1]/",
    "HtTpS://art.example/cover.jpg",
    "ftp://art.example/cover.jpg",
    "//art.example/cover.jpg",
    "cover.jpg",
    "/tmp/cover.png",
    "file://art.example/cover.jpg",
    "file://localhost/tmp/cover.png",
    "file:////art.example/cover.jpg",
    "file:/tmp/cover.png",
    "file:cover.png",
    "file:///\\art.example/cover.jpg",
    "file:///tmp/cover\n.png",
    "file:///tmp/cover\u0000.png",
    " file:///tmp/cover.png",
    "\thttps://art.example/cover.jpg",
    "data:image/svg+xml,<svg/>",
    "image://provider/cover",
    "qrc:/cover.png",
    "file:///",
    "",
    null,
    undefined,
    {},
    42,
  ]) assert.equal(localSource(url), "", String(url))
})
