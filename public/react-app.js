const { createElement: h, useState } = React;
const marketplaceNames = { aws: "AWS", azure: "Azure", gcp: "Google Cloud" };

function Badge({ children, tone = "neutral" }) {
  return h("span", { className: `badge badge-${tone}` }, children);
}

function EvidenceResult({ match }) {
  return h("article", { className: "match-card" },
    h("div", { className: "match-card-top" },
      h("div", null, h("span", { className: "eyebrow" }, marketplaceNames[match.provider] || match.provider), h("h3", null, match.title)),
      h(Badge, { tone: "verified" }, "Live official domain")),
    h("p", { className: "result-snippet" }, match.description),
    h("div", { className: "card-meta" },
      h("span", null, `Retrieved ${new Date(match.retrieved_at).toLocaleString()}`),
      h("a", { href: match.url, target: "_blank", rel: "noreferrer" }, "Inspect source ↗")));
}

function ProviderHealth({ providers = {} }) {
  return h("div", { className: "health-grid" }, Object.entries(providers).map(([key, provider]) =>
    h("div", { className: "health-row", key }, h("span", null, marketplaceNames[key]), h(Badge, { tone: provider.status === "ok" ? "verified" : "error" }, `${provider.status} · ${provider.result_count}`))));
}

function ResearchBrief({ brief }) {
  if (!brief) return null;
  const grounded = brief.status === "grounded";
  return h("section", { className: `research-brief ${grounded ? "grounded" : "abstained"}` },
    h("div", { className: "brief-heading" },
      h("div", null, h("p", { className: "kicker" }, "Agent decision"), h("h2", null, grounded ? "Grounded brief" : "Abstained safely")),
      h(Badge, { tone: grounded ? "verified" : "neutral" }, grounded ? `${Math.round(brief.confidence * 100)}% confidence` : "No grounded match")),
    h("p", { className: "brief-answer" }, brief.answer),
    brief.evidence.length > 0 && h("div", { className: "brief-evidence" }, brief.evidence.map(item =>
      h("a", { href: item.url, target: "_blank", rel: "noreferrer", key: item.id },
        h("strong", null, item.title),
        h("span", null, `${marketplaceNames[item.provider]} · relevance ${Math.round(item.relevance_score * 100)}% · ${item.id}`),
        h("small", null, item.verification.replaceAll("_", " "))))),
    h("p", { className: "brief-caveat" }, brief.caveats.join(" ")));
}

function App() {
  const [request, setRequest] = useState("Find enterprise automation products on Azure");
  const [vendor, setVendor] = useState("Red Hat");
  const [solution, setSolution] = useState("Ansible");
  const [brief, setBrief] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState("");
  const [error, setError] = useState("");

  async function post(path, body) {
    const response = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const next = await response.json();
    if (!response.ok || next.status !== "success") throw new Error(next.message || "Request failed");
    return next.results;
  }

  async function research(event) {
    event.preventDefault();
    if (!request.trim()) return setError("Describe the product or capability you need.");
    setLoading("research"); setError("");
    try { setBrief(await post("/api/research", { request: request.trim() })); } catch (requestError) { setError(requestError.message); } finally { setLoading(""); }
  }

  async function search(event) {
    event.preventDefault();
    if (!vendor.trim() && !solution.trim()) return setError("Enter a vendor, product, or both.");
    setLoading("search"); setError("");
    try { setData(await post("/api/search", { vendor: vendor.trim(), solution: solution.trim() })); } catch (requestError) { setError(requestError.message); } finally { setLoading(""); }
  }

  const evidence = data?.matches || [];
  return h("main", { className: "app-shell" },
    h("nav", { className: "topbar" }, h("div", { className: "brand" }, h("span", { className: "brand-mark" }, "CM"), h("span", null, "CloudMatch")), h("div", { className: "system-status" }, h("span", { className: "status-dot" }), "Live official-domain retrieval")),
    h("section", { className: "hero" },
      h("div", { className: "hero-copy" }, h("p", { className: "kicker" }, "Agent-native marketplace research / v4"), h("h1", null, "Research cloud products. Live."), h("p", { className: "hero-text" }, "Every request searches the current web and accepts only official AWS, Azure, or Google Cloud marketplace URLs. No catalog, synthetic records, cloud accounts, or paid APIs."), h("div", { className: "architecture-strip" }, h("span", null, "Interpret"), h("i", null, "→"), h("span", null, "Search live"), h("i", null, "→"), h("span", null, "Verify domain"), h("i", null, "→"), h("span", null, "Abstain"))),
      h("form", { className: "search-panel", onSubmit: research }, h("label", null, "Research request", h("input", { value: request, onChange: e => setRequest(e.target.value), maxLength: 600, placeholder: "Find automation products on Azure" })), h("button", { type: "submit", disabled: !!loading }, loading === "research" ? "Building brief…" : "Run research agent"), error && h("p", { className: "form-error", role: "alert" }, error))),
    h(ResearchBrief, { brief }),
    h("section", { className: "workspace", "aria-live": "polite" },
      h("div", { className: "section-heading" }, h("div", null, h("p", { className: "kicker" }, "Live result explorer"), h("h2", null, data ? `Results for “${data.query}”` : "Search official marketplaces")), data && h("span", { className: "catalog-count" }, `${data.observability.duration_ms} ms · retrieved now`)),
      h("form", { className: "inline-search", onSubmit: search }, h("input", { "aria-label": "Vendor", value: vendor, onChange: e => setVendor(e.target.value), maxLength: 160, placeholder: "Vendor" }), h("input", { "aria-label": "Product", value: solution, onChange: e => setSolution(e.target.value), maxLength: 160, placeholder: "Product or solution" }), h("button", { type: "submit", disabled: !!loading }, loading === "search" ? "Searching…" : "Search evidence")),
      !data ? h("div", { className: "empty-state initial" }, "No credentials and no local catalog. Every search runs against the current public web.") : h("div", { className: "results-grid" },
        h("div", { className: "match-list" },
          h("div", { className: "result-section-title" }, h("h3", null, "Live official marketplace results"), h(Badge, { tone: evidence.length ? "verified" : "neutral" }, `${evidence.length} returned`)),
          evidence.length ? evidence.map(match => h(EvidenceResult, { match, key: match.id })) : h("div", { className: "empty-state" }, data.disclaimer)),
        h("aside", { className: "insight-panel" }, h("p", { className: "kicker" }, "Provider status"), h("h3", null, "Know what answered"), h("p", null, "Results are accepted only when their URLs belong to an official marketplace domain. Retrieval failure produces an explicit unavailable state or abstention."), h(ProviderHealth, { providers: data.providers }), h("div", { className: "provider-links" }, Object.entries(data.provider_links || {}).map(([key, link]) => h("a", { href: link.url, target: "_blank", rel: "noreferrer", key }, `Search ${marketplaceNames[key]} directly ↗`))), h("div", { className: "telemetry" }, `Live web search · ${evidence.length} verified URLs`)))),
    h("footer", null, h("span", null, "CloudMatch / live search + official-domain verification"), h("span", null, "Native MCP · no catalog · no paid runtime services")));
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
