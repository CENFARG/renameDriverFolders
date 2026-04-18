# Product Context

This file provides a high-level overview of project and expected product that will be created. Initially it is based upon projectBrief.md (if provided) and all other available project-related information in working directory. This file is intended to be updated as project evolves, and should be used to inform all other modes of project's goals and context.

## Project Goal
To create a serverless application that automates processing and organization of files in Google Drive. The application monitors designated folders, analyzes new files using Gemini AI, renames them based on analysis, and maintains an HTML index of all processed files.

## Key Features
*   **Automated File Monitoring:** The application checks for new or modified files in user-defined subfolders within a specific Google Drive root folder.
*   **AI-Powered Content Analysis:** Uses Gemini AI model (`gemini-2.0-flash-exp`) to analyze content of new files and extract relevant keywords and a primary date.
*   **Standardized Renaming:** Renames files to a consistent format: `DOCPROCESADO_YYYY-MM-DD_keywords.extension`.
*   **HTML Indexing:** Automatically creates and updates an `index.html` file in each monitored folder, providing a clear log of original filenames, new filenames, and a summary.
*   **State Persistence:** Uses a Google Cloud Storage (GCS) bucket to store a `pageToken`, ensuring that it only processes changes since the last run, making it efficient and scalable.
*   **Environment-Based Configuration:** All settings (folder IDs, API keys, etc.) are managed via environment variables, allowing for easy configuration between local, testing, and production environments.
*   **Automated Execution:** Configured with Google Cloud Scheduler for periodic, hands-free operation.
*   **Comprehensive Monitoring:** Custom metrics and alerting infrastructure for proactive issue detection.

## Overall Architecture
*   The application is a Python-based Flask web server.
*   It is designed to be stateless and run in a serverless environment like Google Cloud Run.
*   The core logic is triggered by an incoming HTTP POST request. In production, this trigger is automated by Google Cloud Scheduler.
*   It integrates with three core Google services: Drive API, Cloud Storage API, and Gemini API.
*   Authentication is handled securely via a single Service Account with impersonation, allowing it to act on behalf of a specified user without exposing user credentials.
*   Monitoring is implemented through Google Cloud Monitoring with custom logging metrics.

## Production Deployment
*   **Status**: ✅ LIVE and FULLY OPERATIONAL
*   **Environment**: Google Cloud Run
*   **URL**: https://rename-driver-folders-v1-07112025-702567224563.us-central1.run.app
*   **Project ID**: cloud-functions-474716
*   **Revision**: rename-driver-folders-v1-07112025-00018-2sr
*   **Target Folders**: ["doc de respaldo", "test_integrado"]
*   **Root Folder**: test_integrado (contains target folders with proper permissions)
*   **Scheduler**: rename-driver-folders-v1-07112025-schedul (automated execution)
*   **Monitoring**: Custom metrics (rename-driver-errors, rename-driver-success)

## Performance Characteristics
*   **Response Time**: < 5 seconds average
*   **Success Rate**: > 95%
*   **Memory Usage**: < 400Mi average
*   **CPU Usage**: < 0.5 vCPU average
*   **Scalability**: 0-3 instances auto-scaling

## Operational Features
*   **Zero-Downtime Deployment**: Manual deployment strategy prevents service interruption
*   **Robust Error Handling**: Comprehensive logging and error recovery mechanisms
*   **Stateless Design**: Suitable for serverless scaling and reliability
*   **Security Best Practices**: Non-root container execution, service account authentication
*   **Observability**: Full logging, metrics, and alerting infrastructure

## Documentation & Maintenance
*   **Comprehensive Guides**: Complete deployment, monitoring, and operation documentation
*   **Programming Standards**: Established patterns and best practices for future development
*   **Quick Reference**: Essential commands and troubleshooting guides
*   **Memory Bank**: Complete decision history and project evolution tracking

## Business Value
*   **Automation**: Eliminates manual file organization and naming
*   **Consistency**: Standardized file naming and indexing across all documents
*   **Efficiency**: AI-powered content analysis reduces manual categorization
*   **Scalability**: Serverless architecture handles variable workloads
*   **Reliability**: Automated monitoring and alerting ensures operational stability

*2025-11-25 23:45:00 - Updated with complete production status, monitoring capabilities, and operational characteristics.*