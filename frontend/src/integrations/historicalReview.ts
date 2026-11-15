/** Historical technical views are retained only for explicit loopback QA. */
export function isHistoricalReview(): boolean {
  return import.meta.env.DEV === true && import.meta.env.VITE_HISTORICAL_REVIEW === '1'
    && typeof window !== 'undefined' && ['127.0.0.1','localhost'].includes(window.location.hostname)
}
