// Only the public website participates; previews and local demos stay untracked.
export function analyticsAllowed(location, navigator) {
  return (
    location.hostname === "sideword.vercel.app" &&
    location.protocol === "https:" &&
    navigator.doNotTrack !== "1" &&
    navigator.globalPrivacyControl !== true
  );
}

export function sanitizeEvent(event) {
  try {
    const url = new URL(event.url);
    if (!["/", "/zh/"].includes(url.pathname)) return null;
    url.search = "";
    url.hash = "";
    return { ...event, url: url.href };
  } catch {
    return null;
  }
}

if (typeof window !== "undefined" && analyticsAllowed(location, navigator)) {
  // Keep analytics failures isolated from the learning demo and installation UI.
  import("./vercel-analytics.mjs")
    .then(({ inject }) =>
      inject({ mode: "production", beforeSend: sanitizeEvent }),
    )
    .catch(() => {});
}
