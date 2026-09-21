const DATA_URL = "https://raw.githubusercontent.com/ashm-dev/ashm-dev/main/contributions.json";

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  for (const child of children) node.append(child);
  return node;
}

function renderItem(item) {
  return el("li", {}, [el("span", { class: `dot ${item.state}` }), " ", el("a", { href: item.url }, [item.label]), ` ${item.title}`]);
}

function renderProject(project) {
  const details = el("details", {}, [el("summary", {}, [el("b", {}, [project.name]), ` — ${project.summary}`])]);
  for (const section of project.sections) {
    if (!section.items.length) continue;
    details.append(el("h3", {}, [section.title]), el("ul", {}, section.items.map(renderItem)));
  }
  return details;
}

fetch(DATA_URL)
  .then((resp) => resp.json())
  .then((projects) => document.getElementById("projects").replaceChildren(...projects.map(renderProject)))
  .catch(() => document.getElementById("projects").replaceChildren(el("p", { class: "muted" }, ["Could not load the list. See github.com/ashm-dev."])));
