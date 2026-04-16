# PATCH: Clasificación Automática de Documentos
# ================================================
#
# Este patch agrega soporte para clasificación automática de documentos
# con múltiples algoritmos específicos.
#
# Flujo:
# 1. Clasificar documento (determinar tipo)
# 2. Buscar algoritmo correspondiente
# 3. Aplicar instrucciones específicas
# 4. Renombrar con formato correcto

# ================================================

# --- AGREGAR ESTE CÓDIGO ANTES DE process_folder_files() ---

def load_document_algorithms(db_manager) -> list:
    """
    Carga todos los algoritmos activos de document_algorithms.
    Load all active document algorithms from document_algorithms table.
    """
    try:
        # Crear DatabaseManager para tabla document_algorithms
        algorithms_db = DatabaseManager(
            use_supabase=db_manager.use_supabase,
            table_name="document_algorithms"
        )

        # Obtener todos los algoritmos activos
        all_algorithms = algorithms_db.find_all()

        # Filtrar solo activos
        active_algorithms = [
            {
                "id": algo.get("id"),
                "name": algo.get("name"),
                "classification_criteria": algo.get("classification_criteria"),
                "extraction_prompt": algo.get("extraction_prompt"),
                "output_schema": algo.get("output_schema"),
                "filename_format": algo.get("filename_format")
            }
            for algo in all_algorithms
            if algo.get("is_active", True)
        ]

        logger.info(f"Loaded {len(active_algorithms)} active algorithms")
        for algo in active_algorithms:
            logger.info(f"  - {algo['id']}: {algo['name']}")

        return active_algorithms

    except Exception as e:
        logger.error(f"Error loading document algorithms: {e}")
        return []


def classify_document(
    file_name: str,
    file_content: str,
    algorithms: list
) -> tuple:
    """
    Clasifica el documento y determina qué algoritmo usar.
    Classifies document and determines which algorithm to use.

    Returns:
        (algorithm_id, confidence, classification_details)
    """
    import json

    logger.info(f"🔍 Starting classification for: {file_name}")

    # Crear agente temporal para clasificación
    factory = AgentFactory(database_manager=None, config_manager=config_manager)

    # Prompt de clasificación general
    classification_prompt = f"""Eres un clasificador experto en documentos. Tu tarea es analizar este documento y determinar qué tipo de documento es.

Documentos disponibles para clasificación:
- factura_rg830: Facturas de servicios públicos con resolución 830
- recibo_sueldo: Recibos de sueldo y liquidaciones de haberes
- resumen_bancario: Resúmenes de cuenta y extractos bancarios
- estado_contable: Estados contables, balances, informes financieros
- contrato: Contratos y acuerdos comerciales
- generic: Documentos generales (fallback si no coincide con ninguno específico)

ANALIZA el siguiente documento:
Nombre: {file_name}
Contenido (primeros 2000 caracteres):
{file_content[:2000]}

RESPUESTA REQUERIDA (formato JSON estricto):
{{
  "algorithm_id": "uno_de: factura_rg830, recibo_sueldo, resumen_bancario, estado_contable, contrato, generic",
  "confidence": float (0.0 a 1.0, qué tan seguro estás de la clasificación),
  "reasoning": string (breve explicación de por qué elegiste ese algoritmo)
}}

IMPORTANTE:
- Analiza cuidadosamente el contenido y contexto
- Si NO estás seguro (confidence < 0.7), usa "generic"
- Respuesta SOLO en formato JSON, sin texto adicional
"""

    try:
        # Crear agente temporal para clasificación
        agent = factory.create_agent_with_defaults(
            instructions="Eres un clasificador experto en documentos. Analiza y clasifica.",
            model_id="gemini-2.0-flash-exp"
        )

        # Ejecutar clasificación
        logger.info("🤖 Executing classification with AI...")
        response = agent.run(classification_prompt)

        # Parsear respuesta
        classification = parse_agent_response(response)
        logger.info(f"✅ Classification result: {classification}")

        algorithm_id = classification.get("algorithm_id", "generic")
        confidence = classification.get("confidence", 0.0)
        reasoning = classification.get("reasoning", "")

        logger.info(f"   → Classified as: {algorithm_id} (confidence: {confidence})")
        logger.info(f"   → Reasoning: {reasoning}")

        return algorithm_id, confidence, classification

    except Exception as e:
        logger.error(f"❌ Classification failed: {e}")
        logger.warning("⚠️ Falling back to 'generic' algorithm")
        return "generic", 0.0, {"reasoning": f"Classification error: {str(e)}"}


def process_folder_files_with_auto_classify(
    drive_service,
    folder_id: str,
    agent,
    job_config: Dict[str, Any],
    algorithms: list
) -> Dict[str, int]:
    """
    Process all files in a folder with automatic classification.
    Procesa todos los archivos en una carpeta con clasificación automática.

    NUEVO: Por cada archivo, clasifica y usa el algoritmo correcto.
    """
    stats = {"files_processed": 0, "files_renamed": 0, "errors": 0}

    try:
        # List files in folder
        query = f"'{folder_id}' in parents and trashed=false and mimeType != 'application/vnd.google-apps.folder'"
        response = drive_service.files().list(
            q=query,
            fields="files(id, name, mimeType)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()

        files = response.get("files", [])
        logger.info(f"Found {len(files)} files in folder {folder_id}")

        for file in files:
            stats["files_processed"] += 1

            # Skip already processed files
            if "DOCPROCESADO" in file["name"] or file["name"] == "index.html":
                continue

            try:
                # Download file content
                file_bytes = download_file(drive_service, file["id"])

                # Extract content (with OCR if needed)
                content = content_extractor.get_content(file["name"], file_bytes)
                logger.info(f"Extracted content length: {len(content)} chars for {file['name']}")

                # ============================================
                # PASO 1: CLASIFICACIÓN AUTOMÁTICA
                # ============================================
                algorithm_id, confidence, classification_details = classify_document(
                    file_name=file["name"],
                    file_content=content,
                    algorithms=algorithms
                )

                # ============================================
                # PASO 2: BUSCAR ALGORITMO CORRECTO
                # ============================================
                selected_algorithm = None

                for algo in algorithms:
                    if algo["id"] == algorithm_id:
                        selected_algorithm = algo
                        break

                if not selected_algorithm:
                    logger.warning(f"Algorithm '{algorithm_id}' not found in loaded algorithms, falling back to generic")
                    for algo in algorithms:
                        if algo["id"] == "generic":
                            selected_algorithm = algo
                            break

                if not selected_algorithm:
                    raise ValueError(f"Generic algorithm not found in algorithms list")

                logger.info(f"📋 Selected algorithm: {selected_algorithm['name']}")
                logger.info(f"   Filename format: {selected_algorithm['filename_format']}")

                # ============================================
                # PASO 3: EXTRACCIÓN CON ALGORITMO ESPECÍFICO
                # ============================================

                # Crear prompt específico del algoritmo
                extraction_prompt = selected_algorithm["extraction_prompt"].format(
                    original_filename=file["name"],
                    file_content=content[:8000]  # Limit content
                )

                # Crear agente temporal con instrucciones específicas
                factory = AgentFactory(database_manager=None, config_manager=config_manager)

                # Override output_schema del algoritmo seleccionado
                output_schema = selected_algorithm["output_schema"]

                # Crear agente con configuración específica del algoritmo
                agent_config_specific = {
                    "model": {
                        "name": "gemini-2.0-flash-exp",
                        "temperature": 0.3,
                        "max_tokens": 4096
                    },
                    "instructions": extraction_prompt,
                    "output_schema": output_schema,
                    "filename_format": selected_algorithm["filename_format"]
                }

                agent_specific = factory.create_agent_from_job_config({
                    "name": f"Classifier_{selected_algorithm['id']}",
                    "agent_config": agent_config_specific
                })

                # LOG COMPLETO DEL PROMPT ESPECÍFICO
                print("\n" + "="*80)
                print(f"ALGORITHM-SPECIFIC PROMPT ({selected_algorithm['name']}):")
                print("="*80)
                print(extraction_prompt[:2000])  # Primeros 2000 chars
                print("..." if len(extraction_prompt) > 2000 else "")
                print("="*80 + "\n")

                logger.info(f"Sending algorithm-specific prompt to Gemini for {file['name']} (prompt length: {len(extraction_prompt)} chars)")

                # Ejecutar extracción con algoritmo específico
                response = agent_specific.run(extraction_prompt)

                # LOG COMPLETO DE LA RESPUESTA
                print("\n" + "="*80)
                print("RAW RESPONSE FROM GEMINI:")
                print("="*80)
                print(f"Type: {type(response)}")
                print(f"Has .content: {hasattr(response, 'content')}")
                if hasattr(response, 'content'):
                    print(f"Content type: {type(response.content)}")
                    print(f"Content: {response.content}")
                print(f"Response repr: {repr(response)[:500]}")
                print("="*80 + "\n")

                logger.info(f"Gemini response received for {file['name']}")

                # Parsear respuesta
                analysis = parse_agent_response(response)
                logger.info(f"Parsed analysis for {file['name']}: {analysis}")

                # ============================================
                # PASO 4: RENOMBRAR CON FORMATO CORRECTO
                # ============================================

                # Crear job config temporal con el formato del algoritmo
                temp_job_config = {
                    "agent_config": {
                        "filename_format": selected_algorithm["filename_format"]
                    }
                }

                # Generar nombre con formato correcto
                new_name = build_filename(file["name"], analysis, temp_job_config)
                logger.info(f"Generated filename: {new_name}")

                # Renombrar archivo
                rename_file(drive_service, file["id"], new_name)
                stats["files_renamed"] += 1
                logger.info(f"Renamed: {file['name']} -> {new_name}")

                logger.info(f"✅ File processed successfully: {file['name']} -> {new_name} (algorithm: {algorithm_id}, confidence: {confidence})")

            except Exception as e:
                logger.error(f"❌ Error processing file {file['name']}: {e}")
                stats["errors"] += 1

    except Exception as e:
        logger.error(f"❌ Error listing files in folder {folder_id}: {e}")
        stats["errors"] += 1

    return stats

# ================================================
# INSTRUCCIONES PARA APLICAR ESTE PATCH:
# ================================================
#
# 1. Agregar las funciones arriba al main.py
# 2. Modificar process_job() para cargar algoritmos:
#    algorithms = load_document_algorithms(db_manager)
# 3. Modificar el loop de carpetas para usar process_folder_files_with_auto_classify():
#    folder_stats = process_folder_files_with_auto_classify(
#        drive_service=drive_service,
#        folder_id=folder,
#        agent=agent,
#        job_config=job_config,
#        algorithms=algorithms  # <--- AGREGAR ESTE PARÁMETRO
#    )
# ================================================
