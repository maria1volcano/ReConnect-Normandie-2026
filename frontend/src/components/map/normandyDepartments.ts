export type DepartmentCode = '14' | '27' | '50' | '61' | '76'

export interface NormandyDepartment {
  code: DepartmentCode
  name: string
  color: string
  /** [west, south, east, north], from the IGN ADMIN EXPRESS COG CARTO geometry in normandy-departments.geojson */
  bounds: [[number, number], [number, number]]
}

export const NORMANDY_DEPARTMENTS: NormandyDepartment[] = [
  { code: '14', name: 'Calvados', color: '#7D8FB3', bounds: [[-1.1598, 48.7517], [0.4465, 49.4299]] },
  { code: '27', name: 'Eure', color: '#B48A9E', bounds: [[0.2967, 48.6664], [1.8029, 49.4853]] },
  { code: '50', name: 'Manche', color: '#6E9C93', bounds: [[-1.9487, 48.4558], [-0.7348, 49.7276]] },
  { code: '61', name: 'Orne', color: '#A79A6B', bounds: [[-0.8606, 48.1799], [0.9766, 48.9725]] },
  { code: '76', name: 'Seine-Maritime', color: '#8C7FB0', bounds: [[0.0657, 49.2507], [1.7908, 50.0722]] },
]

export const DEPARTMENTS_BY_CODE = new Map(NORMANDY_DEPARTMENTS.map((d) => [d.code, d]))

export function isDepartmentCode(value: unknown): value is DepartmentCode {
  return typeof value === 'string' && DEPARTMENTS_BY_CODE.has(value as DepartmentCode)
}
