import { useEffect } from 'react'
import { DEPARTMENTS_BY_CODE, NORMANDY_DEPARTMENTS, type DepartmentCode } from './normandyDepartments'

interface DepartmentPanelProps {
  selectedDepartment: DepartmentCode | null
  hoveredDepartment: DepartmentCode | null
  onSelectDepartment: (code: DepartmentCode | null) => void
  onHoverDepartment: (code: DepartmentCode | null) => void
}

export function DepartmentPanel({
  selectedDepartment,
  hoveredDepartment,
  onSelectDepartment,
  onHoverDepartment,
}: DepartmentPanelProps) {
  const selected = selectedDepartment ? DEPARTMENTS_BY_CODE.get(selectedDepartment) : undefined

  useEffect(() => () => onHoverDepartment(null), [onHoverDepartment])

  const select = (code: DepartmentCode | null) => {
    onHoverDepartment(null)
    onSelectDepartment(code)
  }

  return (
    <div className="department-panel">
      <nav className="department-crumbs" aria-label="Niveau géographique">
        {selected ? (
          <>
            <button type="button" onClick={() => select(null)}>
              Normandie
            </button>
            <span aria-hidden="true">›</span>
            <span aria-current="location">{selected.name}</span>
          </>
        ) : (
          <span aria-current="location">Normandie</span>
        )}
      </nav>

      <div className="department-summary" aria-live="polite">
        {selected ? (
          <>
            <p className="context-label">Département {selected.code}</p>
            <h2>{selected.name}</h2>
            <dl className="department-facts">
              <div>
                <dt>Code INSEE</dt>
                <dd>{selected.code}</dd>
              </div>
              <div>
                <dt>Région</dt>
                <dd>Normandie (28)</dd>
              </div>
              <div>
                <dt>Prédiagnostic</dt>
                <dd>Analyse non réalisée</dd>
              </div>
            </dl>
            <p className="department-note">
              Aucune priorité n’est attribuée à l’échelle départementale. Les diagnostics seront
              affichés uniquement dans le territoire pilote.
            </p>
          </>
        ) : (
          <>
            <p className="context-label">Région Normandie</p>
            <h2>Choisir un département</h2>
            <p className="department-note">
              Survolez ou sélectionnez un département sur la carte ou dans la liste pour le cadrer.
            </p>
          </>
        )}
      </div>

      <ul className="department-list" onMouseLeave={() => onHoverDepartment(null)}>
        {NORMANDY_DEPARTMENTS.map((department) => (
          <li key={department.code}>
            <button
              type="button"
              className="department-item"
              aria-pressed={department.code === selectedDepartment}
              data-hovered={department.code === hoveredDepartment || undefined}
              onClick={() => select(department.code === selectedDepartment ? null : department.code)}
              onMouseEnter={() => onHoverDepartment(department.code)}
              onFocus={() => onHoverDepartment(department.code)}
              onBlur={() => onHoverDepartment(null)}
            >
              <span
                className="department-swatch"
                style={{ background: department.color }}
                aria-hidden="true"
              />
              <span className="department-name">{department.name}</span>
              <span className="department-code">{department.code}</span>
            </button>
          </li>
        ))}
      </ul>

      <p className="department-source">
        Limites : IGN – ADMIN EXPRESS COG CARTO, Licence Ouverte 2.0
      </p>
    </div>
  )
}
