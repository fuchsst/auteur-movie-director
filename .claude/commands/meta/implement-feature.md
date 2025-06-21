# Complete Feature Development Cycle

Orchestrates the full BMAD methodology for implementing a complete feature in the Blender Movie Director addon.

$ARGUMENTS: feature_name, priority (high/medium/low), target_sprint

## Task
Execute the complete BMAD feature development lifecycle from requirements definition through validation and deployment. This meta-command ensures proper methodology adherence across all development phases.

## BMAD Methodology Application
This command implements the full BMAD workflow using our established film crew personas and templates from .bmad-core/:

1. **Requirements Phase** - Business Analyst persona
2. **Epic Definition** - Product Owner persona  
3. **Story Breakdown** - Development Lead persona
4. **Implementation** - Developer persona with agent-specific templates
5. **Validation** - QA Engineer persona with comprehensive testing
6. **Status Tracking** - Project Manager persona

## Execution Flow
```bash
# 1. Define Product Requirements
claude exec define-prd $ARGUMENTS

# 2. Create Epic Structure  
claude exec define-epic $ARGUMENTS

# 3. Break Down into Stories
claude exec breakdown-stories $ARGUMENTS

# 4. Implement Each Story
# (Automatically iterates through generated stories)
for story in $(get_stories_for_feature $feature_name); do
    claude exec implement-story $story
    claude exec validate-implementation $story
done

# 5. Final Integration Validation
claude exec validate-addon

# 6. Update Project Status
claude exec update-project-status
```

## Integration with BMAD Structure
- Uses personas from `.bmad-core/personas/`
- References templates from `.bmad-core/templates/`
- Follows checklists from `.bmad-core/checklists/`
- Maintains film crew agent metaphor throughout development
- Ensures addon structure consistency with `blender_movie_director/` architecture

## Expected Outcomes
- Complete feature implementation following BMAD methodology
- Proper Blender addon integration with bpy patterns
- Agent integration with CrewAI framework
- Full test coverage and validation
- Updated project documentation and status