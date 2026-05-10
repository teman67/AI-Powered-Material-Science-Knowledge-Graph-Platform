const cards = [
  {
    title: "Documents",
    description: "Upload PDFs and track extraction status.",
  },
  {
    title: "Chat",
    description: "Ask scientific questions with RAG-backed answers.",
  },
  {
    title: "Graph",
    description: "Explore material, property, and process relations.",
  },
  {
    title: "RDF",
    description: "Export and validate RDF triples with SHACL.",
  },
];

export default function Home() {
  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Phase 0 Scaffold</p>
        <h1>AI-Powered Material Science Knowledge Graph Platform</h1>
        <p>
          Frontend shell is active. Next step is wiring upload, chat, graph, and RDF pages to backend APIs.
        </p>
      </section>

      <section className="grid">
        {cards.map((card) => (
          <article key={card.title} className="card">
            <h2>{card.title}</h2>
            <p>{card.description}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
