"""
Ejemplo de uso del OAuth Security Manager
=========================================

Este archivo muestra cómo implementar seguridad OAuth en los endpoints
del API server con whitelist de dominios.

:created:   2025-12-05
:filename:  example_oauth_usage.py
:author:    amBotHs + CENF
"""

from flask import Flask, g, jsonify, request
from core_renombrador.oauth_security import (
    OAuthSecurityManager,
    require_auth,
    create_oauth_manager_from_config
)
from core_renombrador.config_manager import ConfigManager
from core_renombrador.database_manager import DatabaseManager

app = Flask(__name__)

# Initialize managers
config = ConfigManager()
db = DatabaseManager(use_supabase=True)  # or JSON mode

# Initialize OAuth Security
oauth_manager = OAuthSecurityManager(
    client_id=config.get_setting("oauth.client_id"),
    allowed_domains=[
        "miempresa.com",
        "cenf.com.ar", 
        "coutinholla.com"
    ],
    allowed_emails=[
        "admin@miempresa.com",
        "gonzalo@cenf.com.ar"
    ]
)

# Alternative: Load from config
# oauth_manager = create_oauth_manager_from_config(config)


# ==============================================================================
# ENDPOINT PÚBLICO (Sin autenticación)
# ==============================================================================

@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint - público, sin autenticación.
    """
    return jsonify({"status": "healthy"}), 200


# ==============================================================================
# ENDPOINT PROTEGIDO - Manual Job Submission
# ==============================================================================

@app.route("/jobs/manual", methods=["POST"])
@require_auth(oauth_manager, rate_limit_requests=5, rate_limit_minutes=1)
def submit_manual_job():
    """
    Submit a manual job for processing.
    Enviar un trabajo manual para procesamiento.
    
    Headers:
        Authorization: Bearer <google_oauth_token>
    
    Body:
        {
            "folder_id": "1AbCdEf...",
            "job_type": "invoice" | "report" | "generic"
        }
    
    Security:
        - Requires valid Google OAuth token
        - User domain must be in whitelist
        - Rate limited to 5 requests/minute
    """
    # User info is available in g.current_user (set by decorator)
    user = g.current_user
    
    # Parse request
    data = request.json
    folder_id = data.get("folder_id")
    job_type = data.get("job_type", "generic")
    
    # Validate input
    if not folder_id:
        return jsonify({"error": "folder_id is required"}), 400
    
    # TODO: Verify user has permission to access this folder in Drive
    # has_permission = check_drive_permission(user["email"], folder_id)
    # if not has_permission:
    #     return jsonify({"error": "No access to this folder"}), 403
    
    # Create job entry
    job_data = {
        "folder_id": folder_id,
        "job_type": job_type,
        "status": "pending",
        "submitted_by": user["email"],
        "submitted_at": datetime.now().isoformat()
    }
    
    # Store in database or send to Cloud Tasks
    # db.insert(job_data)
    
    return jsonify({
        "message": "Job submitted successfully",
        "job_id": "job-123",
        "submitted_by": user["email"]
    }), 202


# ==============================================================================
# ENDPOINT PROTEGIDO - Listar Jobs del Usuario
# ==============================================================================

@app.route("/jobs/my-jobs", methods=["GET"])
@require_auth(oauth_manager, rate_limit_requests=20, rate_limit_minutes=1)
def list_my_jobs():
    """
    List all jobs submitted by the current user.
    Listar todos los trabajos enviados por el usuario actual.
    """
    user = g.current_user
    
    # Query jobs from database
    # jobs = db.find("submitted_by", user["email"])
    
    return jsonify({
        "user": user["email"],
        "jobs": [
            {"id": "job-1", "status": "completed"},
            {"id": "job-2", "status": "pending"}
        ]
    }), 200


# ==============================================================================
# ENDPOINT PARA CLOUD SCHEDULER (Sin OAuth, usa OIDC de Google)
# ==============================================================================

@app.route("/jobs/scheduled", methods=["POST"])
def scheduled_jobs():
    """
    Triggered by Cloud Scheduler with OIDC authentication.
    Disparado por Cloud Scheduler con autenticación OIDC.
    
    Security:
        - Verifies OIDC token from Google Cloud
        - No OAuth needed (service-to-service)
    """
    # Verify OIDC token from Cloud Scheduler
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # Extract token
        token = auth_header.split("Bearer ")[1]
        
        # Verify it's from Google Cloud
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        
        # Expected audience is the Cloud Run service URL
        audience = request.url_root.rstrip("/")
        
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            audience
        )
        
        # Verify it's from Cloud Scheduler
        email = idinfo.get("email")
        if not email or not email.endswith("gserviceaccount.com"):
            return jsonify({"error": "Invalid service account"}), 403
        
        # Process scheduled jobs
        # ...
        
        return jsonify({
            "message": "Scheduled jobs processed",
            "triggered_by": email
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"OIDC verification failed: {str(e)}"}), 403


# ==============================================================================
# ENDPOINT ADMIN (Solo para dominios específicos)
# ==============================================================================

@app.route("/admin/config", methods=["GET", "POST"])
@require_auth(oauth_manager, rate_limit_requests=10, rate_limit_minutes=5)
def admin_config():
    """
    Admin endpoint to view/update configuration.
    Solo accesible por dominios admin.
    """
    user = g.current_user
    
    # Additional admin check
    admin_domains = ["miempresa.com", "cenf.com.ar"]
    if user["domain"] not in admin_domains:
        return jsonify({"error": "Admin access required"}), 403
    
    if request.method == "GET":
        # Return current config
        return jsonify(config.get_all_config()), 200
    
    elif request.method == "POST":
        # Update config
        # ...
        return jsonify({"message": "Config updated"}), 200


# ==============================================================================
# ERROR HANDLERS
# ==============================================================================

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "error": "Unauthorized",
        "message": "Valid authentication token required"
    }), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({
        "error": "Forbidden",
        "message": "Your domain is not authorized to access this resource"
    }), 403

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({
        "error": "Too Many Requests",
        "message": "Rate limit exceeded. Please wait before making more requests."
    }), 429


if __name__ == "__main__":
    # For local development only
    app.run(debug=True, host="0.0.0.0", port=8080)
