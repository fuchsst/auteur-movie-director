# Technical Dependencies and Cross-Story Relationships

## Overview
This document provides a comprehensive analysis of technical dependencies and cross-story relationships for EPIC-005 Video Assembly Pipeline.

## Story Dependency Graph

### Phase 1: Core Assembly (Weeks 1-2)
```
STORY-067 (VSEAssemblerNode) ←→ STORY-068 (MoviePy Pipeline)
           ↓
STORY-069 (Simple Concatenation)
```

**Critical Dependencies:**
- **STORY-067 ← EPIC-004**: Production Canvas infrastructure
- **STORY-068 ← STORY-067**: Node configuration and validation
- **STORY-069 ← STORY-068**: Basic pipeline for concatenation

### Phase 2: EDL System (Weeks 3-4)
```
STORY-071 (EDL Generator) ← STORY-072 (Story Metadata)
           ↓
STORY-073 (Take Preservation) ← STORY-074 (Professional Standards)
```

**Critical Dependencies:**
- **STORY-071 ← STORY-069**: Basic assembly for EDL creation
- **STORY-072 ← Story System**: Narrative structure access
- **STORY-073 ← Take System**: Take metadata extraction

### Phase 3: Advanced Features (Weeks 5-6)
```
STORY-075 (Multi-format) ← STORY-076 (Progress Tracking)
           ↓
STORY-077 (Error Handling) ← STORY-078 (Batch Operations)
```

**Critical Dependencies:**
- **STORY-075 ← STORY-068**: MoviePy pipeline enhancement
- **STORY-076 ← WebSocket Service**: Real-time communication
- **STORY-077 ← All stories**: Error recovery across system

### Phase 4: Optimization (Weeks 7-8)
```
STORY-079 (Performance) ← STORY-080 (Testing Suite)
           ↓
STORY-081 (Memory Management) ← STORY-082 (Documentation)
```

## Technical Dependencies by Component

### Backend Dependencies

#### MoviePy Integration
```
MoviePy Pipeline
├── FFmpeg (System dependency)
├── Redis (Background tasks)
├── FastAPI (API endpoints)
├── SQLAlchemy (Database)
└── WebSocket (Real-time updates)
```

#### EDL Generation
```
EDL System
├── Story Structure Parser
├── Take Metadata Extractor
├── Timecode Calculator
├── CMX3600 Formatter
└── NLE Compatibility Layer
```

#### Multi-format Export
```
Export System
├── FFmpeg (Multiple codecs)
├── Hardware Acceleration (NVENC/QSV)
├── Quality Presets
├── Format Validation
└── Performance Optimization
```

### Frontend Dependencies

#### Svelte Flow Integration
```
VSEAssemblerNode
├── Svelte Flow Core
├── Node Registry System
├── WebSocket Client
├── Progress Visualization
└── Error Handling
```

#### Real-time Updates
```
Progress System
├── WebSocket Connection
├── Progress Store (Svelte)
├── Notification Service
├── UI Components
└── State Management
```

## Cross-System Dependencies

### Project Structure Integration
```
Assembly System Dependencies
├── Project Management (EPIC-001)
├── Story Structure (EPIC-002)
├── Function Runner (EPIC-003)
├── Production Canvas (EPIC-004)
└── Take System (EPIC-002)
```

### Database Dependencies
```
Data Dependencies
├── Project Configuration (project.json)
├── Shot Metadata (shots table)
├── Take Information (takes table)
├── Story Structure (story metadata)
└── Export History (exports table)
```

### File System Dependencies
```
Directory Structure Dependencies
├── 03_Renders/ (Source shots)
├── 04_Project_Files/assemblies/ (EDL files)
├── 06_Exports/ (Final videos)
├── 05_Cache/ (Temporary files)
└── .git/ (Version control with LFS)
```

## External Service Dependencies

### Required Services
```
External Dependencies
├── FFmpeg (Video processing)
├── Redis (Background tasks)
├── PostgreSQL (Database)
├── Redis (Caching)
└── WebSocket (Real-time communication)
```

### Optional Services
```
Enhanced Services
├── AWS S3 (Cloud storage)
├── CloudFront (CDN)
├── Lambda (Serverless processing)
├── CloudWatch (Monitoring)
└── Sentry (Error tracking)
```

## Version Compatibility Matrix

### Software Versions
| Component | Minimum | Recommended | Latest Tested |
|-----------|---------|-------------|---------------|
| Python | 3.9 | 3.11 | 3.12 |
| MoviePy | 1.0.3 | 2.0.0 | 2.1.0 |
| FFmpeg | 4.4 | 5.1 | 6.0 |
| Redis | 6.2 | 7.0 | 7.2 |
| PostgreSQL | 13 | 15 | 16 |
| Node.js | 16 | 18 | 20 |
| Svelte | 3.0 | 4.0 | 4.2 |

### Platform Support
| Platform | Status | Notes |
|----------|--------|--------|
| Ubuntu 20.04+ | ✅ Full Support | Primary development |
| macOS 12+ | ✅ Full Support | Apple Silicon compatible |
| Windows 10+ | ✅ Full Support | WSL2 recommended |
| Docker | ✅ Full Support | Containerized deployment |

## Build and Deployment Dependencies

### Build Requirements
```
Build Dependencies
├── Python build tools (pip, setuptools)
├── Node.js build tools (npm, vite)
├── Docker (containerization)
├── Git (version control)
└── Make (build automation)
```

### Runtime Requirements
```
Runtime Dependencies
├── System libraries (libavcodec, libavformat)
├── Graphics drivers (GPU acceleration)
├── Network connectivity (real-time updates)
├── Storage space (video processing)
└── Memory (minimum 4GB, recommended 8GB+)
```

## Security Dependencies

### Input Validation
```
Security Validation Chain
├── File path sanitization
├── User input validation
├── SQL injection prevention
├── XSS protection
└── CSRF protection
```

### Access Control
```
Permission Dependencies
├── User authentication
├── Project authorization
├── File access control
├── API rate limiting
└── Audit logging
```

## Testing Dependencies

### Test Infrastructure
```
Testing Dependencies
├── pytest (unit testing)
├── pytest-cov (coverage)
├── pytest-asyncio (async testing)
├── pytest-benchmark (performance)
├── Docker (integration testing)
└── Locust (load testing)
```

### Mock Dependencies
```
Mock Services
├── Mock NLE integration
├── Mock video files
├── Mock project data
├── Mock hardware acceleration
└── Mock network conditions
```

## Environment Variables

### Required Environment Variables
```bash
# Core configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost/db

# Video processing
FFMPEG_PATH=/usr/bin/ffmpeg
MAX_MEMORY_MB=2048
PROCESSING_THREADS=4

# Security
SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret
```

### Optional Environment Variables
```bash
# Enhanced configuration
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
S3_BUCKET=your-bucket-name
CDN_URL=https://your-cdn.com

# Monitoring
SENTRY_DSN=your-sentry-dsn
PROMETHEUS_URL=http://localhost:9090
```

## Deployment Dependencies

### Development Environment
```yaml
# docker-compose.dev.yml
services:
  backend:
    build: .
    depends_on:
      - redis
      - postgres
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres/db
      - REDIS_URL=redis://redis:6379

  frontend:
    build: ./frontend
    depends_on:
      - backend

  redis:
    image: redis:7-alpine

  postgres:
    image: postgres:15-alpine
```

### Production Environment
```yaml
# docker-compose.prod.yml
services:
  backend:
    image: auteur/backend:latest
    depends_on:
      - redis
      - postgres
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
```

## Migration Dependencies

### Database Migrations
```sql
-- Required database extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Required tables
CREATE TABLE IF NOT EXISTS assembly_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id),
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### File System Migrations
```bash
# Directory structure creation
mkdir -p workspace/{project_name}/06_Exports/
mkdir -p workspace/{project_name}/04_Project_Files/assemblies/
mkdir -p workspace/{project_name}/05_Cache/
```

## Risk Mitigation Strategies

### Dependency Risks
1. **FFmpeg Compatibility**: Use official Docker images
2. **Memory Limits**: Implement streaming processing
3. **Network Dependencies**: Add offline fallback modes
4. **Platform Differences**: Use containerized deployment
5. **Version Conflicts**: Pin specific versions in requirements

### Fallback Strategies
1. **Format Fallback**: Multiple codec options
2. **Quality Fallback**: Progressive quality reduction
3. **Performance Fallback**: Graceful degradation
4. **Error Recovery**: Checkpoint-based restart
5. **Network Fallback**: Offline processing mode

## Success Criteria

### Dependency Validation Checklist
- [ ] All system dependencies installed and configured
- [ ] Database migrations applied successfully
- [ ] File system permissions configured correctly
- [ ] Network connectivity verified
- [ ] Security configurations validated
- [ ] Performance benchmarks achieved
- [ ] Cross-platform compatibility verified
- [ ] CI/CD pipeline passes all tests

This comprehensive dependency analysis ensures successful implementation of EPIC-005 Video Assembly Pipeline with all technical requirements met.