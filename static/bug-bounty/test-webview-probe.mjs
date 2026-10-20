import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const html = readFileSync(new URL("./hollister-webview-probe.html", import.meta.url), "utf8");
const script = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(script, "Probe must contain its inline script");

function load(geolocation) {
  const elements = Object.fromEntries(["context", "result", "location"].map(id =>
    [id, {textContent: "", disabled: false, addEventListener(event, fn) {
      assert.equal(event, "click");
      this.click = fn;
    }}]));
  vm.runInNewContext(script, {
    document: {getElementById: id => elements[id]},
    window: {location: {origin: "https://woldhack.nl"}, isSecureContext: true},
    navigator: {userAgent: "probe-test", geolocation}
  });
  return elements;
}

let calls = 0;
let callbacks;
const page = load({getCurrentPosition(success, error, options) {
  calls++;
  callbacks = {success, error};
  assert.equal(options.timeout, 15000);
}});
assert.equal(calls, 0, "Loading the page must not request location");
assert.equal(JSON.parse(page.context.textContent).origin, "https://woldhack.nl");
page.location.click();
assert.equal(calls, 1);
assert.equal(page.location.disabled, true);
callbacks.success({coords: {latitude: 1.25, longitude: 2.5, accuracy: 10}, timestamp: 123});
assert.equal(JSON.parse(page.result.textContent).latitude, 1.25);
assert.equal(page.location.disabled, false);
page.location.click();
callbacks.error({code: 1, message: "Permission denied"});
assert.equal(JSON.parse(page.result.textContent).status, "error");
assert.equal(page.location.disabled, false);
const unsupported = load(undefined);
unsupported.location.click();
assert.match(unsupported.result.textContent, /unavailable/);
console.log("PASS: no automatic location request; success, denial and unavailable API displayed correctly.");
