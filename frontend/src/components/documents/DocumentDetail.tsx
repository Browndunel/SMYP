import { AlertTriangle, AlertCircle } from 'lucide-react'
import type { Document } from '../../types'
import { Badge } from '../ui/Badge'

interface DocumentDetailProps {
  document: Document
}

const typeLabels: Record<Document['type'], string> = {
  facture: 'Facture',
  devis: 'Devis',
  attestation_urssaf: 'Attestation URSSAF',
  kbis: 'Extrait Kbis',
  rib: 'RIB',
}

const fieldLabels: Record<string, string> = {
  siret: 'SIRET',
  montant_ht: 'Montant HT',
  montant_ttc: 'Montant TTC',
  tva_rate: 'Taux TVA',
  date_emission: 'Date d\'émission',
  date_expiration: 'Date d\'expiration',
  iban: 'IBAN',
  fournisseur: 'Fournisseur',
}

function formatValue(key: string, value: string | number): string {
  if (typeof value === 'number') {
    if (key.includes('montant')) return `${value.toLocaleString('fr-FR', { minimumFractionDigits: 2 })} €`
    if (key === 'tva_rate') return `${value} %`
    return String(value)
  }
  return value
}

export function DocumentDetail({ document }: DocumentDetailProps) {
  const statusVariant = document.status === 'OK'
    ? 'ok'
    : document.status === 'suspect'
    ? 'suspect'
    : 'frauduleux'

  const fields = Object.entries(document.fields).filter(([, v]) => v !== undefined && v !== null)

  return (
    <div className="flex flex-col gap-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-medium tracking-[-0.02em] text-foreground">{document.name}</h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            {typeLabels[document.type]} · {document.date}
          </p>
        </div>
        <Badge variant={statusVariant}>{document.status}</Badge>
      </div>

      {/* Anomalies */}
      {document.anomalies.length > 0 && (
        <div className={[
          'rounded-lg border p-4',
          document.status === 'frauduleux'
            ? 'border-red-200 bg-red-50'
            : 'border-amber-200 bg-amber-50',
        ].join(' ')}>
          <div className="flex items-center gap-2 mb-2">
            {document.status === 'frauduleux' ? (
              <AlertCircle size={15} className="text-red-600" />
            ) : (
              <AlertTriangle size={15} className="text-amber-600" />
            )}
            <p className={[
              'text-[11px] font-medium uppercase tracking-[0.08em]',
              document.status === 'frauduleux' ? 'text-red-700' : 'text-amber-700',
            ].join(' ')}>
              {document.anomalies.length} anomalie{document.anomalies.length > 1 ? 's' : ''} détectée{document.anomalies.length > 1 ? 's' : ''}
            </p>
          </div>
          <ul className="space-y-1">
            {document.anomalies.map((anomaly, i) => (
              <li
                key={i}
                className={[
                  'text-sm font-mono',
                  document.status === 'frauduleux' ? 'text-red-700' : 'text-amber-700',
                ].join(' ')}
              >
                · {anomaly}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Fields */}
      {fields.length > 0 && (
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground mb-3">
            Champs extraits
          </p>
          <div className="grid grid-cols-2 gap-3">
            {fields.map(([key, value]) => (
              <div key={key} className="rounded-lg bg-muted/50 border border-border px-3 py-2.5">
                <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground">
                  {fieldLabels[key] ?? key}
                </p>
                <p className="text-sm font-medium text-foreground mt-0.5 tracking-[-0.01em]">
                  {formatValue(key, value as string | number)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {fields.length === 0 && document.anomalies.length === 0 && (
        <p className="text-sm text-muted-foreground">Aucune donnée extraite.</p>
      )}
    </div>
  )
}
