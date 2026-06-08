import styles from "./page.module.css";

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <h1>Indian Startup Ecosystem RAG</h1>
        <p>Search and explore Indian startups using hybrid search + LLM.</p>
      </main>
    </div>
  );
}
