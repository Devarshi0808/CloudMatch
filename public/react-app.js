const { createElement: h, useState } = React;

const marketplaceNames = { aws: "AWS", azure: "Azure", gcp: "Google Cloud" };

function ResultCard({ match }) {
  return h("article", { className: "match-card" },
    h("div", { className: "match-card-top" },
      h("div", null,
        h("span", { className: "eyebrow" }, match.vendor),
        h("h3", null, match.solution)
      ),
      h("strong", { className: "score" }, `${match.score}%`)
    ),
    h("p", { className: "match-type" }, "Catalog match"),
    h("ul", { className: "evidence" }, match.evidence.map(item => h("li", { key: item }, item)))
  );
}

function App() {
  const [vendor, setVendor] = useState("");
  const [solution, setSolution] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function search(event) {
    event.preventDefault();
    if (!vendor.trim() && !solution.trim()) return setError("Enter a vendor, product, or both.");
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ vendor: vendor.trim(), solution: solution.trim() })
      });
      const next = await response.json();
      if (!response.ok || next.status !== "success") throw new Error(next.message || "Search failed");
      setData(next.results);
    } catch (searchError) {
      setError(searchError.message);
    } finally {
      setLoading(false);
    }
  }

  return h("main", { className: "app-shell" },
    h("nav", { className: "topbar" },
      h("div", { className: "brand" }, h("span", { className: "brand-mark" }, "CM"), h("span", null, "CloudMatch")),
      h("div", { className: "system-status" }, h("span", { className: "status-dot" }), "Hybrid retrieval online")
    ),
    h("section", { className: "hero" },
      h("div", { className: "hero-copy" },
        h("p", { className: "kicker" }, "Marketplace intelligence / v2"),
        h("h1", null, "Find the right cloud product, with evidence."),
        h("p", { className: "hero-text" }, "Ranked catalog matching for vendor and product discovery across AWS, Azure, and Google Cloud."),
        h("div", { className: "architecture-strip" },
          h("span", null, "Normalize"), h("i", null, "→"), h("span", null, "Retrieve"), h("i", null, "→"), h("span", null, "Explain"), h("i", null, "→"), h("span", null, "LLM tail")
        )
      ),
      h("form", { className: "search-panel", onSubmit: search },
        h("label", null, "Vendor", h("input", { value: vendor, onChange: event => setVendor(event.target.value), placeholder: "Red Hat, Adobe, Microsoft" })),
        h("label", null, "Product or solution", h("input", { value: solution, onChange: event => setSolution(event.target.value), placeholder: "Ansible, Photoshop, Office 365" })),
        h("button", { type: "submit", disabled: loading }, loading ? "Ranking..." : "Rank matches"),
        error && h("p", { className: "form-error" }, error)
      )
    ),
    h("section", { className: "workspace" },
      h("div", { className: "section-heading" },
        h("div", null, h("p", { className: "kicker" }, "Results"), h("h2", null, data ? `Matches for ${data.query}` : "Start with a vendor or product")),
        data && h("span", { className: "catalog-count" }, `${data.catalog_size} catalog records`)
      ),
      data ? h("div", { className: "results-grid" },
        h("div", { className: "match-list" }, data.matches.length ? data.matches.map(match => h(ResultCard, { key: `${match.vendor}-${match.solution}`, match })) : h("div", { className: "empty-state" }, "No catalog candidates met the ranking threshold.")),
        h("aside", { className: "insight-panel" },
          h("p", { className: "kicker" }, "External discovery"),
          h("h3", null, "Search live marketplaces"),
          h("p", null, "These links open each provider's search page. They are not presented as verified listings."),
          h("div", { className: "provider-links" }, Object.entries(data.marketplace_links).map(([key, url]) => h("a", { href: url, target: "_blank", rel: "noreferrer", key: key }, `${marketplaceNames[key]} ↗`))),
          h("div", { className: "llm-box" }, h("span", { className: "llm-badge" }, data.llm?.enabled ? "LLM enabled" : "LLM optional"), h("p", null, data.llm?.suggestions?.length ? data.llm.suggestions.join(" · ") : "Deterministic ranking is active. Configure OPENAI_API_KEY for query suggestions."))
        )
      ) : h("div", { className: "empty-state initial" }, "Your ranked results will appear here. Try “Red Hat” to see vendor-only retrieval."),
    ),
    h("footer", null, h("span", null, "CloudMatch / explainable retrieval"), h("span", null, "MCP-compatible tools at /api/mcp"))
  );
}

document.body.innerHTML = '<div id="root"></div>';
ReactDOM.createRoot(document.getElementById("root")).render(h(App));
