import { linkClickHandler, useRoute } from '../../app/router'

export function SiteHeader(_props: { experimental?: boolean } = {}) {
  const route = useRoute()
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
        <a href="/" onClick={linkClickHandler('/')} aria-current={route === '/' ? 'page' : undefined}>Carte</a>
        <a href="/catalogue" onClick={linkClickHandler('/catalogue')} aria-current={route === '/catalogue' ? 'page' : undefined}>Catalogue des actions</a>
        <a href="/methode" onClick={linkClickHandler('/methode')} aria-current={route === '/methode' ? 'page' : undefined}>Méthode et sources</a>
      </nav>
    </header>
    </>
  )
}
