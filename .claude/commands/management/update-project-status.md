# Update Project Status

Comprehensive project status tracking using the Project Manager persona and BMAD project management methodology.

$ARGUMENTS: update_scope (daily/weekly/sprint/milestone), include_metrics (true/false), stakeholder_report (true/false)

## Task
Track and report on project progress across all aspects of the Blender Movie Director addon development, providing visibility into sprint progress, agent implementation status, and overall project health.

## Project Manager Persona Application
Use the Project Manager persona from `.bmad-core/personas/project-manager.md`:
- **Progress Tracking** - Story completion, sprint velocity, and milestone progress
- **Risk Management** - Issue identification and mitigation strategies
- **Stakeholder Communication** - Status reporting and expectation management
- **Resource Planning** - Team capacity and development resource allocation
- **Quality Metrics** - Code quality, test coverage, and technical debt monitoring

## Status Tracking Framework
```bash
# 1. Sprint Progress Analysis
- Story completion tracking and velocity calculation
- Agent implementation progress across film crew roles
- Backend integration status and health metrics
- Blender addon functionality development progress

# 2. Quality Metrics Assessment
- Code coverage and quality scores
- Technical debt accumulation
- Bug count and resolution time
- Documentation completeness

# 3. Risk and Blocker Analysis
- Current development blockers
- Technical risks and mitigation status
- Dependency management and external factors
- Resource availability and capacity planning

# 4. Stakeholder Reporting
- Executive summary for leadership
- Technical progress for development stakeholders
- User experience updates for product stakeholders
```

## Progress Tracking Categories

### Sprint Progress Metrics
```python
def track_sprint_progress():
    """Track current sprint progress and velocity"""
    
    # Story completion tracking
    completed_stories = get_completed_stories(current_sprint)
    in_progress_stories = get_in_progress_stories(current_sprint)
    sprint_velocity = calculate_velocity(completed_stories)
    
    # Agent implementation progress
    agent_progress = track_agent_implementation_status()
    
    # Component development status
    ui_progress = track_ui_component_progress()
    backend_progress = track_backend_integration_progress()
    
    return {
        'story_completion': len(completed_stories),
        'velocity': sprint_velocity,
        'agent_progress': agent_progress,
        'component_progress': {
            'ui': ui_progress,
            'backend': backend_progress
        }
    }
```

### Quality Metrics Tracking
```python
def track_quality_metrics():
    """Monitor code quality and technical health"""
    
    # Code quality metrics
    code_coverage = get_test_coverage()
    quality_score = get_code_quality_score()
    technical_debt = assess_technical_debt()
    
    # Blender addon specific metrics
    addon_compliance = check_blender_addon_standards()
    agent_integration_health = check_agent_system_health()
    
    return {
        'code_coverage': code_coverage,
        'quality_score': quality_score,
        'technical_debt': technical_debt,
        'addon_compliance': addon_compliance,
        'agent_health': agent_integration_health
    }
```

### Agent Implementation Status
Track progress across all film crew agents:
- **Producer Agent** - Core orchestration and project management
- **Screenwriter Agent** - Story development and script structuring
- **Casting Director Agent** - Character asset management
- **Art Director Agent** - Style consistency and visual identity
- **Cinematographer Agent** - Video generation and camera control
- **Sound Designer Agent** - Audio creation and synchronization
- **Editor Agent** - Final assembly and post-production

## Status Report Templates

### Daily Status Update
```markdown
# Daily Status - {date}

## Sprint Progress
- Stories completed today: {count}
- Stories in progress: {count}
- Blockers: {blocker_list}

## Agent Development
- {Agent Name}: {status} - {progress_notes}

## Quality Metrics
- Test coverage: {percentage}%
- Build status: PASS/FAIL
- Critical issues: {count}

## Next Day Focus
- Priority stories: {story_list}
- Planned activities: {activity_list}
```

### Weekly Status Report
```markdown
# Weekly Status Report - Week {number}

## Executive Summary
- Sprint progress: {percentage}% complete
- Agent implementation: {agent_count}/{total_agents} complete
- Quality status: {overall_health}
- Key achievements: {achievement_list}

## Detailed Progress
### Story Completion
- Completed: {completed_count}
- In Progress: {in_progress_count}
- Velocity: {velocity} points/week

### Agent Implementation Status
- Producer: {status} - {details}
- Screenwriter: {status} - {details}
- Casting Director: {status} - {details}
- Art Director: {status} - {details}
- Cinematographer: {status} - {details}
- Sound Designer: {status} - {details}
- Editor: {status} - {details}

### Quality Metrics
- Code coverage: {percentage}%
- Quality score: {score}/10
- Technical debt: {level}
- Bug count: {count}

## Risks and Mitigation
- [ ] Risk 1: {description} - Mitigation: {strategy}
- [ ] Risk 2: {description} - Mitigation: {strategy}

## Next Week Priorities
- [ ] Priority 1: {description}
- [ ] Priority 2: {description}
```

## Project Health Dashboard
Real-time metrics and indicators:
- **Sprint Burn-down** - Story completion tracking
- **Agent Implementation Progress** - Film crew agent development status
- **Code Quality Trends** - Quality metrics over time
- **Backend Integration Health** - Service connectivity and reliability
- **Blender Addon Compliance** - Standards adherence and functionality

## Stakeholder Communication
- **Development Team** - Technical progress and implementation details
- **Product Stakeholders** - Feature delivery and user value metrics
- **Leadership** - High-level progress and risk management
- **User Community** - Feature previews and release planning

## Output Artifacts
- Updated project dashboard with current metrics
- Stakeholder-specific status reports
- Risk register and mitigation plan updates
- Sprint retrospective data collection
- Milestone progress tracking and forecasting