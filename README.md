# SonarQ-Agnostic

Visualizador web para reportes de calidad de **SonarQube/SonarCloud** con backend en FastAPI y frontend en HTML/CSS/JS.

Este repositorio está organizado como un proyecto full-stack simple:

- `backend/`: API, lógica de sincronización, persistencia local (SQLite) y tests
- `frontend/`: interfaz de usuario (dashboard, issues, tendencias)
- `specs/`: especificaciones funcionales y técnicas del feature actual

---

## ✨ Características principales

- Gestión de conexiones a SonarQube/SonarCloud
- Sincronización de proyectos
- Dashboard con métricas clave (bugs, vulnerabilities, code smells, coverage)
- Navegación y filtrado de issues
- Tendencias históricas
- Almacenamiento local en SQLite para consulta offline

---

## 🧱 Estructura del repositorio

```text
SonarQ-Agnostic/
├── backend/                    # FastAPI app + tests + pyproject
├── frontend/                   # HTML/CSS/JS app
├── specs/001-sonarqube-report-viewer/
│   ├── spec.md
│   ├── plan.md
│   ├── tasks.md
│   ├── quickstart.md
│   └── contracts/openapi.yaml
├── sonar-project.properties    # Config para análisis de Sonar
└── README.md                   # Este archivo
```

---

## 🚀 Inicio rápido

### Prerrequisitos

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) recomendado

### 1) Instalar dependencias

Desde la raíz del repo:

```bash
cd backend
uv sync
```

### 2) Configurar entorno

```bash
cp .env.example .env
```

Edita `backend/.env` con tus valores (por ejemplo URL y token de SonarQube/SonarCloud).

### 3) Levantar la aplicación

```bash
uv run uvicorn src.main:app --reload --port 8000
```

Abrir en navegador:

- http://localhost:8000

---

## 🧪 Testing y calidad

Desde la raíz del repo:

```bash
uv run pytest backend/tests/ --tb=short -q
```

Con cobertura:

```bash
uv run pytest backend/tests/ --cov=backend/src --cov-report=term-missing --tb=short -q
```

Lint (desde `backend/`):

```bash
uv run ruff check .
uv run ruff format .
```

---

## 🔌 Endpoints API (resumen)

- `GET /api/health`
- `GET /api/connections`
- `POST /api/connections`
- `POST /api/connections/{id}/test`
- `GET /api/projects`
- `POST /api/projects/{id}/refresh`
- `GET /api/projects/{id}/issues`
- `GET /api/projects/{id}/trends`

Contrato OpenAPI:

- `specs/001-sonarqube-report-viewer/contracts/openapi.yaml`

---

## 📚 Documentación relacionada

- Backend guide: `backend/README.md`
- Feature spec: `specs/001-sonarqube-report-viewer/spec.md`
- Plan técnico: `specs/001-sonarqube-report-viewer/plan.md`
- Tareas: `specs/001-sonarqube-report-viewer/tasks.md`
- Quickstart del feature: `specs/001-sonarqube-report-viewer/quickstart.md`

---

## 🤝 Contribución

1. Crear rama feature/fix.
2. Hacer cambios pequeños y testeables.
3. Ejecutar tests y lint antes de abrir PR.
4. Mantener consistencia con los docs de `specs/`.

---

## 📝 Estado actual

El proyecto implementa el feature `001-sonarqube-report-viewer` con cobertura de pruebas en backend y validaciones de calidad activas en el flujo de desarrollo.
