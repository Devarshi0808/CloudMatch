const { createElement: h, useState } = React;
const marketplaceNames = { aws: "AWS", azure: "Azure", gcp: "Google Cloud" };

function Badge({ children, tone = "neutral" }) {
  return h("span", { className: `badge badge-${tone}` }, children);
}

function EvidenceResult({ match }) {
  return h("article", { className: "match-card" },
    h("div", { className: "match-card-top" },
      h("div", null, h("span", { className: "eyebrow" }, marketplaceNames[match.provider] || match.provider), h("h3", null, match.title)),
      h(Badge, { tone: "verified" }, "Reviewed evidence")),
    h("p", { className: "result-snippet" }, match.description),
    h("div", { className: "card-meta" },
      h("span", null, `${match.vendor} · verified ${match.verified_at}`),
      h("a", { href: match.url, target: "_blank", rel: "noreferrer" }, "Inspect source ↗")));
}

function BenchmarkResult({ match }) {
  return h("article", { className: "match-card benchmark-card" },
    h("div", { className: "match-card-top" }, h("div", null, h("span", { className: "eyebrow" }, match.vendor), h("h3", null, match.solution)), h("strong", { className: "score" }, `${match.score}%`)),
    h("p", { className: "match-type" }, "Benchmark catalog · not marketplace evidence"),
    h("ul", { className: "evidence" }, (match.evidence || []).map(item => h("li", { key: item }, item))));
}

function ProviderHealth({ providers = {} }) {
  return h("div", { className: "health-grid" }, Object.entries(providers).map(([key, provider]) =>
    h("div", { className: "health-row", key }, h("span", null, marketplaceNames[key]), h(Badge, { tone: provider.status === "snapshot" ? "verified" : "neutral" }, provider.detail))));
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
        h("span", null, `${marketplaceNames[item.provider]} · ${item.score}% · ${item.id}`),
        h("small", null, `Matched: ${item.matched_terms.join(", ")}`)))),
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
  const benchmark = data?.catalog_matches || [];
  return h("main", { className: "app-shell" },
    h("nav", { className: "topbar" }, h("div", { className: "brand" }, h("span", { className: "brand-mark" }, "CM"), h("span", null, "CloudMatch")), h("div", { className: "system-status" }, h("span", { className: "status-dot" }), "Zero-cost grounded retrieval")),
    h("section", { className: "hero" },
      h("div", { className: "hero-copy" }, h("p", { className: "kicker" }, "Agent-native marketplace research / v3"), h("h1", null, "Research cloud products. Keep the evidence."), h("p", { className: "hero-text" }, "Natural-language discovery over reviewed public listings, with confidence, citations, abstention, and native MCP tools—without cloud accounts or paid APIs."), h("div", { className: "architecture-strip" }, h("span", null, "Interpret"), h("i", null, "→"), h("span", null, "Retrieve"), h("i", null, "→"), h("span", null, "Ground"), h("i", null, "→"), h("span", null, "Abstain"))),
      h("form", { className: "search-panel", onSubmit: research }, h("label", null, "Research request", h("input", { value: request, onChange: e => setRequest(e.target.value), maxLength: 600, placeholder: "Find automation products on Azure" })), h("button", { type: "submit", disabled: !!loading }, loading === "research" ? "Building brief…" : "Run research agent"), error && h("p", { className: "form-error", role: "alert" }, error))),
    h(ResearchBrief, { brief }),
    h("section", { className: "workspace", "aria-live": "polite" },
      h("div", { className: "section-heading" }, h("div", null, h("p", { className: "kicker" }, "Evidence explorer"), h("h2", null, data ? `Results for “${data.query}”` : "Inspect marketplace evidence")), data && h("span", { className: "catalog-count" }, `${data.observability.duration_ms} ms · snapshot ${data.snapshot_verified_at}`)),
      h("form", { className: "inline-search", onSubmit: search }, h("input", { "aria-label": "Vendor", value: vendor, onChange: e => setVendor(e.target.value), maxLength: 160, placeholder: "Vendor" }), h("input", { "aria-label": "Product", value: solution, onChange: e => setSolution(e.target.value), maxLength: 160, placeholder: "Product or solution" }), h("button", { type: "submit", disabled: !!loading }, loading === "search" ? "Searching…" : "Search evidence")),
      !data ? h("div", { className: "empty-state initial" }, "No credentials needed. Search the reviewed snapshot or ask the research agent a natural-language question.") : h("div", { className: "results-grid" },
        h("div", { className: "match-list" },
          h("div", { className: "result-section-title" }, h("h3", null, "Reviewed marketplace evidence"), h(Badge, { tone: evidence.length ? "verified" : "neutral" }, `${evidence.length} returned`)),
          evidence.length ? evidence.map(match => h(EvidenceResult, { match, key: match.id })) : h("div", { className: "empty-state" }, data.disclaimer),
          h("div", { className: "result-section-title benchmark-title" }, h("h3", null, "Explainable benchmark suggestions"), h(Badge, null, `${benchmark.length} ranked`)),
          benchmark.map((match, index) => h(BenchmarkResult, { match, key: `${match.vendor}-${match.solution}-${index}` }))),
        h("aside", { className: "insight-panel" }, h("p", { className: "kicker" }, "Evidence coverage"), h("h3", null, "Know what answered"), h("p", null, "Every grounded result resolves to a stable evidence ID and public source. Missing coverage produces an explicit abstention instead of a fabricated listing."), h(ProviderHealth, { providers: data.providers }), h("div", { className: "provider-links" }, Object.entries(data.provider_links || {}).map(([key, link]) => h("a", { href: link.url, target: "_blank", rel: "noreferrer", key }, `Search ${marketplaceNames[key]} directly ↗`))), h("div", { className: "telemetry" }, `${data.retrieval.snapshot_results}/${data.retrieval.snapshot_size} snapshot matches · ${data.retrieval.benchmark_results} benchmark`)))),
    h("footer", null, h("span", null, "CloudMatch / reviewed evidence + safe abstention"), h("span", null, "Native MCP · no paid runtime services")));
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
