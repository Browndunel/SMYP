"""
Helpers pour générer des données françaises réalistes :
SIRET, IBAN, TVA intracommunautaire, RIB, BIC.
"""
import random
import string
from faker import Faker

_fake = Faker("fr_FR")

# ---------------------------------------------------------------------------
# Noms de l'équipe (scénario S8)
# ---------------------------------------------------------------------------

TEAM_COMPANIES: list[str] = [
    "Yoni SAS",
    "Louise Corp",
    "Ludo & Associés",
    "Brawn Dunel SARL",
    "Eloic Services EURL",
    "Loan Conseil SAS",
    "Mathis & Co SARL",
]

# ---------------------------------------------------------------------------
# SIRET / SIREN
# ---------------------------------------------------------------------------

def generate_siret() -> str:
    """Génère un SIRET de 14 chiffres (format valide mais non Luhn-vérifié)."""
    siren = "".join(str(random.randint(0, 9)) for _ in range(9))
    nic = "".join(str(random.randint(0, 9)) for _ in range(5))
    return siren + nic


def generate_tva_intra(siret: str) -> str:
    """
    Génère un numéro de TVA intracommunautaire français.
    Format : FR + clé (2 chiffres) + SIREN (9 chiffres).
    """
    siren = siret[:9]
    key = (12 + 3 * (int(siren) % 97)) % 97
    return f"FR{key:02d}{siren}"


# ---------------------------------------------------------------------------
# RIB / IBAN / BIC
# ---------------------------------------------------------------------------

def _rib_key(code_banque: str, code_guichet: str, numero_compte: str) -> int:
    """Calcule la clé RIB (comptes numériques uniquement)."""
    b = int(code_banque)
    g = int(code_guichet)
    c = int(numero_compte)
    key = 97 - ((89 * b + 15 * g + 3 * c) % 97)
    return 0 if key == 97 else key


def _iban_check_digits(bban: str) -> str:
    """Calcule les 2 chiffres de contrôle IBAN pour un BBAN français."""
    # Déplacer FR00 en fin, remplacer lettres par chiffres (F=15, R=27)
    check_input = bban + "152700"
    remainder = int(check_input) % 97
    digits = 98 - remainder
    return f"{digits:02d}"


def generate_rib_data() -> dict:
    """Génère un jeu complet de coordonnées bancaires françaises."""
    code_banque = f"{random.randint(10000, 99999)}"
    code_guichet = f"{random.randint(10000, 99999)}"
    # Numéro de compte : 11 chiffres
    numero_compte = f"{random.randint(10000000000, 99999999999)}"
    cle = _rib_key(code_banque, code_guichet, numero_compte)
    cle_str = f"{cle:02d}"
    bban = f"{code_banque}{code_guichet}{numero_compte}{cle_str}"
    check = _iban_check_digits(bban)
    iban_raw = f"FR{check}{bban}"
    # Formatage en groupes de 4
    iban_formatted = " ".join(iban_raw[i:i+4] for i in range(0, len(iban_raw), 4))
    return {
        "code_banque": code_banque,
        "code_guichet": code_guichet,
        "numero_compte": numero_compte,
        "cle_rib": cle_str,
        "iban": iban_formatted,
        "iban_raw": iban_raw,
        "bic": generate_bic(),
        "banque": _fake.company(),
    }


def generate_bic() -> str:
    """Génère un code BIC/SWIFT plausible (8 caractères)."""
    bank_code = "".join(random.choices(string.ascii_uppercase, k=4))
    country = "FR"
    location = "".join(random.choices(string.ascii_uppercase + string.digits, k=2))
    return bank_code + country + location


# ---------------------------------------------------------------------------
# Noms / adresses
# ---------------------------------------------------------------------------

_FORMES_JURIDIQUES = ["SARL", "SAS", "EURL", "SA", "SASU"]
_SECTEURS = [
    "Conseil", "Informatique", "Services", "BTP", "Commerce",
    "Industrie", "Transport", "Communication", "Finance", "Sécurité",
]


def random_company_name(team_names: list[str] | None = None) -> str:
    """Génère un nom de société.

    Si team_names est fourni, retourne directement un nom choisi dans la liste
    (les entrées sont des noms de sociétés complets, ex : "Yoni SAS").
    """
    if team_names:
        return random.choice(team_names)
    forme = random.choice(_FORMES_JURIDIQUES)
    return f"{_fake.last_name()} {random.choice(_SECTEURS)} {forme}"


def random_address() -> str:
    return (
        f"{random.randint(1, 150)} {_fake.street_name()}\n"
        f"{_fake.postcode()} {_fake.city()}"
    )


def random_person_name() -> str:
    return _fake.name()
