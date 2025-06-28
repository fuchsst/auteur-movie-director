# Define Epic with Acceptance Criteria

Creates a comprehensive epic using the Product Owner persona, breaking down PRD requirements into manageable development chunks.

$ARGUMENTS: epic_name, based_on_prd, target_milestone

## Task
Transform PRD requirements into a well-defined epic with clear acceptance criteria, scope boundaries, and integration points within the BMAD film crew agent architecture.

## Product Owner Persona Application
Use the Product Owner persona from `.bmad-core/personas/product-owner.md`:
- **Feature Vision** - Epic alignment with generative film studio goals
- **Scope Definition** - Clear boundaries and deliverable outcomes
- **Acceptance Criteria** - Testable and measurable success conditions
- **Priority Assessment** - Value-driven development prioritization
- **Stakeholder Alignment** - User and technical stakeholder buy-in

## Epic Definition Template
```markdown
# Epic: {epic_name}

## Epic Description
Brief description of the epic's purpose within the Blender Movie Director ecosystem.

## Business Value
- Impact on generative film production workflow
- User experience improvements
- Technical capability enhancements
- Agent orchestration benefits

## Scope & Boundaries
### In Scope
- Core functionality and features
- Blender addon integration requirements
- Agent system integration points
- Backend service integration needs

### Out of Scope  
- Future enhancements and extensions
- Non-essential features for MVP
- External system integrations beyond core backends

## Acceptance Criteria
### Functional Criteria
- [ ] Core feature functionality works within Blender
- [ ] Agent integration follows CrewAI framework patterns
- [ ] Backend service integration is stable and performant
- [ ] User interface follows Blender addon conventions

### Technical Criteria
- [ ] Code follows established addon architecture
- [ ] Agent implementation follows film crew metaphor
- [ ] Workflow templates are properly configured
- [ ] Integration tests pass successfully

### Quality Criteria
- [ ] User experience meets Blender standards
- [ ] Performance meets established benchmarks
- [ ] Documentation is complete and accurate
- [ ] Code quality meets project standards
```

## Epic Decomposition Strategy
Epic breakdown considerations:
- **Agent-Centric Stories** - Stories aligned with specific film crew agents
- **UI Component Stories** - Blender panel and operator implementations
- **Backend Integration Stories** - API client and workflow template development
- **Testing & Validation Stories** - Quality assurance and integration testing

## Integration with BMAD Structure
Epic must consider:
- **Film Crew Agents** - Which agents are involved and how they collaborate
- **Workflow Templates** - Required ComfyUI/Wan2GP template development
- **Asset Data Model** - Custom property and data structure requirements
- **UI Components** - Blender panels, operators, and Asset Browser integration

## Epic Sizing and Estimation
- **Complexity Assessment** - Technical difficulty and integration challenges
- **Development Effort** - Story point estimation using team velocity
- **Dependencies** - Cross-epic and external dependencies
- **Risk Factors** - Technical risks and mitigation strategies

## Output Artifacts
- Complete epic specification in `.bmad-core/epics/{epic_name}.md`
- Story breakdown ready for sprint planning
- Technical architecture decisions documented
- Acceptance criteria validated with stakeholders