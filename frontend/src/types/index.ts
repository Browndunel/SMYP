export interface Document {
  id: string
  name: string
  date: string
  type: 'facture' | 'devis' | 'attestation_urssaf' | 'kbis' | 'rib'
  status: 'OK' | 'suspect' | 'frauduleux'
  anomalies: string[]
  fields: {
    siret?: string
    montant_ht?: number
    montant_ttc?: number
    tva_rate?: number
    date_emission?: string
    date_expiration?: string
    iban?: string
    fournisseur?: string
  }
}

export interface AuthStore {
  token: string | null
  isLoggedIn: boolean
  login: (token: string) => void
  logout: () => void
}

export interface DocumentsStore {
  documents: Document[]
  isLoading: boolean
  setDocuments: (docs: Document[]) => void
  addDocuments: (docs: Document[]) => void
  removeDocument: (id: string) => void
  setLoading: (loading: boolean) => void
}

export interface SignInResponse {
  token: string
}

export interface ApiError {
  message: string
  status?: number
}
