/*! @license
ISC License

Copyright (c) 2026 Lucide Icons and Contributors

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
*/
/** Presentation only. Four local Lucide SVGs (ISC), no runtime download.
 * Source: https://github.com/lucide-icons/lucide/tree/c55aab36b553a7de50a0050e7042fd7b2d64664e/icons
 * Notice: ../components/experimental/action-family-icons.LICENSE.txt
 * Add a family here with its label, accent, icon background and vector nodes.
 * These theme colors never encode justification, ecological priority or works.
 */
export interface ActionFamilyVisual {
  label: string
  color: string
  iconBackground: string
  iconName: string | null
  iconNodes: ReadonlyArray<readonly [string, Readonly<Record<string, string>>]>
}
const ICONS: Record<string, ActionFamilyVisual['iconNodes']> = {
  "Trees": [
    [
      "path",
      {
        "d": "M10 10v.2A3 3 0 0 1 8.9 16H5a3 3 0 0 1-1-5.8V10a3 3 0 0 1 6 0Z"
      }
    ],
    [
      "path",
      {
        "d": "M7 16v6"
      }
    ],
    [
      "path",
      {
        "d": "M13 19v3"
      }
    ],
    [
      "path",
      {
        "d": "M12 19h8.3a1 1 0 0 0 .7-1.7L18 14h.3a1 1 0 0 0 .7-1.7L16 9h.2a1 1 0 0 0 .8-1.7L13 3l-1.4 1.5"
      }
    ]
  ],
  "Droplets": [
    [
      "path",
      {
        "d": "M7 16.3c2.2 0 4-1.83 4-4.05 0-1.16-.57-2.26-1.71-3.19S7.29 6.75 7 5.3c-.29 1.45-1.14 2.84-2.29 3.76S3 11.1 3 12.25c0 2.22 1.8 4.05 4 4.05z"
      }
    ],
    [
      "path",
      {
        "d": "M12.56 6.6A10.97 10.97 0 0 0 14 3.02c.5 2.5 2 4.9 4 6.5s3 3.5 3 5.5a6.98 6.98 0 0 1-11.91 4.97"
      }
    ]
  ],
  "Sprout": [
    [
      "path",
      {
        "d": "M14 9.536V7a4 4 0 0 1 4-4h1.5a.5.5 0 0 1 .5.5V5a4 4 0 0 1-4 4 4 4 0 0 0-4 4c0 2 1 3 1 5a5 5 0 0 1-1 3"
      }
    ],
    [
      "path",
      {
        "d": "M4 9a5 5 0 0 1 8 4 5 5 0 0 1-8-4"
      }
    ],
    [
      "path",
      {
        "d": "M5 21h14"
      }
    ]
  ],
  "Route": [
    [
      "path",
      {
        "d": "M9 5h8.5a1 1 0 010 7h-11a1 1 0 000 7H15"
      }
    ],
    [
      "circle",
      {
        "cx": "18",
        "cy": "19",
        "r": "3"
      }
    ],
    [
      "circle",
      {
        "cx": "6",
        "cy": "5",
        "r": "3"
      }
    ]
  ]
}
export const ACTION_FAMILY_VISUALS: Readonly<Record<string, ActionFamilyVisual>> = {
  A01: {label: 'Haies', color: '#287A49', iconBackground: '#EDF5F0', iconName: 'Trees', iconNodes: ICONS.Trees},
  A02: {label: 'Milieux humides', color: '#247EB0', iconBackground: '#EDF5FA', iconName: 'Droplets', iconNodes: ICONS.Droplets},
  A03: {label: 'Friches', color: '#98662C', iconBackground: '#FAF3E9', iconName: 'Sprout', iconNodes: ICONS.Sprout},
  A04: {label: 'Franchissements pour la faune', color: '#6862A8', iconBackground: '#F2F1FA', iconName: 'Route', iconNodes: ICONS.Route},
}
const UNKNOWN_FAMILY: ActionFamilyVisual = {
  label: 'Famille à documenter', color: '#819389', iconBackground: '#F1F4F2', iconName: null, iconNodes: [],
}
export function actionFamilyVisual(actionId: string): ActionFamilyVisual {
  return Object.hasOwn(ACTION_FAMILY_VISUALS, actionId) ? ACTION_FAMILY_VISUALS[actionId] : UNKNOWN_FAMILY
}
