# Validate Story Implementation

Comprehensive validation of story implementation using the QA Engineer persona and BMAD quality assurance methodology.

$ARGUMENTS: story_id, validation_scope (unit/integration/end-to-end/all), automated_only (true/false)

## Task
Execute thorough validation of story implementation against acceptance criteria, ensuring quality standards and proper integration with the BMAD film crew agent architecture.

## QA Engineer Persona Application
Use the QA Engineer persona from `.bmad-core/personas/qa-engineer.md`:
- **Test Strategy** - Comprehensive testing approach and coverage analysis
- **Quality Validation** - Code quality, performance, and reliability assessment
- **Integration Testing** - Cross-component and system integration validation
- **User Experience** - Blender addon usability and workflow validation
- **Regression Prevention** - Ensure new changes don't break existing functionality

## Validation Framework

### Test Execution Commands
```bash
# Run all tests (local)
make test

# Run tests with coverage
make test-coverage

# Run tests in Docker (recommended for consistency)
make test-e2e
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Run specific test categories
make test-backend     # Backend tests only
make test-frontend    # Frontend tests only
make test-quick      # Unit tests only (skip integration)

# Debug specific tests
cd backend && pytest -xvs tests/test_specific.py
cd frontend && npm test ComponentName
```

### Validation Process
```bash
# 1. Acceptance Criteria Validation
# Verify each acceptance criterion is met
for criteria in $(get_acceptance_criteria $story_id); do
    validate_criteria $criteria
    document_validation_result $criteria
done

# 2. Technical Quality Assessment
- Code quality and standards compliance
- Integration with BMAD architecture
- Performance and resource usage
- Error handling and edge cases

# 3. Integration Testing
- Agent system integration
- Backend service communication
- Blender addon functionality
- Asset data model consistency

# 4. User Experience Validation
- Blender UI/UX standards compliance
- Workflow integration smoothness
- Error messaging and user feedback
- Documentation accuracy
```

### Coverage Requirements
- **Unit Tests**: 80% minimum coverage
- **Critical Paths**: 90% coverage required
- **New Code**: 100% coverage for new features

See `.bmad-core/methods/TESTING-GUIDE.md` for detailed testing instructions.

## Testing Categories

### Unit Testing Validation
```python
# Validate unit test coverage and quality
def validate_unit_tests(story_id):
    """Ensure comprehensive unit test coverage"""
    
    # Test coverage analysis
    coverage_report = run_coverage_analysis()
    assert coverage_report.percentage >= 80
    
    # Test quality assessment
    test_quality = assess_test_quality()
    assert test_quality.score >= 'good'
    
    # Agent-specific testing patterns
    if story_involves_agent(story_id):
        validate_agent_tests()
```

### Integration Testing Validation
```python
# Validate integration with BMAD systems
def validate_integration_tests(story_id):
    """Test integration with film crew agents and backends"""
    
    # Agent orchestration testing
    if story_involves_agents(story_id):
        validate_crewai_integration()
        validate_agent_communication()
    
    # Backend service integration
    if story_involves_backends(story_id):
        validate_comfyui_integration()
        validate_wan2gp_integration()
        validate_litellm_integration()
    
    # Blender addon integration
    validate_blender_integration()
    validate_ui_functionality()
```

### End-to-End Testing Validation
```python
# Validate complete workflow functionality  
def validate_e2e_tests(story_id):
    """Test complete user workflows"""
    
    # User workflow testing
    for workflow in get_user_workflows(story_id):
        execute_workflow_test(workflow)
        validate_workflow_outcomes(workflow)
    
    # Film production pipeline testing
    if story_affects_pipeline(story_id):
        validate_production_pipeline()
```

## Quality Assessment Areas

### Code Quality Validation
- **Style Compliance** - PEP 8 and project coding standards
- **Type Annotation** - Proper type hints and documentation
- **Error Handling** - Robust error handling and user feedback
- **Performance** - Resource usage and execution efficiency
- **Security** - Input validation and safe API interactions

### Architecture Compliance
- **BMAD Patterns** - Adherence to established agent architecture
- **Blender Integration** - Proper bpy API usage and addon patterns
- **CrewAI Framework** - Correct agent implementation and orchestration
- **Asset Data Model** - Proper custom property usage and data management

### User Experience Validation
- **Blender UI Standards** - Consistent with Blender's design language
- **Workflow Integration** - Smooth integration with existing Blender workflows
- **Error Messaging** - Clear and actionable error messages
- **Documentation** - Accurate and helpful user documentation

## Validation Reporting
```markdown
# Validation Report: {story_id}

## Summary
- Overall validation status: PASS/FAIL
- Test coverage: {percentage}%
- Quality score: {score}/10
- Integration status: PASS/FAIL

## Acceptance Criteria Validation
- [ ] Criterion 1: PASS/FAIL - Details
- [ ] Criterion 2: PASS/FAIL - Details
- [ ] Criterion 3: PASS/FAIL - Details

## Technical Quality Assessment
- Code quality: {score}/10
- Architecture compliance: PASS/FAIL
- Performance: PASS/FAIL
- Security: PASS/FAIL

## Integration Testing Results
- Agent integration: PASS/FAIL
- Backend integration: PASS/FAIL
- Blender integration: PASS/FAIL
- UI functionality: PASS/FAIL

## Issues Identified
- [ ] Issue 1: {description} - Priority: {high/medium/low}
- [ ] Issue 2: {description} - Priority: {high/medium/low}

## Recommendations
- [ ] Recommendation 1: {action_needed}
- [ ] Recommendation 2: {action_needed}
```

## Output Artifacts
- Comprehensive validation report with pass/fail status
- Test coverage analysis and quality metrics
- Integration testing results and evidence
- Issue tracking and remediation recommendations
- Story validation sign-off for sprint completion