PYTHON  := python3
VENV    := .venv
PIP     := $(VENV)/bin/pip
EXEC    := $(VENV)/bin/python

.DEFAULT_GOAL := help

# ── Aide ────────────────────────────────────────────────────────────────────

.PHONY: help
help:
	@echo ""
	@echo "  make install   Crée le venv et installe les dépendances"
	@echo "  make run       Lance la génération du dataset"
	@echo "  make clean     Supprime le venv"
	@echo "  make reset     Supprime le venv + le dataset généré"
	@echo ""

# ── Installation ─────────────────────────────────────────────────────────────

.PHONY: install
install: $(VENV)/bin/activate
	@echo ""
	@echo "  Environnement prêt. Lance : make run"
	@echo ""

$(VENV)/bin/activate: requirements.txt
	@echo "→ Création du venv..."
	$(PYTHON) -m venv $(VENV)
	@echo "→ Installation des dépendances..."
	$(PIP) install --upgrade pip --quiet
	$(PIP) install -r requirements.txt --quiet
	@touch $(VENV)/bin/activate

# ── Exécution ────────────────────────────────────────────────────────────────

.PHONY: run
run: $(VENV)/bin/activate
	$(EXEC) generate_dataset.py

# ── Nettoyage ────────────────────────────────────────────────────────────────

.PHONY: clean
clean:
	rm -rf $(VENV)
	@echo "→ Venv supprimé."

.PHONY: reset
reset: clean
	rm -rf dataset/
	@echo "→ Dataset supprimé."
