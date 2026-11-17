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
// Async font styles change their media after loading; keep that loaded copy on navigation.
document.addEventListener("htmx:head:before:add", event => {
  const element = event.detail.headElement;
  if (element.tagName === "LINK" && element.id && element.hasAttribute("hx-preserve") && document.getElementById(element.id)) {
    event.preventDefault();
  }
});
