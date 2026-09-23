const DATA_URL = "https://raw.githubusercontent.com/ashm-dev/ashm-dev/main/contributions.json";
const LANGS = ["en", "ru"];

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  for (const child of children) node.append(child);
  return node;
}

function pickLang() {
  let saved = null;
  try { saved = localStorage.getItem("lang"); } catch { saved = null; }
  if (LANGS.includes(saved)) return saved;
  return (navigator.language || "").toLowerCase().startsWith("ru") ? "ru" : "en";
}

function yearsSince(since, forms) {
  const [y, m] = since.split("-").map(Number);
  const now = new Date();
  const n = Math.max(1, Math.floor((now.getFullYear() * 12 + now.getMonth() + 1 - (y * 12 + m)) / 12));
  const mod10 = n % 10;
  const mod100 = n % 100;
  const form = mod10 === 1 && mod100 !== 11 ? "one" : mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14) ? "few" : "many";
  return forms[form].replace("{n}", String(n));
}

function landed(section) {
  return section.items.filter((item) => item.state === "done").length;
}

function summary(project, t) {
  const [first, second] = project.sections;
  const verb = t.verbs[first.title] || t.verbs["Pull requests"];
  return `${landed(first)} ${verb} ${t.nouns[first.title]} · ${second.items.length} ${t.nouns[second.title]}`;
}

function renderItem(item) {
  return el("li", {}, [el("span", { class: `dot ${item.state}` }), " ", el("a", { href: item.url }, [item.label]), ` ${item.title}`]);
}

function renderProject(project, t) {
  const details = el("details", {}, [el("summary", {}, [el("b", {}, [project.name]), ` — ${summary(project, t)}`])]);
  for (const section of project.sections) {
    if (!section.items.length) continue;
    details.append(el("h3", {}, [section.title]), el("ul", {}, section.items.map(renderItem)));
  }
  return details;
}

function renderProfile(t, lang, since) {
  document.documentElement.lang = lang;
  document.title = t.name;
  document.getElementById("name").textContent = t.name;
  document.getElementById("role").textContent = t.role;
  document.getElementById("contacts").replaceChildren(...t.contacts.map((c) => el("a", { href: c.url }, [c.label])));
  document.getElementById("summary").textContent = t.summary.replace("{years}", yearsSince(since, t.years));
  document.getElementById("h-experience").textContent = t.headings.experience;
  document.getElementById("h-languages").textContent = t.headings.languages;
  document.getElementById("h-oss").textContent = t.headings.oss;
  document.getElementById("experience").replaceChildren(...t.experience.flatMap((job) => [
    el("dt", {}, [job.period]),
    el("dd", {}, [
      el("b", {}, [job.title]), ", ", el("a", { href: job.url }, [job.company]),
      el("ul", { class: "bullets" }, job.bullets.map((b) => el("li", {}, [el("b", {}, [`${b.lead}: `]), b.text]))),
    ]),
  ]));
  document.getElementById("languages").replaceChildren(...t.languages.map((l) => el("li", {}, [el("span", { class: "lang" }, [l.code]), l.text])));
  document.getElementById("oss-note").replaceChildren(
    `${t.oss_note} `, el("span", { class: "dot done" }), ` ${t.legend.done}, `, el("span", { class: "dot open" }), ` ${t.legend.open}.`,
  );
  const cv = document.getElementById("cv");
  cv.textContent = t.headings.cv;
  cv.href = `cv-${lang}.pdf`;
  for (const button of document.querySelectorAll("[data-lang]")) {
    button.setAttribute("aria-current", button.dataset.lang === lang ? "true" : "false");
  }
}

async function main() {
  const content = await fetch("content.json").then((resp) => resp.json());
  let lang = pickLang();
  let projects = null;
  const render = () => {
    const t = content[lang];
    renderProfile(t, lang, content.since);
    const box = document.getElementById("projects");
    if (projects) box.replaceChildren(...projects.map((p) => renderProject(p, t)));
  };
  for (const button of document.querySelectorAll("[data-lang]")) {
    button.addEventListener("click", () => {
      lang = button.dataset.lang;
      try { localStorage.setItem("lang", lang); } catch { /* private mode */ }
      render();
    });
  }
  render();
  try {
    projects = await fetch(DATA_URL).then((resp) => resp.json());
  } catch {
    document.getElementById("projects").replaceChildren(el("p", { class: "muted" }, ["github.com/ashm-dev"]));
    return;
  }
  render();
}

main();
