"use strict";
document.addEventListener("htmx:after:settle", () => {
  const page = document.getElementById("page");
  if (page) document.documentElement.lang = page.dataset.language;
  const main = document.getElementById("main");
  if (main) main.focus({ preventScroll: true });
});
document.addEventListener("htmx:response:error", event => {
  const url = event.detail?.ctx?.request?.action;
  if (url && new URL(url, location.href).origin === location.origin) location.assign(url);
});
