import { el } from "./dom.js";
import { renderProject } from "./contributions.js";
import { renderProfile } from "./profile.js";

const DATA_URL = "https://raw.githubusercontent.com/ashm-dev/ashm-dev/main/contributions.json";
const LANGS = ["en", "ru"];

function pickLang() {
  let saved = null;
  try { saved = localStorage.getItem("lang"); } catch { saved = null; }
  if (LANGS.includes(saved)) return saved;
  return (navigator.language || "").toLowerCase().startsWith("ru") ? "ru" : "en";
}

async function loadJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`);
  return response.json();
}

async function main() {
  const content = await loadJson("content.json");
  let lang = pickLang();
  let projects = null;
  let failed = false;
  const render = () => {
    const t = content[lang];
    renderProfile(t, lang, content.since);
    const box = document.getElementById("projects");
    if (projects) box.replaceChildren(...projects.map((project) => renderProject(project, t)));
    if (failed) box.replaceChildren(el("p", { class: "muted" }, [
      t.error, " ", el("a", { href: "https://github.com/ashm-dev" }, ["GitHub"]),
    ]));
  };
  for (const button of document.querySelectorAll("[data-lang]")) {
    button.addEventListener("click", () => {
      lang = button.dataset.lang;
      try { localStorage.setItem("lang", lang); } catch { /* Private browsing may disable storage. */ }
      render();
    });
  }
  render();
  try {
    projects = await loadJson(DATA_URL);
  } catch {
    failed = true;
  }
  render();
}

main().catch((error) => {
  console.error(error);
  document.getElementById("projects").replaceChildren(el("a", { href: "https://github.com/ashm-dev" }, ["GitHub"]));
});
