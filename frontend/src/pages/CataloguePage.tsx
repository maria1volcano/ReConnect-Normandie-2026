import { useEffect, useMemo, useState } from 'react'
import { SiteHeader } from '../components/layout/SiteHeader'
import { linkClickHandler, navigate } from '../app/router'
import { loadCatalogueFamilies, type CatalogueFamily, type RuleId } from '../integrations/catalogueData'

const LEVEL_LABELS: Record<string, string> = {
  rouge: 'Secteur à examiner en priorité',
  orange: 'Priorité d’examen élevée',
  jaune: 'Priorité d’examen modérée',
  gris: 'Informations insuffisantes',
}

function readable(text: string) { return text.replace(/\bR[1-4]\b/g,'de cette famille').replace(/\bA0[1-4]\b/g,'de cette famille').replace(/SRCE/g,'schéma régional des continuités écologiques').replace(/conflit_potentiel/g,'pression potentielle à qualifier').replace(/obstacle_confirme/g,'obstacle confirmé par expertise') }

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
          <p className="context-label">Actions et pistes conservées</p>
          <h1>Actions à étudier et pistes historiques</h1>
          <p className="doc-lede">
            Les actions à instruire sont sélectionnées dans chaque fiche territoriale. Les pistes historiques restent consultables ici ; elles ne constituent pas des travaux validés. Les conditions propres à chaque famille doivent être vérifiées.
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
                    {f === 'all' ? 'Toutes' : ({R1: 'Faune', R2: 'Bocage', R3: 'Friches', R4: 'Milieux humides'} as const)[f]}
                  </button>
                ))}
              </div>
              <div className="filter-group">
                <span className="filter-label">Examen territorial</span>
                <select value={levelFilter} onChange={(e) => setLevelFilter(e.target.value)} aria-label="Filtrer par niveau documentaire">
                  <option value="all">Tous</option>
                  <option value="rouge">Secteur à examiner en priorité</option>
                  <option value="orange">Priorité d’examen élevée</option>
                  <option value="jaune">Priorité d’examen modérée</option>
                  <option value="gris">Informations insuffisantes</option>
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

                        <h2>{family.name}</h2>
                      </div>
                      <span className="lead-badge">Famille à qualifier</span>
                    </header>

                    <p className="catalogue-question">« {family.question} »</p>

                    <dl className="catalogue-details">
                      <div><dt>Déclencheur étayé</dt><dd>{readable(family.declarationEtayee)}</dd></div>
                      <div><dt>Indice indicatif</dt><dd>{readable(family.declarationIndicative)}</dd></div>
                      <div><dt>Absence documentée</dt><dd>{readable(family.absenceDocumentee)}</dd></div>
                      <div><dt>Non évaluable</dt><dd>{readable(family.nonEvaluable)}</dd></div>
                      <div><dt>À vérifier</dt><dd>{readable(family.aVerifier)}</dd></div>
                      <div><dt>Sources</dt><dd>{family.sources.map(readable).join(' · ')}</dd></div>
                    </dl>

                    <footer className="catalogue-card-foot">
                      <p className="catalogue-counts">
                        {family.selectedCount === null ? 'Décisions du nouveau lot indisponibles dans cet export.' : <><strong>{family.selectedCount}</strong> sélection(s) d’étude par maille dans le lot chargé.</>}<br /><strong>{family.leadCount}</strong> pistes historiques sur{' '}
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
                      <ul className="catalogue-cells" aria-label={`Mailles concernées par ${family.name}`}>
                        {cells.map((cell) => (
                          <li key={cell.mailleId}>
                            <button
                              type="button"
                              className="catalogue-cell"
                              title={`${cell.municipalities.join(', ')} — secteur ${cell.sectorNumber}`}
                              onClick={() => navigate(`/?famille=${family.ruleId}&maille=${encodeURIComponent(cell.mailleId)}`)}
                            >
                              <span className={`level-dot level-dot--${cell.documentaryLevel}`} aria-hidden="true" />
                              <span className="catalogue-cell-id">{cell.municipalities.join(' / ')} — secteur {cell.sectorNumber}</span>
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
              Les 404 examens de familles (101 mailles × 4 familles) sont toutes « non évaluable » : les
              méthodes écologiques nécessaires ne sont pas encore validées sur ce territoire. Le décompte des
              pistes historiques provient des fiches de la source chargée ; ces pistes ne sont pas des sélections de restauration.
            </p>
          </>
        )}
      </main>
    </div>
  )
}
