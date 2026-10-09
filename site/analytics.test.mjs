import { test } from "node:test";
import assert from "node:assert/strict";
import { analyticsAllowed, sanitizeEvent } from "./analytics.js";
test("production origin and browser privacy controls", () => {
  const location = { hostname: "sideword.vercel.app", protocol: "https:" };
  assert.equal(analyticsAllowed(location, {}), true);
  assert.equal(analyticsAllowed(location, {doNotTrack: "1"}), false);
  assert.equal(analyticsAllowed(location, {globalPrivacyControl: true}), false);
  assert.equal(analyticsAllowed({...location, hostname: "preview.vercel.app"}, {}), false);
});
test("only public pageviews are retained and sanitized", () => {
  for (const path of ["/", "/zh/"]) {
    const url = `https://sideword.vercel.app${path}`;
    assert.deepEqual(sanitizeEvent({type: "pageview", url: url + "?email=private#secret"}), {type: "pageview", url});
    assert.equal(sanitizeEvent({type: "event", url}), null);
  }
  for (const url of ["https://evil.example/", "https://sideword.vercel.app/private", "invalid"]) assert.equal(sanitizeEvent({type: "pageview", url}), null);
});
