import { createElement } from 'react'
import iconLicense from './action-family-icons.LICENSE.txt?raw'
import type { ActionFamilyVisual } from '../../integrations/actionFamilyVisuals'

/** Decorative vector: the adjacent family label and action title provide its meaning. */
export function ActionFamilyIcon({ family }: { family: ActionFamilyVisual }) {
  if (!family.iconName) return null
  return <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
    aria-hidden="true" focusable="false" data-icon={family.iconName}>
    <metadata>{iconLicense}</metadata>
    {family.iconNodes.map(([tag, attributes], index) => createElement(tag, { ...attributes, key: index }))}
  </svg>
}
