# Story: STORY-104 - Quality System Deployment Guide

## Story Description
As a DevOps engineer, I need a comprehensive deployment guide for the quality tier system so that the three-tier quality system can be deployed consistently across different environments with proper configuration management and monitoring.

## Acceptance Criteria
- [ ] Complete deployment documentation
- [ ] Configuration management for quality tiers
- [ ] Environment-specific quality mappings
- [ ] Deployment validation scripts
- [ ] Health check endpoints for quality system
- [ ] Rollback procedures for quality configurations
- [ ] No dynamic resource-based deployment logic

## Technical Details

### Deployment Configuration Structure
```yaml
# /deployment/quality-config/production.yaml
environment: production
quality_system:
  enabled: true
  tiers:
    - name: low
      description: "Fast generation, basic quality"
      enabled: true
    - name: standard
      description: "Balanced quality and performance"
      enabled: true
    - name: high
      description: "Maximum quality, slower generation"
      enabled: true

workflows:
  root_path: "/opt/comfyui_workflows"
  config_path: "/opt/comfyui_workflows/config/quality_mappings.yaml"
  
  # Production-specific mappings
  mappings:
    character_portrait:
      low:
        workflow_path: "library/image_generation/character_portrait/low_v1"
        parameters:
          steps: 20
          cfg_scale: 7.0
      standard:
        workflow_path: "library/image_generation/character_portrait/standard_v1"
        parameters:
          steps: 35
          cfg_scale: 7.5
      high:
        workflow_path: "library/image_generation/character_portrait/high_v1"
        parameters:
          steps: 60
          cfg_scale: 8.0

monitoring:
  health_check_enabled: true
  metrics_collection: true
  alerting:
    enabled: true
    thresholds:
      workflow_missing: "critical"
      config_invalid: "critical"
```

### Deployment Scripts
```bash
#!/bin/bash
# /deployment/scripts/deploy-quality-system.sh

set -e

ENVIRONMENT=${1:-"development"}
WORKSPACE_ROOT=${2:-"./workspace"}
COMFYUI_WORKFLOWS_ROOT=${3:-"./comfyui_workflows"}

echo "Deploying Quality Tier System to $ENVIRONMENT"

# 1. Validate environment
validate_environment() {
    echo "Validating environment..."
    
    if [[ ! -d "$COMFYUI_WORKFLOWS_ROOT" ]]; then
        echo "Error: ComfyUI workflows directory not found: $COMFYUI_WORKFLOWS_ROOT"
        exit 1
    fi
    
    if [[ ! -f "$COMFYUI_WORKFLOWS_ROOT/config/quality_mappings.yaml" ]]; then
        echo "Error: Quality mappings config not found"
        exit 1
    fi
}

# 2. Backup existing configuration
backup_config() {
    echo "Backing up existing configuration..."
    
    BACKUP_DIR="/tmp/quality_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    if [[ -f "$COMFYUI_WORKFLOWS_ROOT/config/quality_mappings.yaml" ]]; then
        cp "$COMFYUI_WORKFLOWS_ROOT/config/quality_mappings.yaml" "$BACKUP_DIR/"
    fi
    
    echo "Backup created at: $BACKUP_DIR"
}

# 3. Deploy configuration
deploy_config() {
    echo "Deploying quality configuration..."
    
    CONFIG_SOURCE="deployment/quality-config/${ENVIRONMENT}.yaml"
    CONFIG_TARGET="$COMFYUI_WORKFLOWS_ROOT/config/quality_mappings.yaml"
    
    if [[ -f "$CONFIG_SOURCE" ]]; then
        cp "$CONFIG_SOURCE" "$CONFIG_TARGET"
        echo "Deployed $ENVIRONMENT configuration"
    else
        echo "Using default configuration"
    fi
}

# 4. Validate workflows
validate_workflows() {
    echo "Validating workflows..."
    
    python3 -c "
import sys
sys.path.append('backend')
from app.services.workflow_validator import WorkflowValidator
from app.services.quality_config_manager import QualityConfigManager
import yaml

# Validate configuration
config = QualityConfigManager('$COMFYUI_WORKFLOWS_ROOT/config/quality_mappings.yaml')
validator = WorkflowValidator('$COMFYUI_WORKFLOWS_ROOT')

# Check all mappings
errors = validator.validate_all_mappings(config.config)
if errors:
    print('Validation errors:')
    for error in errors:
        print(f'  {error}')
    sys.exit(1)

print('All workflows validated successfully')
"
}

# 5. Set permissions
set_permissions() {
    echo "Setting permissions..."
    chmod 755 "$COMFYUI_WORKFLOWS_ROOT"
    chmod 644 "$COMFYUI_WORKFLOWS_ROOT/config/quality_mappings.yaml"
    find "$COMFYUI_WORKFLOWS_ROOT" -type f -name "*.yaml" -exec chmod 644 {} \;
    find "$COMFYUI_WORKFLOWS_ROOT" -type f -name "*.json" -exec chmod 644 {} \;
}

# 6. Health check
health_check() {
    echo "Running health check..."
    
    python3 -c "
import requests
try:
    response = requests.get('http://localhost:8000/api/v1/quality/health')
    if response.status_code == 200:
        print('Health check passed')
    else:
        print('Health check failed')
        exit(1)
except Exception as e:
    print(f'Health check failed: {e}')
    exit(1)
"
}

# Main deployment flow
main() {
    validate_environment
    backup_config
    deploy_config
    validate_workflows
    set_permissions
    health_check
    
    echo "Quality tier system deployment completed successfully"
}

main "$@"
```

### Docker Configuration
```dockerfile
# /deployment/docker/quality-service.Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/app ./app
COPY backend/scripts ./scripts

# Copy workflow configurations
COPY comfyui_workflows /opt/comfyui_workflows

# Set environment variables
ENV PYTHONPATH=/app
ENV COMFYUI_WORKFLOWS_ROOT=/opt/comfyui_workflows
ENV QUALITY_CONFIG_PATH=/opt/comfyui_workflows/config/quality_mappings.yaml

# Create health check script
RUN cat > /usr/local/bin/health-check.sh << 'EOF'
#!/bin/bash
curl -f http://localhost:8000/api/v1/quality/health || exit 1
EOF
RUN chmod +x /usr/local/bin/health-check.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /usr/local/bin/health-check.sh

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Deployment
```yaml
# /deployment/kubernetes/quality-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quality-service
  namespace: auteur
  labels:
    app: quality-service
    component: quality-tier-system
spec:
  replicas: 2
  selector:
    matchLabels:
      app: quality-service
  template:
    metadata:
      labels:
        app: quality-service
        component: quality-tier-system
    spec:
      containers:
      - name: quality-service
        image: auteur/quality-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: COMFYUI_WORKFLOWS_ROOT
          value: "/opt/comfyui_workflows"
        - name: QUALITY_CONFIG_PATH
          value: "/opt/comfyui_workflows/config/quality_mappings.yaml"
        volumeMounts:
        - name: workflows-config
          mountPath: /opt/comfyui_workflows/config
        - name: workflows-library
          mountPath: /opt/comfyui_workflows/library
        livenessProbe:
          httpGet:
            path: /api/v1/quality/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/quality/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: workflows-config
        configMap:
          name: quality-config
      - name: workflows-library
        persistentVolumeClaim:
          claimName: workflows-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: quality-service
  namespace: auteur
spec:
  selector:
    app: quality-service
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: quality-config
  namespace: auteur
data:
  quality_mappings.yaml: |
    version: "1.0"
    mappings:
      character_portrait:
        low:
          workflow_path: "library/image_generation/character_portrait/low_v1"
          description: "Fast character portrait generation"
          parameters:
            steps: 20
            cfg_scale: 7.0
        standard:
          workflow_path: "library/image_generation/character_portrait/standard_v1"
          description: "Balanced quality character portrait"
          parameters:
            steps: 35
            cfg_scale: 7.5
        high:
          workflow_path: "library/image_generation/character_portrait/high_v1"
          description: "High quality character portrait"
          parameters:
            steps: 60
            cfg_scale: 8.0
```

### Health Check Service
```python
# backend/app/services/quality_health_check.py
from typing import Dict, Any, List
import os
from pathlib import Path

class QualityHealthCheckService:
    def __init__(self, workflows_root: str, config_path: str):
        self.workflows_root = Path(workflows_root)
        self.config_path = Path(config_path)
    
    def check_system_health(self) -> Dict[str, Any]:
        """Check overall quality system health"""
        
        checks = {
            "status": "healthy",
            "timestamp": None,
            "checks": {}
        }
        
        # Check configuration file
        config_check = self._check_configuration()
        checks["checks"]["configuration"] = config_check
        
        # Check workflow availability
        workflow_check = self._check_workflows()
        checks["checks"]["workflows"] = workflow_check
        
        # Check file permissions
        permission_check = self._check_permissions()
        checks["checks"]["permissions"] = permission_check
        
        # Determine overall status
        failed_checks = [
            check for check in checks["checks"].values()
            if check["status"] != "healthy"
        ]
        
        checks["status"] = "unhealthy" if failed_checks else "healthy"
        checks["timestamp"] = None  # Would use actual timestamp
        checks["failed_checks"] = len(failed_checks)
        
        return checks
    
    def _check_configuration(self) -> Dict[str, Any]:
        """Check configuration file health"""
        
        check = {
            "status": "healthy",
            "details": {}
        }
        
        if not self.config_path.exists():
            check["status"] = "unhealthy"
            check["details"]["error"] = "Configuration file not found"
            return check
        
        try:
            import yaml
            with open(self.config_path) as f:
                config = yaml.safe_load(f)
            
            # Validate basic structure
            if "mappings" not in config:
                check["status"] = "unhealthy"
                check["details"]["error"] = "Invalid configuration structure"
                return check
            
            # Count mappings
            total_mappings = 0
            for task_type, tiers in config.get("mappings", {}).items():
                for tier, mapping in tiers.items():
                    total_mappings += 1
                    
                    # Validate mapping structure
                    if "workflow_path" not in mapping:
                        check["status"] = "unhealthy"
                        check["details"][f"{task_type}_{tier}"] = "Missing workflow_path"
            
            check["details"]["total_mappings"] = total_mappings
            
        except Exception as e:
            check["status"] = "unhealthy"
            check["details"]["error"] = str(e)
        
        return check
    
    def _check_workflows(self) -> Dict[str, Any]:
        """Check workflow availability"""
        
        check = {
            "status": "healthy",
            "details": {
                "total_workflows": 0,
                "missing_workflows": [],
                "invalid_workflows": []
            }
        }
        
        try:
            import yaml
            with open(self.config_path) as f:
                config = yaml.safe_load(f)
            
            missing_workflows = []
            invalid_workflows = []
            total_workflows = 0
            
            for task_type, tiers in config.get("mappings", {}).items():
                for tier, mapping in tiers.items():
                    total_workflows += 1
                    
                    workflow_path = mapping.get("workflow_path")
                    if not workflow_path:
                        invalid_workflows.append(f"{task_type}_{tier}: missing path")
                        continue
                    
                    full_path = self.workflows_root / workflow_path
                    workflow_file = full_path / "workflow_api.json"
                    
                    if not workflow_file.exists():
                        missing_workflows.append(str(workflow_file))
            
            check["details"]["total_workflows"] = total_workflows
            check["details"]["missing_workflows"] = missing_workflows
            check["details"]["invalid_workflows"] = invalid_workflows
            
            if missing_workflows or invalid_workflows:
                check["status"] = "unhealthy"
        
        except Exception as e:
            check["status"] = "unhealthy"
            check["details"]["error"] = str(e)
        
        return check
    
    def _check_permissions(self) -> Dict[str, Any]:
        """Check file and directory permissions"""
        
        check = {
            "status": "healthy",
            "details": {}
        }
        
        # Check config file permissions
        if self.config_path.exists():
            stat = self.config_path.stat()
            if not bool(stat.st_mode & 0o444):  # Read permission
                check["status"] = "unhealthy"
                check["details"]["config_readable"] = False
        
        # Check workflows directory permissions
        if self.workflows_root.exists():
            stat = self.workflows_root.stat()
            if not bool(stat.st_mode & 0o555):  # Read and execute permissions
                check["status"] = "unhealthy"
                check["details"]["workflows_accessible"] = False
        
        return check
```

### API Health Check Endpoints
```python
# backend/app/api/v1/quality_health.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/quality", tags=["quality-health"])

@router.get("/health")
async def get_quality_health() -> Dict[str, Any]:
    """Get quality system health status"""
    
    from app.services.quality_health_check import QualityHealthCheckService
    
    service = QualityHealthCheckService(
        workflows_root="/opt/comfyui_workflows",
        config_path="/opt/comfyui_workflows/config/quality_mappings.yaml"
    )
    
    return service.check_system_health()

@router.get("/ready")
async def get_quality_ready() -> Dict[str, Any]:
    """Readiness check for quality system"""
    
    try:
        service = QualityHealthCheckService(
            workflows_root="/opt/comfyui_workflows",
            config_path="/opt/comfyui_workflows/config/quality_mappings.yaml"
        )
        
        health = service.check_system_health()
        
        if health["status"] == "healthy":
            return {"status": "ready", "timestamp": None}
        else:
            raise HTTPException(status_code=503, detail="Quality system not ready")
            
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/version")
async def get_quality_version() -> Dict[str, Any]:
    """Get quality system version information"""
    
    return {
        "system": "quality-tier-system",
        "version": "1.0.0",
        "supported_tiers": ["low", "standard", "high"],
        "config_version": "1.0"
    }
```

### Monitoring and Alerting
```yaml
# /deployment/monitoring/quality-alerts.yaml
groups:
- name: quality_tier_system
  rules:
  - alert: QualityConfigMissing
    expr: absent(quality_config_last_modified)
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Quality configuration file is missing"
      description: "The quality mappings configuration file is not accessible"

  - alert: WorkflowMissing
    expr: increase(quality_workflow_missing_total[5m]) > 0
    for: 0m
    labels:
      severity: critical
    annotations:
      summary: "Required workflow is missing"
      description: "A workflow referenced in quality mappings is not found"

  - alert: QualitySystemDown
    expr: up{job="quality-service"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Quality system is down"
      description: "The quality tier service is not responding"

  - alert: HighQualityRequestRate
    expr: rate(quality_tier_selection_total{tier="high"}[5m]) > 10
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High rate of high-quality requests"
      description: "Unusually high rate of high-quality tier selections"
```

### Rollback Procedures
```bash
#!/bin/bash
# /deployment/scripts/rollback-quality-system.sh

set -e

ENVIRONMENT=${1:-"development"}
BACKUP_DIR=${2:-"/tmp/quality_backup"}

echo "Rolling back Quality Tier System in $ENVIRONMENT"

# 1. Stop quality service
echo "Stopping quality service..."
systemctl stop auteur-quality || docker stop auteur-quality || kubectl delete deployment quality-service -n auteur

# 2. Restore configuration
if [[ -d "$BACKUP_DIR" ]]; then
    echo "Restoring configuration from backup..."
    
    if [[ -f "$BACKUP_DIR/quality_mappings.yaml" ]]; then
        cp "$BACKUP_DIR/quality_mappings.yaml" "/opt/comfyui_workflows/config/quality_mappings.yaml"
        echo "Configuration restored from backup"
    else
        echo "Warning: No backup configuration found"
    fi
else
    echo "Warning: No backup directory found"
fi

# 3. Validate restored configuration
echo "Validating restored configuration..."
python3 -c "
import sys
sys.path.append('backend')
from app.services.quality_health_check import QualityHealthCheckService

service = QualityHealthCheckService(
    workflows_root='/opt/comfyui_workflows',
    config_path='/opt/comfyui_workflows/config/quality_mappings.yaml'
)

health = service.check_system_health()
if health['status'] != 'healthy':
    print('Rollback validation failed')
    print(health)
    sys.exit(1)

print('Rollback validation successful')
"

# 4. Restart service
echo "Restarting quality service..."
systemctl start auteur-quality || docker start auteur-quality || kubectl apply -f kubernetes/quality-deployment.yaml

echo "Quality system rollback completed"
```

### Environment-Specific Configurations
```yaml
# /deployment/quality-config/development.yaml
environment: development
quality_system:
  enabled: true
  tiers:
    - name: low
      description: "Fast development testing"
      enabled: true
    - name: standard
      description: "Standard development quality"
      enabled: true
    - name: high
      description: "Full quality for final testing"
      enabled: true

workflows:
  root_path: "./test_workflows"
  config_path: "./test_workflows/config/quality_mappings.yaml"
  
  # Development-specific mappings with smaller parameters
  mappings:
    character_portrait:
      low:
        workflow_path: "library/image_generation/character_portrait/low_v1"
        parameters:
          steps: 10  # Faster for development
          cfg_scale: 7.0
      standard:
        workflow_path: "library/image_generation/character_portrait/standard_v1"
        parameters:
          steps: 15  # Faster for development
          cfg_scale: 7.0
      high:
        workflow_path: "library/image_generation/character_portrait/high_v1"
        parameters:
          steps: 25  # Faster for development
          cfg_scale: 7.5

monitoring:
  health_check_enabled: true
  metrics_collection: false
  alerting:
    enabled: false

# /deployment/quality-config/staging.yaml
environment: staging
quality_system:
  enabled: true
  tiers:
    - name: low
      description: "Staging testing quality"
      enabled: true
    - name: standard
      description: "Staging standard quality"
      enabled: true
    - name: high
      description: "Production-like staging quality"
      enabled: true

workflows:
  root_path: "/opt/comfyui_workflows"
  config_path: "/opt/comfyui_workflows/config/quality_mappings.yaml"
  
  # Staging mappings (same as production)
  mappings:
    character_portrait:
      low:
        workflow_path: "library/image_generation/character_portrait/low_v1"
        parameters:
          steps: 20
          cfg_scale: 7.0
      standard:
        workflow_path: "library/image_generation/character_portrait/standard_v1"
        parameters:
          steps: 35
          cfg_scale: 7.5
      high:
        workflow_path: "library/image_generation/character_portrait/high_v1"
        parameters:
          steps: 60
          cfg_scale: 8.0

monitoring:
  health_check_enabled: true
  metrics_collection: true
  alerting:
    enabled: true
    thresholds:
      workflow_missing: "warning"
      config_invalid: "warning"
```

### Deployment Validation
```python
# /deployment/scripts/validate-deployment.py
import sys
import yaml
import requests
from pathlib import Path

def validate_deployment(environment: str, base_url: str = "http://localhost:8000"):
    """Validate quality system deployment"""
    
    print(f"Validating quality system deployment for {environment}")
    
    # 1. Check health endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/quality/health")
        if response.status_code != 200:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        health = response.json()
        if health["status"] != "healthy":
            print(f"❌ System unhealthy: {health}")
            return False
        
        print("✅ Health check passed")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # 2. Check version endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/quality/version")
        if response.status_code != 200:
            print(f"❌ Version check failed: {response.status_code}")
            return False
        
        version = response.json()
        print(f"✅ Version check passed: {version['version']}")
    except Exception as e:
        print(f"❌ Version check failed: {e}")
        return False
    
    # 3. Check quality tier availability
    test_task_types = ["character_portrait", "scene_generation"]
    
    for task_type in test_task_types:
        try:
            response = requests.get(f"{base_url}/api/v1/quality/tiers/{task_type}")
            if response.status_code != 200:
                print(f"❌ Tier check failed for {task_type}: {response.status_code}")
                return False
            
            tiers = response.json()
            expected_tiers = ["low", "standard", "high"]
            available_tiers = list(tiers["available_tiers"].keys())
            
            if not all(tier in available_tiers for tier in expected_tiers):
                print(f"❌ Missing tiers for {task_type}: {available_tiers}")
                return False
            
            print(f"✅ Tier check passed for {task_type}")
        except Exception as e:
            print(f"❌ Tier check failed for {task_type}: {e}")
            return False
    
    print("🎉 All deployment validations passed!")
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate quality system deployment")
    parser.add_argument("--environment", required=True, choices=["development", "staging", "production"])
    parser.add_argument("--base-url", default="http://localhost:8000")
    
    args = parser.parse_args()
    
    success = validate_deployment(args.environment, args.base_url)
    sys.exit(0 if success else 1)
```

## Test Requirements
- Deployment script functionality
- Configuration validation
- Health check endpoints
- Environment-specific configurations
- Rollback procedure testing
- Monitoring integration

## Definition of Done
- Deployment scripts are executable and tested
- Health checks validate system readiness
- Configuration management works across environments
- Rollback procedures are tested and documented
- Monitoring alerts are configured
- Deployment validation scripts pass for all environments