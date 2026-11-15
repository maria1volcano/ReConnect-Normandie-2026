import { linkClickHandler } from '../../app/router'

export function SiteHeader({ experimental = false }: { experimental?: boolean } = {}) {
  return (
    <><header className="app-header">
      <a className="brand" href="/" onClick={linkClickHandler('/')} aria-label="ReConnect Normandie, retour à la carte">
        <img
          src="/assets/reconnect-normandie-symbole.png"
          alt=""
          className="brand-symbol"
          width="814"
          height="653"
        />
        <span className="brand-text">
          <strong>
            ReConnect <span className="brand-normandie">Normandie</span>
            <img
              src="/images/normandy-flag.png"
              alt="Drapeau de la Normandie"
              className="brand-flag-inline"
              width="28"
              height="19"
            />
          </strong>
          <small>Prédiagnostic des continuités écologiques</small>
        </span>
      </a>

      <nav className="header-nav" aria-label="Navigation principale">
        <a href="/" onClick={linkClickHandler('/')}>Carte</a>
        <a href="/methode" onClick={linkClickHandler('/methode')}>{experimental ? 'Méthode et sources' : 'Méthode'}</a>
        {!experimental && <a href="/catalogue" onClick={linkClickHandler('/catalogue')}>Catalogue</a>}
      </nav>
    </header>
    {!experimental && <p className="public-release-notice" role="note">Version publique : données actuellement autorisées. Le nouveau parcours multi-actions reste en validation locale.</p>}
    </>
  )
}
