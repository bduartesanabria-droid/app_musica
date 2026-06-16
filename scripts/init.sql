-- SEMIMUS - Script de inicialización de base de datos
-- Este script se ejecuta automáticamente al crear el contenedor Docker

-- Extensión para UUIDs (opcional)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Crear esquema si no existe
CREATE SCHEMA IF NOT EXISTS public;

-- Configurar búsqueda de esquema
SET search_path TO public;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE semimus TO semimus;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO semimus;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO semimus;
