import { linkClickHandler } from '../../app/router'

export function SiteHeader() {
  return (
    <header className="app-header">
      <a className="brand" href="/" onClick={linkClickHandler('/')} aria-label="ReConnect Normandie, retour à la carte">
        <img
          src="/images/ecological-emblem.png"
          alt="Emblème écologique ReConnect"
          className="brand-emblem"
          width="52"
          height="52"
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
        <a href="/methode" onClick={linkClickHandler('/methode')}>Méthode</a>
        <a href="/catalogue" onClick={linkClickHandler('/catalogue')}>Catalogue</a>
      </nav>
    </header>
  )
}
