# EPIC-002 Story Dependency Graph

## Visual Dependency Flow

```mermaid
graph TD
    %% Foundation Stories
    EPIC001[EPIC-001 Stories<br/>Web Platform Foundation]
    S025[STORY-025<br/>Project Scaffolding<br/>5 points]
    S026[STORY-026<br/>Git Integration<br/>5 points]
    S027[STORY-027<br/>Project API<br/>3 points]
    S028[STORY-028<br/>Project Browser UI<br/>5 points]
    
    %% Asset Stories
    S029[STORY-029<br/>Asset Service<br/>5 points]
    S030[STORY-030<br/>Asset Browser<br/>8 points]
    S031[STORY-031<br/>Asset Operations<br/>5 points]
    
    %% Takes Stories
    S021[STORY-021<br/>Takes Service<br/>5 points - Partial]
    S032[STORY-032<br/>Takes Gallery<br/>5 points]
    S033[STORY-033<br/>Takes Integration<br/>3 points]
    
    %% Git Advanced Stories
    S034[STORY-034<br/>Git Extensions<br/>5 points]
    S035[STORY-035<br/>Git UI<br/>8 points]
    S036[STORY-036<br/>Git Performance<br/>3 points]
    
    %% Import/Export Stories
    S037[STORY-037<br/>Project Export<br/>5 points]
    S038[STORY-038<br/>Project Import<br/>6 points]
    
    %% Dependencies
    EPIC001 --> S025
    S025 --> S026
    S025 --> S027
    S026 --> S027
    S027 --> S028
    
    EPIC001 --> S029
    S029 --> S030
    S029 --> S031
    S025 --> S031
    S026 --> S031
    
    S025 --> S021
    S021 --> S032
    S021 --> S033
    S026 --> S033
    
    S026 --> S034
    S034 --> S035
    S034 --> S036
    
    S025 --> S037
    S026 --> S037
    S029 --> S037
    S021 --> S037
    S037 --> S038
    
    %% Styling
    classDef foundation fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef asset fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef takes fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef git fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef export fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef partial fill:#ffebee,stroke:#b71c1c,stroke-width:3px
    
    class S025,S026,S027,S028 foundation
    class S029,S030,S031 asset
    class S021,S032,S033 takes
    class S034,S035,S036 git
    class S037,S038 export
    class S021 partial
```

## Sprint Parallelization Opportunities

### Sprint 1: Foundation (Week 1-2)
```
Backend Team:
- STORY-025 (Days 1-5)
- STORY-026 (Days 3-7) - Can start once 025 directory structure is defined
- STORY-027 (Days 6-8)

Frontend Team:
- STORY-028 (Days 4-10) - Can start mockups early, integrate with API later
```

### Sprint 2: Assets (Week 3-4)
```
Backend Team:
- STORY-029 (Days 1-5)
- STORY-031 (Days 6-10) - Requires 029 service

Frontend Team:
- STORY-030 (Days 1-10) - Can develop with mock data initially
```

### Sprint 3: Takes (Week 5-6)
```
Backend Team:
- Complete STORY-021 (Days 1-2)
- STORY-033 (Days 3-5)

Frontend Team:
- STORY-032 (Days 1-8) - Can start with existing takes service
```

### Sprint 4: Git Advanced (Week 7-8)
```
Backend Team:
- STORY-034 (Days 1-5)
- STORY-036 (Days 6-8)

Frontend Team:
- STORY-035 (Days 2-10) - Heavy UI work
```

### Sprint 5: Import/Export (Week 9-10)
```
Full Team:
- STORY-037 (Days 1-5)
- STORY-038 (Days 6-10)
```

## Critical Dependencies

### Must Complete First
1. **STORY-025** - Everything depends on project structure
2. **STORY-026** - Git is foundational for version control

### Can Be Deferred
1. **STORY-036** - Performance optimization
2. **STORY-037/038** - Import/Export (nice to have)

### Parallel Work Opportunities
- **Frontend/Backend Split**: Most sprints allow parallel work
- **Asset System**: Can be developed independently once file APIs exist
- **Git UI**: Can use mock data while backend is built

## Risk Areas

### High Risk Dependencies
- **STORY-025 → All**: Project structure blocks everything
- **STORY-021 Partial**: Unknown remaining work could impact sprint 3
- **STORY-030**: Large UI component (8 points) could slip

### Mitigation Strategies
1. Start STORY-025 immediately with senior developer
2. Assess STORY-021 status in sprint planning
3. Consider splitting STORY-030 if needed
4. Keep STORY-037/038 as stretch goals