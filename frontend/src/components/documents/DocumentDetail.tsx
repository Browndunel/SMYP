import type { LucideIcon } from "lucide-react";
import {
  AlertCircle,
  AlertTriangle,
  Braces,
  CalendarClock,
  FileSearch,
  ScanText,
  Tags,
} from "lucide-react";
import type { Document, DocumentDataValue, ExtractedEntity } from "../../types";
import { Badge } from "../ui/Badge";

interface DocumentDetailProps {
  document: Document;
}

interface DetailEntry {
  label: string;
  value: DocumentDataValue | undefined;
}

const typeLabels: Record<Document["type"], string> = {
  facture: "Facture",
  devis: "Devis",
  attestation_urssaf: "Attestation URSSAF",
  kbis: "Extrait Kbis",
  rib: "RIB",
  autre: "Autre",
};

const fieldLabels: Record<string, string> = {
  siret: "SIRET",
  montant_ht: "Montant HT",
  montant_ttc: "Montant TTC",
  tva_rate: "Taux TVA",
  date_emission: "Date d'émission",
  date_expiration: "Date d'expiration",
  iban: "IBAN",
  fournisseur: "Fournisseur",
  filename: "Nom du fichier extrait",
  text: "Texte OCR",
  label: "Label",
  nomFichierDOrigine: "Nom du fichier d'origine",
  dateTraitement: "Date de traitement",
  type: "Type détecté",
  status: "Statut",
  entitiesCount: "Nombre d'entités",
};

function isRecord(
  value: DocumentDataValue | undefined,
): value is Record<string, DocumentDataValue | undefined> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasDisplayValue(value: DocumentDataValue | undefined): boolean {
  if (value === undefined || value === null) return false;
  if (typeof value === "string") return value.trim().length > 0;
  if (typeof value === "number" || typeof value === "boolean") return true;
  if (Array.isArray(value)) return value.some((item) => hasDisplayValue(item));
  return Object.values(value).some((item) => hasDisplayValue(item));
}

function formatLabel(key: string): string {
  if (fieldLabels[key]) return fieldLabels[key];

  return key
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/^\w/, (letter) => letter.toUpperCase());
}

function formatDate(value: string): string {
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

function formatPrimitiveValue(
  key: string,
  value: string | number | boolean | null,
): string {
  if (value === null) return "Non renseigné";

  if (typeof value === "boolean") {
    return value ? "Oui" : "Non";
  }

  if (typeof value === "number") {
    if (/montant|total|prix/i.test(key)) {
      return `${value.toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;
    }

    if (/tva|rate|taux|percent/i.test(key)) {
      return `${value} %`;
    }

    return value.toLocaleString("fr-FR");
  }

  if (/date/i.test(key)) {
    return formatDate(value);
  }

  return value;
}

function renderValue(
  name: string,
  value: DocumentDataValue | undefined,
): JSX.Element {
  if (!hasDisplayValue(value)) {
    return <p className="text-sm text-muted-foreground">Non renseigné</p>;
  }

  if (
    value === null ||
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return (
      <p className="text-sm font-medium text-foreground mt-0.5 whitespace-pre-wrap break-words">
        {formatPrimitiveValue(name, value)}
      </p>
    );
  }

  if (Array.isArray(value)) {
    const primitiveItems = value.every(
      (item) =>
        item === null ||
        typeof item === "string" ||
        typeof item === "number" ||
        typeof item === "boolean",
    );

    if (primitiveItems) {
      return (
        <div className="flex flex-wrap gap-2 mt-1">
          {value.map((item, index) => (
            <span
              key={`${name}-${index}`}
              className="inline-flex rounded-full border border-border bg-muted px-2.5 py-1 text-xs text-foreground"
            >
              {formatPrimitiveValue(
                name,
                item as string | number | boolean | null,
              )}
            </span>
          ))}
        </div>
      );
    }

    return (
      <div className="space-y-2 mt-1">
        {value.map((item, index) => (
          <div
            key={`${name}-${index}`}
            className="rounded-lg border border-border bg-background px-3 py-2.5"
          >
            {renderValue(`${name}_${index}`, item)}
          </div>
        ))}
      </div>
    );
  }

  if (!isRecord(value)) {
    return (
      <p className="text-sm text-muted-foreground">Aucune donnée disponible.</p>
    );
  }

  return (
    <EntryGrid
      entries={Object.entries(value).map(([key, item]) => ({
        label: key,
        value: item,
      }))}
    />
  );
}

function EntryGrid({ entries }: { entries: DetailEntry[] }) {
  const visibleEntries = entries.filter(({ value }) => hasDisplayValue(value));

  if (visibleEntries.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">Aucune donnée disponible.</p>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {visibleEntries.map(({ label, value }) => (
        <div
          key={label}
          className="rounded-lg border border-border bg-muted/30 px-3 py-2.5"
        >
          <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground">
            {formatLabel(label)}
          </p>
          {renderValue(label, value)}
        </div>
      ))}
    </div>
  );
}

function DetailSection({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: LucideIcon;
  children: JSX.Element;
}) {
  return (
    <section className="space-y-3">
      <div className="flex items-center gap-2">
        <Icon size={15} className="text-muted-foreground" />
        <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground">
          {title}
        </p>
      </div>
      {children}
    </section>
  );
}

function EntitiesSection({ entities }: { entities: ExtractedEntity[] }) {
  return (
    <div className="space-y-2">
      {entities.map((entity, index) => {
        const { text, label, ...rest } = entity;
        const extraEntries = Object.entries(rest).map(([key, value]) => ({
          label: key,
          value,
        }));

        return (
          <div
            key={`${label ?? "entity"}-${index}`}
            className="rounded-lg border border-border bg-card px-4 py-3"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm font-medium text-foreground break-words">
                  {typeof text === "string" && text.trim().length > 0
                    ? text
                    : "Entité sans texte"}
                </p>
              </div>
              <Badge variant="outline" className="shrink-0">
                {typeof label === "string" && label.trim().length > 0
                  ? label
                  : "Sans label"}
              </Badge>
            </div>

            {extraEntries.length > 0 && (
              <div className="mt-3">
                <EntryGrid entries={extraEntries} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export function DocumentDetail({ document }: DocumentDetailProps) {
  const statusVariant =
    document.status === "OK"
      ? "ok"
      : document.status === "suspect"
        ? "suspect"
        : "frauduleux";

  const anomalies = document.anomalies ?? [];
  const fieldsEntries = Object.entries(document.fields ?? {}).map(
    ([label, value]) => ({ label, value }),
  );
  const entities = Array.isArray(document.donneesExtraites?.entities)
    ? document.donneesExtraites.entities.filter(
        (entity): entity is ExtractedEntity => isRecord(entity),
      )
    : [];
  const extractedText =
    typeof document.donneesExtraites?.text === "string"
      ? document.donneesExtraites.text.trim()
      : "";

  const summaryEntries: DetailEntry[] = [
    {
      label: "nomFichierDOrigine",
      value: document.nomFichierDOrigine ?? document.name,
    },
    { label: "filename", value: document.donneesExtraites?.filename },
    {
      label: "dateTraitement",
      value: document.dateTraitement ?? document.date,
    },
    { label: "type", value: typeLabels[document.type] },
    { label: "status", value: document.status },
    {
      label: "entitiesCount",
      value: entities.length > 0 ? entities.length : undefined,
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-medium tracking-[-0.02em] text-foreground">
            {document.name}
          </h2>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {typeLabels[document.type]} · {document.date}
          </p>
        </div>
        <Badge variant={statusVariant}>{document.status}</Badge>
      </div>

      {anomalies.length > 0 && (
        <div
          className={[
            "rounded-lg border p-4",
            document.status === "frauduleux"
              ? "border-red-200 bg-red-50"
              : "border-amber-200 bg-amber-50",
          ].join(" ")}
        >
          <div className="mb-2 flex items-center gap-2">
            {document.status === "frauduleux" ? (
              <AlertCircle size={15} className="text-red-600" />
            ) : (
              <AlertTriangle size={15} className="text-amber-600" />
            )}
            <p
              className={[
                "text-[11px] font-medium uppercase tracking-[0.08em]",
                document.status === "frauduleux"
                  ? "text-red-700"
                  : "text-amber-700",
              ].join(" ")}
            >
              {anomalies.length} anomalie{anomalies.length > 1 ? "s" : ""}{" "}
              détectée{anomalies.length > 1 ? "s" : ""}
            </p>
          </div>
          <ul className="space-y-1">
            {anomalies.map((anomaly, index) => (
              <li
                key={`${anomaly}-${index}`}
                className={[
                  "text-sm font-mono",
                  document.status === "frauduleux"
                    ? "text-red-700"
                    : "text-amber-700",
                ].join(" ")}
              >
                · {anomaly}
              </li>
            ))}
          </ul>
        </div>
      )}

      <DetailSection title="Vue d'ensemble" icon={FileSearch}>
        <EntryGrid entries={summaryEntries} />
      </DetailSection>

      {fieldsEntries.length > 0 && (
        <DetailSection title="Données extraites" icon={Braces}>
          <EntryGrid entries={fieldsEntries} />
        </DetailSection>
      )}

      {entities.length > 0 && (
        <DetailSection title="Entités détectées" icon={Tags}>
          <EntitiesSection entities={entities} />
        </DetailSection>
      )}

      {extractedText.length > 0 && (
        <DetailSection title="Texte OCR brut" icon={ScanText}>
          <div className="rounded-lg border border-border bg-card px-4 py-3">
            <pre className="whitespace-pre-wrap break-words font-sans text-sm leading-6 text-foreground">
              {extractedText}
            </pre>
          </div>
        </DetailSection>
      )}

      {fieldsEntries.length === 0 &&
        anomalies.length === 0 &&
        entities.length === 0 &&
        extractedText.length === 0 && (
          <div className="rounded-lg border border-dashed border-border px-4 py-6 text-center">
            <CalendarClock
              size={18}
              className="mx-auto text-muted-foreground"
            />
            <p className="mt-2 text-sm text-muted-foreground">
              Aucune donnée extraite à afficher.
            </p>
          </div>
        )}
    </div>
  );
}
