import { useEffect, useMemo, useState } from 'react'
import { SiteHeader } from '../components/layout/SiteHeader'
import { linkClickHandler, navigate } from '../app/router'
import { loadCatalogueFamilies, type CatalogueFamily, type RuleId } from '../integrations/catalogueData'

const LEVEL_LABELS: Record<string, string> = {
  rouge: 'V1 · Rouge',
  orange: 'V2 · Orange',
  jaune: 'V3 · Jaune',
  gris: 'V4 · Gris',
}

export function CataloguePage() {
  const [families, setFamilies] = useState<CatalogueFamily[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [familyFilter, setFamilyFilter] = useState<RuleId | 'all'>('all')
  const [levelFilter, setLevelFilter] = useState<string>('all')
  const [communeFilter, setCommuneFilter] = useState<string>('all')

  useEffect(() => {
    let cancelled = false
    loadCatalogueFamilies()
      .then((result) => { if (!cancelled) setFamilies(result) })
      .catch((err) => { if (!cancelled) setError(String(err)) })
    return () => { cancelled = true }
  }, [])

  const communes = useMemo(() => {
    const set = new Set<string>()
    families?.forEach((f) => f.cells.forEach((c) => c.municipalities.forEach((m) => set.add(m))))
    return Array.from(set).sort()
  }, [families])

  const visibleFamilies = useMemo(
    () => (families ?? []).filter((f) => familyFilter === 'all' || f.ruleId === familyFilter),
    [families, familyFilter],
  )

  const cellMatches = (cell: CatalogueFamily['cells'][number]) =>
    (levelFilter === 'all' || cell.documentaryLevel === levelFilter) &&
    (communeFilter === 'all' || cell.municipalities.includes(communeFilter))

  return (
    <div className="application-shell">
      <SiteHeader />
      <main className="doc-page catalogue-page" id="main-content">
        <section className="doc-hero">
          <p className="context-label">M2 · Règles R1–R4</p>
          <h1>Catalogue des pistes d’investigation</h1>
          <p className="doc-lede">
            Quatre familles de vérification documentaire issues de la spécification M2
            (R1→A04, R2→A01, R3→A03, R4→A02). Chaque fiche est une{' '}
            <strong>piste d’investigation documentaire — non validée</strong> : elle indique ce
            qu’il faut vérifier, jamais une intervention à réaliser.
          </p>
          <a className="analysis-jump" href="/" onClick={linkClickHandler('/')}>
            ← Retour à la carte
          </a>
        </section>

        {error && (
          <div className="doc-section catalogue-alert" role="alert">
            <strong>Catalogue indisponible</strong>
            <p className="doc-note" style={{ marginTop: 6 }}>{error}</p>
          </div>
        )}

        {!families && !error && <p className="doc-note">Chargement du catalogue…</p>}

        {families && (
          <>
            <div className="catalogue-filters" role="group" aria-label="Filtres du catalogue">
              <div className="filter-group">
                <span className="filter-label">Famille</span>
                {(['all', 'R1', 'R2', 'R3', 'R4'] as const).map((f) => (
                  <button
                    key={f}
                    type="button"
                    className={`filter-chip ${familyFilter === f ? 'is-active' : ''}`}
                    aria-pressed={familyFilter === f}
                    onClick={() => setFamilyFilter(f)}
                  >
                    {f === 'all' ? 'Toutes' : f}
                  </button>
                ))}
              </div>
              <div className="filter-group">
                <span className="filter-label">Niveau V</span>
                <select value={levelFilter} onChange={(e) => setLevelFilter(e.target.value)} aria-label="Filtrer par niveau documentaire">
                  <option value="all">Tous</option>
                  <option value="rouge">V1 · Rouge</option>
                  <option value="orange">V2 · Orange</option>
                  <option value="jaune">V3 · Jaune</option>
                  <option value="gris">V4 · Gris</option>
                </select>
              </div>
              <div className="filter-group">
                <span className="filter-label">Commune</span>
                <select value={communeFilter} onChange={(e) => setCommuneFilter(e.target.value)} aria-label="Filtrer par commune">
                  <option value="all">Toutes</option>
                  {communes.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
            </div>

            <div className="catalogue-grid">
              {visibleFamilies.map((family) => {
                const cells = family.cells.filter(cellMatches)
                return (
                  <article key={family.ruleId} className="catalogue-card" id={`famille-${family.ruleId}`}>
                    <header className="catalogue-card-head">
                      <div>
                        <p className="catalogue-ids">{family.ruleId} → {family.actionId}</p>
                        <h2>{family.name}</h2>
                      </div>
                      <span className="lead-badge">Piste d’investigation documentaire — non validée</span>
                    </header>

                    <p className="catalogue-question">« {family.question} »</p>

                    <dl className="catalogue-details">
                      <div><dt>Déclencheur étayé</dt><dd>{family.declarationEtayee}</dd></div>
                      <div><dt>Indice indicatif</dt><dd>{family.declarationIndicative}</dd></div>
                      <div><dt>Absence documentée</dt><dd>{family.absenceDocumentee}</dd></div>
                      <div><dt>Non évaluable</dt><dd>{family.nonEvaluable}</dd></div>
                      <div><dt>À vérifier</dt><dd>{family.aVerifier}</dd></div>
                      <div><dt>Sources</dt><dd>{family.sources.join(' · ')}</dd></div>
                    </dl>

                    <footer className="catalogue-card-foot">
                      <p className="catalogue-counts">
                        <strong>{family.leadCount}</strong> pistes à étudier sur{' '}
                        <strong>{family.cellCount}</strong> mailles
                        {cells.length !== family.cells.length && (
                          <> — <strong>{cells.length}</strong> affichée{cells.length > 1 ? 's' : ''} avec les filtres</>
                        )}
                      </p>
                      <button
                        type="button"
                        className="catalogue-map-link"
                        onClick={() => navigate(`/?famille=${family.ruleId}`)}
                      >
                        Voir les secteurs concernés →
                      </button>
                    </footer>

                    {cells.length > 0 ? (
                      <ul className="catalogue-cells" aria-label={`Mailles concernées par ${family.ruleId}`}>
                        {cells.map((cell) => (
                          <li key={cell.mailleId}>
                            <button
                              type="button"
                              className="catalogue-cell"
                              title={`${cell.mailleId} — ${cell.municipalities.join(', ')}`}
                              onClick={() => navigate(`/?famille=${family.ruleId}&maille=${encodeURIComponent(cell.mailleId)}`)}
                            >
                              <span className={`level-dot level-dot--${cell.documentaryLevel}`} aria-hidden="true" />
                              <span className="catalogue-cell-id">{cell.mailleId}</span>
                              <span className="catalogue-cell-meta">
                                {LEVEL_LABELS[cell.documentaryLevel] ?? cell.documentaryLevel}
                                {' · '}
                                {cell.municipalities.join(', ')}
                              </span>
                            </button>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="doc-note catalogue-empty">
                        Aucune maille ne correspond aux filtres pour cette famille.
                      </p>
                    )}
                  </article>
                )
              })}
            </div>

            <p className="doc-note">
              Les 404 évaluations R1–R4 (101 mailles × 4 règles) sont toutes « non évaluable » : les
              méthodes familiales ne sont pas encore validées sur ce territoire. Le décompte des
              pistes « à étudier » provient des fiches publiques (<code>cells.json</code>).
            </p>
          </>
        )}
      </main>
    </div>
  )
}
