    # ============================================================
    # NUEVO DISEÑO: Auto-Clasificación con TODOS los algoritmos
    # ============================================================

    # Find appropriate job config
    # For manual jobs, we use AUTO-CLASSIFICATION with ALL active algorithms
    job_id = f"job-manual-auto-classify"

    logger.info(f"="*80)
    logger.info(f"MANUAL JOB REQUEST - User: {user['email']}")
    logger.info(f"  job_type: {job_request.job_type}")
    logger.info(f"  folder_id: {job_request.folder_id}")
    logger.info(f"  job_id: {job_id}")
    logger.info(f"="*80)

    # Check if job config exists in DB, if not create it (Auto-seeding)
    existing_jobs = db_manager.find("id", job_id)

    logger.info(f"STEP 1: Checking if job config '{job_id}' exists...")
    logger.info(f"  Found: {len(existing_jobs) > 0}")

    if not existing_jobs:
        logger.info(f"STEP 2: Job config not found. Creating AUTO-CLASSIFY job with ALL algorithms.")

        # ============================================================
        # NUEVO DISEÑO: Cargar TODOS los algoritmos activos
        # ============================================================
        logger.info(f"STEP 3: Loading ALL active algorithms from document_algorithms...")

        all_algorithms = algorithms_manager.find("is_active", True)
        logger.info(f"  Found {len(all_algorithms)} active algorithms")

        # Build a comprehensive prompt that includes ALL algorithms
        algorithm_blocks = []
        for algo in all_algorithms:
            logger.info(f"  - Algorithm: {algo['id']} - {algo['name']}")
            algorithm_blocks.append(f"""
<ALGORITHM id="{algo['id']}" name="{algo['name']}">
{algo['classification_criteria']}

EXTRACTION_SCHEMA:
{algo['output_schema']}

FILENAME_FORMAT:
{algo['filename_format']}
</ALGORITHM>
""")

        algorithms_prompt = "\n".join(algorithm_blocks)

        logger.info(f"STEP 4: Building AUTO-CLASSIFY job config...")
        logger.info(f"  Total algorithms included: {len(all_algorithms)}")

        # Create AUTO-CLASSIFY job config
        auto_classify_config = {
            "id": job_id,
            "name": "Auto-Classification with AI",
            "description": "AI-powered document classifier that automatically selects the appropriate algorithm",
            "active": True,
            "trigger_type": "manual",
            "schedule": None,
            "source_folder_id": "DYNAMIC",
            "target_folder_names": ["*"],
            "agent_config": {
                "model": {
                    "name": "gemini-2.0-flash-exp",
                    "temperature": 0.3,
                    "max_tokens": 4096
                },
                "instructions": f"""You are an intelligent document classifier. Your task is to analyze documents and determine which algorithm should be used for renaming.

AVAILABLE ALGORITHMS:
{algorithms_prompt}

PROCESS:
1. Analyze the document content
2. Determine which algorithm best matches the document type
3. Use that algorithm's extraction_schema to extract the information
4. Return the data in the format specified by the chosen algorithm

IMPORTANT: You must identify the correct algorithm and use its specific output schema, not a generic one.
""",
                "prompt_template": """Analyze the following document and determine which algorithm applies:

ORIGINAL FILE: {original_filename}

DOCUMENT CONTENT:
{file_content}

AVAILABLE ALGORITHMS:
{algorithms_prompt}

TASK:
1. Identify which algorithm best matches this document
2. Extract information according to that algorithm's schema
3. Return the data in the exact format specified by the chosen algorithm

Output the result as JSON following the chosen algorithm's output_schema.
""",
                "output_schema": {
                    "detected_algorithm": "string - the ID of the algorithm that best matches",
                    "confidence": "number - confidence score 0-1",
                    "extracted_data": "object - the data extracted according to the chosen algorithm's schema"
                },
                "filename_format": "{detected_algorithm}_{date}.{ext}"
            }
        }

        logger.info(f"STEP 5: Inserting AUTO-CLASSIFY job config into database...")
        logger.info(f"  Config name: {auto_classify_config['name']}")
        logger.info(f"  target_folder_names: {auto_classify_config['target_folder_names']}")

        try:
            db_manager.insert(auto_classify_config)
            logger.info(f"✅ SUCCESS: AUTO-CLASSIFY job config created successfully!")
        except Exception as e:
            logger.error(f"❌ ERROR: Failed to insert AUTO-CLASSIFY job config: {e}")
            # Continue anyway, might exist but find failed
    else:
        logger.info(f"STEP 2 (ALTERNATE): Job config '{job_id}' ALREADY EXISTS")
        logger.info(f"  Reusing existing config")
        logger.info(f"  Config name: {existing_jobs[0]['name']}")
        logger.info(f"  target_folder_names: {existing_jobs[0].get('target_folder_names', 'NOT SET')}")
        logger.warning(f"⚠️  WARNING: If target_folder_names is NOT ['*'], this will cause issues!")

    logger.info(f"="*80)
    logger.info(f"ACTION: Creating Cloud Tasks task for Worker...")
    logger.info(f"  job_id: {job_id}")
    logger.info(f"  folder_id: {job_request.folder_id}")
    logger.info(f"="*80)
