from pathlib import Path

# =====================================================
# SIGA CAFE ERP
# Configuración General
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Base de datos
DB_DIR = BASE_DIR / "database"
DB_DIR.mkdir(exist_ok=True)

RUTA_DB = DB_DIR / "erp_cafe.db"

# Reportes
REPORTES_DIR = BASE_DIR / "reportes"
REPORTES_DIR.mkdir(exist_ok=True)

# Exportaciones
EXPORTACIONES_DIR = BASE_DIR / "exportaciones"
EXPORTACIONES_DIR.mkdir(exist_ok=True)

# Backups
BACKUPS_DIR = BASE_DIR / "backups"
BACKUPS_DIR.mkdir(exist_ok=True)

# Logs
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)