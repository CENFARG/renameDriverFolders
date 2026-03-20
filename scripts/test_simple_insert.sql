-- Script de prueba simplificado
-- Ejecutar esto primero para verificar que la tabla se crea correctamente

-- Paso 1: Crear tabla simple para prueba
CREATE TABLE IF NOT EXISTS test_algorithms (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(500) NOT NULL
);

-- Paso 2: Insert simple (sin JSON, sin texto largo)
INSERT INTO test_algorithms (id, name) VALUES
('test1', 'Algoritmo de Prueba 1');

-- Paso 3: Verificar
SELECT * FROM test_algorithms;
