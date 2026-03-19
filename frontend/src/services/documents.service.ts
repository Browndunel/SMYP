import { api } from "./api";
import { useAuthStore } from "../store/auth.store";
import type { Document, DocumentDataValue, ExtractedData } from "../types";

type RawDocument = Partial<Document> & {
  id?: string;
  _id?: string;
  __v?: number;
  donneeExtraites?: unknown;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function toDocumentDataValue(value: unknown): DocumentDataValue | undefined {
  if (
    value === null ||
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return value;
  }

  if (Array.isArray(value)) {
    return value
      .map((item) => toDocumentDataValue(item))
      .filter(
        (item): item is Exclude<DocumentDataValue, undefined> =>
          item !== undefined,
      );
  }

  if (isRecord(value)) {
    return Object.fromEntries(
      Object.entries(value)
        .map(([key, item]) => [key, toDocumentDataValue(item)] as const)
        .filter(([, item]) => item !== undefined),
    );
  }

  return String(value);
}

function normalizeExtractedData(value: unknown): ExtractedData | undefined {
  if (!isRecord(value)) return undefined;

  const normalized = toDocumentDataValue(value);
  if (
    !normalized ||
    Array.isArray(normalized) ||
    typeof normalized !== "object"
  )
    return undefined;

  return normalized as ExtractedData;
}

function inferDocumentType(
  raw: RawDocument,
  extracted?: ExtractedData,
): Document["type"] {
  const haystack = [
    raw.type,
    raw.nomFichierDOrigine,
    raw.name,
    extracted?.file_name,
    extracted?.filename,
    extracted?.text,
  ]
    .filter(
      (value): value is string => typeof value === "string" && value.length > 0,
    )
    .join(" ")
    .toLowerCase();

  if (haystack.includes("facture")) return "facture";
  if (haystack.includes("devis")) return "devis";
  if (haystack.includes("urssaf") || haystack.includes("attestation"))
    return "attestation_urssaf";
  if (haystack.includes("kbis")) return "kbis";
  if (haystack.includes("rib") || haystack.includes("iban")) return "rib";
  return "autre";
}

function formatDocumentDate(value?: string): string {
  if (!value) return "Date inconnue";

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;

  return parsed.toLocaleString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function collectFields(
  raw: RawDocument,
  extracted?: ExtractedData,
): Document["fields"] {
  const baseFields = isRecord(raw.fields)
    ? ((toDocumentDataValue(raw.fields) as Document["fields"] | undefined) ??
      {})
    : {};

  if (!extracted) return baseFields;

  // New structure: fields nested under extracted.fields
  if (isRecord(extracted.fields)) {
    const nestedFields =
      (toDocumentDataValue(extracted.fields) as Document["fields"] | undefined) ??
      {};
    return { ...baseFields, ...nestedFields };
  }

  // Fallback: old structure where fields were at root of extracted data
  const extractedEntries = Object.entries(extracted).filter(
    ([key, value]) =>
      ![
        "filename",
        "file_name",
        "file_id",
        "text",
        "entities",
        "ocr_confidence",
        "classification_confidence",
      ].includes(key) && value !== undefined,
  );

  return {
    ...baseFields,
    ...Object.fromEntries(extractedEntries),
  };
}

function normalize(raw: RawDocument): Document {
  const donneesExtraites = normalizeExtractedData(
    raw.donneeExtraites ?? raw.donneesExtraites,
  );
  const anomalies = Array.isArray(raw.anomalies)
    ? raw.anomalies.filter((item): item is string => typeof item === "string")
    : [];

  return {
    id: raw.id ?? raw._id ?? "",
    name:
      raw.name ??
      raw.nomFichierDOrigine ??
      donneesExtraites?.filename ??
      "Document sans nom",
    date: raw.date ?? formatDocumentDate(raw.dateTraitement),
    type: raw.type ?? inferDocumentType(raw, donneesExtraites),
    status: raw.status ?? (anomalies.length > 0 ? "suspect" : "OK"),
    anomalies,
    fields: collectFields(raw, donneesExtraites),
    nomFichierDOrigine: raw.nomFichierDOrigine,
    dateTraitement: raw.dateTraitement,
    donneesExtraites,
  };
}

function requireToken(): string {
  const { token, logout } = useAuthStore.getState();

  if (!token) {
    logout();
    throw new Error("Session invalide, reconnectez-vous");
  }

  return token;
}

export const documentsService = {
  async getDocuments(): Promise<Document[]> {
    const raw = await api.getDocuments(requireToken());
    return (raw as RawDocument[]).map(normalize);
  },

  async uploadDocuments(files: File[]): Promise<Document[]> {
    const token = requireToken();
    const results: Document[] = [];
    for (const file of files) {
      const raw = await api.uploadDocument(file, token);
      results.push(normalize(raw as RawDocument));
    }
    return results;
  },

  async deleteDocument(id: string): Promise<void> {
    return api.deleteDocument(id, requireToken());
  },
};
