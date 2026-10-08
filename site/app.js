const {
  words,
  labels: t,
  command,
} = JSON.parse(document.querySelector("#demo-data").textContent);
const tabs = [...document.querySelectorAll("[data-word]")];
const done = new Set();
let selected = 0;
const content = document.querySelector(".word-content");
const initial = content.innerHTML;
const status = document.querySelector(".demo-status");
const remember = document.querySelector(".remember");
function render() {
  tabs.forEach((tab, i) => {
    tab.disabled = done.has(i);
    tab.setAttribute("aria-pressed", String(i === selected && !done.has(i)));
  });
  document.querySelector(".demo-count").textContent =
    `${words.length - done.size} ${t.left}`;
  remember.disabled = done.size === words.length;
  if (remember.disabled) {
    content.replaceChildren();
    const title = document.createElement("p");
    title.className = "word";
    title.textContent = t.empty;
    const text = document.createElement("p");
    text.className = "meaning";
    text.textContent = t.emptyText;
    content.append(title, text);
    document.querySelector(".reset").focus();
    return;
  }
  content.innerHTML = initial;
  const word = words[selected];
  for (const [selector, value] of Object.entries({
    ".word": word.name,
    ".ipa": `/${word.ipa}/`,
    ".meaning": word.meaning,
    ".example p": word.example,
    ".translation": word.translation,
  }))
    content.querySelector(selector).textContent = value;
}
tabs.forEach((tab, i) =>
  tab.addEventListener("click", () => {
    selected = i;
    status.textContent = "";
    render();
  }),
);
remember.addEventListener("click", () => {
  done.add(selected);
  status.textContent = t.remembered;
  selected = words.findIndex((_, i) => !done.has(i));
  render();
});
document.querySelector(".reset").addEventListener("click", () => {
  done.clear();
  selected = 0;
  status.textContent = "";
  render();
  tabs[0].focus();
});
document.querySelector(".copy").addEventListener("click", async () => {
  const feedback = document.querySelector(".copy-status");
  try {
    await navigator.clipboard.writeText(command);
    feedback.textContent = t.copied;
  } catch {
    feedback.textContent = t.copyFailed;
    const range = document.createRange();
    range.selectNodeContents(document.querySelector(".install-command"));
    const selection = getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
  }
});
const theme = document.querySelector(".theme");
theme.setAttribute(
  "aria-pressed",
  String(matchMedia("(prefers-color-scheme: dark)").matches),
);
theme.addEventListener("click", () => {
  const current =
    document.documentElement.dataset.theme ||
    (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  theme.setAttribute("aria-pressed", String(next === "dark"));
});
