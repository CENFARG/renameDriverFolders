# Crear Service Role Key para Supabase

## Paso 1: Ir al panel de Supabase

1. Ir a: https://supabase.com/dashboard/project/uenywfvtuulcjelouork
2. En el menú lateral, hacer clic en **"Settings"** (icono de engranaje)

## Paso 2: Crear nueva API Key

1. Bajar hasta la sección **"API"**
2. Hacer clic en **"Create API Key"**
3. En "Name/Description", poner: `Claude Code Service Role`
4. IMPORTANTE: Seleccionar **"Service Role (secret)"** - NO "Anon key"
5. Hacer clic en **"Generate"**

## Paso 3: Copiar y guardar en Secret Manager

La key se verá algo como: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

Copiarla y ejecutar:

```bash
gcloud secrets create "supabase-service-role-key" "LA_KEY_AQUI" \
    --project cloud-functions-474716
```

## Paso 4: Ejecutar script nuevamente

Una vez creada la key, el script `create_algorithms_supabase.py` la usará automáticamente.

---

## ¿Por qué Service Role y no Anon Key?

- **Anon Key**: Solo permite operaciones con RLS (Row Level Security)
- **Service Role**: Ignora RLS y puede ejecutar SQL arbitrario
- Necesitamos Service Role para CREAR tablas y ejecutar SQL complejos

---

## ALTERNATIVA: Crear tabla manualmente

Si no querés crear service role key, podés crear la tabla manualmente:

1. Ir a: https://supabase.com/dashboard/project/uenywfvtuulcjelouork/sql
2. Copiar y pegar el SQL de `scripts/create_algorithms_table.sql`
3. Ejecutar
4. Luego usaré un script para insertar los algoritmos con la anon key
