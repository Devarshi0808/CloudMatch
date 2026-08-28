const { createElement: h, useState } = React;
const marketplaceNames = { aws: "AWS", azure: "Azure", gcp: "Google Cloud" };

function Badge({ children, tone = "neutral" }) {
  return h("span", { className: `badge badge-${tone}` }, children);
}

function EvidenceResult({ match, rank }) {
  const score = Math.round((match.match_score ?? match.rank_score ?? match.relevance_score) * 100);
  return h("article", { className: "match-card" },
    h("div", { className: "match-card-top" },
      h("div", null,
        h("span", { className: "eyebrow" }, `${rank}. ${marketplaceNames[match.provider] || match.provider}`),
        h("h3", null, match.title)),
      h(Badge, { tone: "verified" }, `${score}% match`)),
    h("p", { className: "result-snippet" }, match.description || "No public description was returned."),
    h("div", { className: "card-meta" },
      h("span", null, `Official domain · ${match.matched_terms?.length || 0} query terms matched`),
      h("a", { href: match.url, target: "_blank", rel: "noreferrer" }, "Inspect source ↗")));
}

function ProviderHealth({ providers = {} }) {
  return h("div", { className: "health-grid" }, Object.entries(providers).map(([key, provider]) =>
    h("div", { className: "health-row", key },
      h("span", null, marketplaceNames[key]),
      h(Badge, { tone: provider.status === "ok" ? "verified" : "error" }, `${provider.status} · ${provider.result_count}`))));
}

function ResearchBrief({ brief }) {
  if (!brief) return null;
  const grounded = brief.status === "grounded";
  const quality = brief.quality || {};
  return h("section", { className: `research-brief ${grounded ? "grounded" : "abstained"}` },
    h("div", { className: "brief-heading" },
      h("div", null, h("p", { className: "kicker" }, "Agent decision"), h("h2", null, grounded ? "Grounded brief" : "Abstained safely")),
      h(Badge, { tone: grounded ? "verified" : "neutral" }, grounded ? `${Math.round(brief.confidence * 100)}% confidence` : "No grounded match")),
    h("p", { className: "brief-answer" }, brief.answer),
    h("div", { className: "quality-strip" },
      h("span", null, h("strong", null, quality.result_count || 0), " relevant"),
      h("span", null, h("strong", null, quality.duplicate_count || 0), " duplicates removed"),
      h("span", null, h("strong", null, quality.filtered_count || 0), " low-quality filtered")),
    h("p", { className: "brief-caveat" }, brief.caveats.join(" ")));
}

function Results({ brief }) {
  if (!brief) return h("div", { className: "empty-state initial" }, "Submit one request. The same grounded evidence powers both the decision and the result list.");
  const evidence = brief.evidence || [];
  const provider = brief.request?.provider;
  const links = Object.entries(brief.provider_links || {}).filter(([key]) => !provider || key === provider);
  return h("div", { className: "results-grid" },
    h("div", { className: "match-list" },
      h("div", { className: "result-section-title" },
        h("h3", null, "Ranked official marketplace evidence"),
        h(Badge, { tone: evidence.length ? "verified" : "neutral" }, `${evidence.length} distinct`)),
      evidence.length
        ? evidence.map((match, index) => h(EvidenceResult, { match, rank: index + 1, key: match.id }))
        : h("div", { className: "empty-state" }, "CloudMatch found no sufficiently relevant official listing and returned no fallback data.")),
    h("aside", { className: "insight-panel" },
      h("p", { className: "kicker" }, "Provider status"),
      h("h3", null, "Know what answered"),
      h("p", null, "Every result passed provider-domain validation, lexical relevance checks, and canonical-title deduplication."),
      h(ProviderHealth, { providers: brief.providers }),
      h("div", { className: "provider-links" }, links.map(([key, link]) =>
        h("a", { href: link.url, target: "_blank", rel: "noreferrer", key }, `Search ${marketplaceNames[key]} directly ↗`))),
      h("div", { className: "telemetry" }, `Live web search · ${evidence.length} distinct verified URLs`)));
}

function App() {
  const [request, setRequest] = useState("Find Red Hat Ansible on Azure");
  const [brief, setBrief] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function research(event) {
    event.preventDefault();
    if (!request.trim()) return setError("Describe the product or capability you need.");
    setLoading(true); setError("");
    try {
      const response = await fetch("/api/research", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ request: request.trim() }) });
      const payload = await response.json();
      if (!response.ok || payload.status !== "success") throw new Error(payload.message || "Request failed");
      setBrief(payload.results);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return h("main", { className: "app-shell" },
    h("nav", { className: "topbar" },
      h("div", { className: "brand" }, h("span", { className: "brand-mark" }, "CM"), h("span", null, "CloudMatch")),
      h("div", { className: "system-status" }, h("span", { className: "status-dot" }), "Live official-domain retrieval")),
    h("section", { className: "hero" },
      h("div", { className: "hero-copy" },
        h("p", { className: "kicker" }, "Agent-native marketplace research / v4.1"),
        h("h1", null, "Research cloud products. Live."),
        h("p", { className: "hero-text" }, "One request produces one ranked evidence set from current AWS, Azure, or Google Cloud marketplace pages—without catalogs, snapshots, or cloud accounts."),
        h("div", { className: "architecture-strip" }, h("span", null, "Interpret"), h("i", null, "→"), h("span", null, "Retrieve"), h("i", null, "→"), h("span", null, "Filter + dedupe"), h("i", null, "→"), h("span", null, "Ground or abstain"))),
      h("form", { className: "search-panel", onSubmit: research },
        h("label", null, "Research request", h("input", { value: request, onChange: event => setRequest(event.target.value), maxLength: 600, placeholder: "Find automation products on Azure" })),
        h("button", { type: "submit", disabled: loading }, loading ? "Verifying live evidence…" : "Run research agent"),
        error && h("p", { className: "form-error", role: "alert" }, error))),
    h(ResearchBrief, { brief }),
    h("section", { className: "workspace", "aria-live": "polite" },
      h("div", { className: "section-heading" },
        h("div", null, h("p", { className: "kicker" }, "Live result explorer"), h("h2", null, brief ? `Evidence for “${brief.request.search_query}”` : "One request, one evidence set")),
        brief && h("span", { className: "catalog-count" }, `Retrieved ${new Date(brief.retrieved_at).toLocaleTimeString()}`)),
      h(Results, { brief })),
    h("footer", null,
      h("span", null, "CloudMatch / live retrieval + quality-controlled ranking"),
      h("span", null, "Native MCP · no catalog · explicit abstention")));
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
