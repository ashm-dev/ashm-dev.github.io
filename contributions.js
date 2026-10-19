import { el } from "./dom.js";

export function projectSummary(project, t) {
  return project.sections.filter((section) => section.items.length).map((section) => {
    const counts = ["done", "open"].map((state) => {
      const count = section.items.filter((item) => item.state === state).length;
      return count ? `${count} ${t.states[section.title][state]}` : null;
    }).filter(Boolean);
    return `${t.sections[section.title]}: ${counts.join(", ")}`;
  }).join(" · ");
}

export function renderProject(project, t) {
  const details = el("details", { "data-project": project.name }, [
    el("summary", {}, [el("b", {}, [project.name]), el("span", { class: "project-counts" }, [projectSummary(project, t)])]),
  ]);
  for (const section of project.sections) {
    if (!section.items.length) continue;
    details.append(el("h3", {}, [t.sections[section.title]]));
    details.append(el("ul", {}, section.items.map((item) => {
      const state = t.states[section.title][item.state];
      return el("li", {}, [
        el("span", { class: `dot ${item.state}`, role: "img", "aria-label": state, title: state }), " ",
        el("a", { href: item.url }, [item.label]), ` ${item.title}`,
      ]);
    })));
  }
  return details;
}
