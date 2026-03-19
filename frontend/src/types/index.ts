export type DocumentPrimitive = string | number | boolean | null;

export type DocumentDataValue =
  | DocumentPrimitive
  | DocumentDataValue[]
  | { [key: string]: DocumentDataValue | undefined };

export interface ExtractedEntity {
  text?: string;
  label?: string;
  [key: string]: DocumentDataValue | undefined;
}

export interface ExtractedData {
  filename?: string;
  file_name?: string;
  file_id?: string;
  ocr_confidence?: number;
  classification_confidence?: number;
  text?: string;
  entities?: ExtractedEntity[];
  fields?: Record<string, DocumentDataValue | undefined>;
  [key: string]: DocumentDataValue | undefined;
}

export interface Document {
  id: string;
  name: string;
  date: string;
  type: "facture" | "devis" | "attestation_urssaf" | "kbis" | "rib" | "autre";
  status: "OK" | "suspect" | "frauduleux";
  anomalies: string[];
  fields: Record<string, DocumentDataValue | undefined>;
  nomFichierDOrigine?: string;
  dateTraitement?: string;
  donneesExtraites?: ExtractedData;
}

export interface AuthStore {
  token: string | null;
  isLoggedIn: boolean;
  login: (token: string) => void;
  logout: () => void;
}

export interface DocumentsStore {
  documents: Document[];
  isLoading: boolean;
  setDocuments: (docs: Document[]) => void;
  addDocuments: (docs: Document[]) => void;
  removeDocument: (id: string) => void;
  setLoading: (loading: boolean) => void;
}

export interface SignInResponse {
  token: string;
}

export interface ApiError {
  message: string;
  status?: number;
}
