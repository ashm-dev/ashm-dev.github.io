import { el } from "./dom.js";

function plural(n, forms) {
  const mod10 = n % 10;
  const mod100 = n % 100;
  const form = mod10 === 1 && mod100 !== 11 ? "one" : mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14) ? "few" : "many";
  return forms[form].replace("{n}", String(n));
}

function monthsBetween(start, end) {
  const [y1, m1] = start.split("-").map(Number);
  const now = new Date();
  const [y2, m2] = end ? end.split("-").map(Number) : [now.getFullYear(), now.getMonth() + 1];
  return Math.max(1, y2 * 12 + m2 - (y1 * 12 + m1) + 1);
}

function duration(job, forms) {
  const months = monthsBetween(job.start, job.end);
  const parts = [];
  if (months >= 12) parts.push(plural(Math.floor(months / 12), forms.year));
  if (months % 12) parts.push(plural(months % 12, forms.month));
  return parts.join(" ");
}

export function renderProfile(t, lang, since) {
  document.documentElement.lang = lang;
  document.title = t.name;
  document.getElementById("name").textContent = t.name;
  document.getElementById("role").textContent = t.role;
  document.getElementById("contacts").replaceChildren(...t.contacts.map((c) => el("a", { href: c.url }, [c.label])));
  const years = plural(Math.max(1, Math.floor(monthsBetween(since, null) / 12)), t.years);
  document.getElementById("summary").textContent = t.summary.replace("{years}", years);
  document.getElementById("h-experience").textContent = t.headings.experience;
  document.getElementById("h-languages").textContent = t.headings.languages;
  document.getElementById("h-oss").textContent = t.headings.oss;
  document.getElementById("experience").replaceChildren(...t.experience.flatMap((job) => [
    el("dt", {}, [job.period, el("br"), el("span", { class: "muted" }, [duration(job, t.duration)])]),
    el("dd", {}, [
      el("b", {}, [job.title]), ", ", el("a", { href: job.url }, [job.company]),
      el("ul", { class: "bullets" }, job.bullets.map((b) => el("li", {}, [el("b", {}, [`${b.lead}: `]), b.text]))),
    ]),
  ]));
  document.getElementById("languages").replaceChildren(...t.languages.map((l) => el("li", {}, [el("span", { class: "lang" }, [l.code]), l.text])));
  const cv = document.getElementById("cv");
  cv.textContent = t.headings.cv;
  cv.href = `cv-${lang}.pdf`;
  for (const button of document.querySelectorAll("[data-lang]")) {
    button.setAttribute("aria-current", button.dataset.lang === lang ? "true" : "false");
  }
}
