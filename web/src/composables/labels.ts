const ROLE_LABELS: Record<string, string> = {
  sales: 'Vendas',
  kitchen: 'Cozinha',
  admin: 'Admin',
}

const UNIT_LABELS: Record<string, string> = {
  serving: 'porção',
  un: 'un',
  kg: 'kg',
  L: 'L',
}

export function roleLabel(role: string): string {
  return ROLE_LABELS[role] || role
}

export function unitLabel(unit: string): string {
  return UNIT_LABELS[unit] || unit
}

export function formatQty(value: number, unit: string): string {
  if (unit === 'kg' || unit === 'L') {
    return Number(value.toFixed(3)).toString()
  }
  return Math.round(value).toString()
}
