# User Story: STORY-088 - Digital Table Read Integration

## Story Description
**As a** filmmaker and creative director
**I want** an AI-powered "Digital Table Read" system that analyzes my initial creative concept and produces a comprehensive creative bible
**So that** every subsequent AI decision and generative output is anchored to the original human-defined creative and emotional intent, preventing creative drift

## Acceptance Criteria

### Functional Requirements
- [ ] **Dramaturg Agent** implementation for thematic and emotional analysis
- [ ] **Core Dramatic Question** extraction from initial concept
- [ ] **Central Theme** identification and documentation
- [ ] **Key Motifs and Symbols** recognition and cataloging
- [ ] **Emotional Beat Sheet** generation for story arc mapping
- [ ] **Creative Bible** generation as immutable project constitution
- [ ] **Context Propagation** system for all downstream agents
- [ ] **Human Approval Gates** at critical creative milestones

### Technical Requirements
- [ ] **Agentic Crew 2.0** hierarchical processing architecture
- [ ] **Story Circle Integration** (Dan Harmon's 8-step structure)
- [ ] **Emotional Arc Mapping** with intensity scoring
- [ ] **Thematic Consistency Validation** across all outputs
- [ ] **Creative Intent Locking** mechanism
- [ ] **Context Degradation Prevention** system
- [ ] **Multi-agent Collaboration** with feedback loops
- [ ] **Creative Constraint Engine** for vision preservation

### Quality Requirements
- [ ] **Thematic Accuracy** validation (90%+ alignment)
- [ ] **Emotional Arc Consistency** testing
- [ ] **Creative Drift Detection** and prevention
- [ ] **Human-in-the-loop** validation at each stage
- [ ] **Cross-agent Consistency** verification
- [ ] **Creative Bible Completeness** validation
- [ ] **Context Propagation Accuracy** testing

## Implementation Notes

### Dramaturg Agent Architecture
```python
class DramaturgAgent:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.thematic_analyzer = ThematicAnalyzer()
        self.emotional_mapper = EmotionalArcMapper()
        self.symbol_detector = SymbolDetector()
        self.creative_bible = CreativeBible()
    
    async def perform_digital_table_read(self, initial_concept: dict) -> DigitalTableReadResult:
        """Perform comprehensive creative analysis"""
        
        # Step 1: Analyze initial concept
        concept_analysis = await self.analyze_initial_concept(initial_concept)
        
        # Step 2: Extract dramatic question
        dramatic_question = await self.extract_dramatic_question(concept_analysis)
        
        # Step 3: Identify central theme
        central_theme = await self.identify_central_theme(concept_analysis)
        
        # Step 4: Map emotional arc
        emotional_beat_sheet = await self.create_emotional_beat_sheet(concept_analysis)
        
        # Step 5: Identify motifs and symbols
        motifs_symbols = await self.identify_motifs_symbols(concept_analysis)
        
        # Step 6: Generate creative bible
        creative_bible = await self.generate_creative_bible({
            'dramatic_question': dramatic_question,
            'central_theme': central_theme,
            'emotional_beat_sheet': emotional_beat_sheet,
            'motifs_symbols': motifs_symbols,
            'initial_concept': initial_concept
        })
        
        return DigitalTableReadResult(
            creative_bible=creative_bible,
            validation_score=await self.validate_creative_intent(creative_bible),
            requires_approval=await self.check_approval_required(creative_bible)
        )
    
    async def analyze_initial_concept(self, concept: dict) -> ConceptAnalysis:
        """Deep analysis of initial creative concept"""
        
        analysis = ConceptAnalysis()
        
        # Use Story Circle for structure
        story_circle = await self.apply_story_circle(concept)
        analysis.story_structure = story_circle
        
        # Analyze character journey
        character_analysis = await self.analyze_character_journey(concept)
        analysis.character_arc = character_analysis
        
        # Extract emotional beats
        emotional_beats = await self.extract_emotional_beats(concept)
        analysis.emotional_beats = emotional_beats
        
        # Identify visual motifs
        visual_motifs = await self.identify_visual_motifs(concept)
        analysis.visual_motifs = visual_motifs
        
        return analysis
```

### Story Circle Integration
```python
class StoryCircleAnalyzer:
    """Dan Harmon's Story Circle implementation"""
    
    def __init__(self):
        self.story_circle_steps = [
            "YOU",           # Protagonist in comfort zone
            "NEED",          # Protagonist wants something
            "GO",            # Protagonist enters unfamiliar situation
            "SEARCH",        # Protagonist adapts to new situation
            "FIND",          # Protagonist gets what they wanted
            "TAKE",          # Protagonist pays heavy price
            "RETURN",        # Protagonist returns to familiar situation
            "CHANGE"         # Protagonist has changed
        ]
    
    async def analyze_character_arc(self, concept: dict) -> CharacterArc:
        """Map character journey to Story Circle"""
        
        character_arc = CharacterArc()
        
        # Extract character want vs need
        want = await self.extract_character_want(concept)
        need = await self.extract_character_need(concept)
        
        character_arc.want = want
        character_arc.need = need
        character_arc.internal_conflict = await self.identify_internal_conflict(want, need)
        
        # Map to Story Circle steps
        for step in self.story_circle_steps:
            character_arc.steps[step] = await self.map_to_step(concept, step)
        
        return character_arc
    
    async def extract_character_want(self, concept: dict) -> str:
        """Extract surface-level character desire"""
        # Analyze concept for explicit character goals
        return concept.get('character_want', 'Survival')
    
    async def extract_character_need(self, concept: dict) -> str:
        """Extract deeper character need"""
        # Deep analysis of character's unconscious need
        return concept.get('character_need', 'Self-acceptance')
```

### Creative Bible System
```python
class CreativeBible:
    """Immutable creative constitution for project"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.sections = {
            'dramatic_question': None,
            'central_theme': None,
            'emotional_beat_sheet': None,
            'visual_motifs': [],
            'symbol_library': {},
            'character_bibles': {},
            'aesthetic_guidelines': {},
            'emotional_intensity_map': {},
            'context_locks': {}
        }
    
    async def generate_complete_bible(self, analysis_results: dict) -> CreativeBible:
        """Generate comprehensive creative bible"""
        
        bible = CreativeBible(self.project_id)
        
        # Core dramatic question
        bible.sections['dramatic_question'] = analysis_results['dramatic_question']
        
        # Central theme
        bible.sections['central_theme'] = {
            'primary_theme': analysis_results['central_theme'],
            'sub_themes': analysis_results.get('sub_themes', []),
            'theme_variations': await self.generate_theme_variations(analysis_results['central_theme'])
        }
        
        # Emotional beat sheet
        bible.sections['emotional_beat_sheet'] = await self.create_detailed_beat_sheet(
            analysis_results['emotional_beat_sheet']
        )
        
        # Visual motifs and symbols
        bible.sections['visual_motifs'] = await self.catalogue_visual_motifs(
            analysis_results['visual_motifs']
        )
        
        # Symbol library
        bible.sections['symbol_library'] = await self.build_symbol_library(
            analysis_results['symbols']
        )
        
        # Character bibles
        bible.sections['character_bibles'] = await self.create_character_bibles(
            analysis_results['characters']
        )
        
        # Aesthetic guidelines
        bible.sections['aesthetic_guidelines'] = await self.generate_aesthetic_guidelines(
            analysis_results
        )
        
        return bible
    
    async def create_detailed_beat_sheet(self, emotional_beats: list) -> dict:
        """Create detailed emotional beat sheet with intensity mapping"""
        
        beat_sheet = {}
        
        for beat in emotional_beats:
            beat_sheet[beat['name']] = {
                'position': beat['position'],
                'intensity': beat['intensity'],
                'emotional_tone': beat['tone'],
                'visual_cues': await self.generate_visual_cues(beat),
                'audio_cues': await self.generate_audio_cues(beat),
                'character_state': beat['character_state'],
                'thematic_relevance': beat['theme_connection']
            }
        
        return beat_sheet
```

### Context Propagation System
```python
class ContextPropagationSystem:
    """Ensures creative intent flows through all agentic processes"""
    
    def __init__(self, creative_bible: CreativeBible):
        self.creative_bible = creative_bible
        self.propagation_engine = PropagationEngine()
        self.context_validator = ContextValidator()
        self.lock_manager = ContextLockManager()
    
    async def propagate_context(self, target_agent: str, request_data: dict) -> dict:
        """Propagate creative context to any agent"""
        
        # Get relevant context for agent
        agent_context = await self.get_agent_relevant_context(target_agent, request_data)
        
        # Validate context integrity
        validated_context = await self.context_validator.validate(agent_context)
        
        # Apply context locks
        locked_context = await self.lock_manager.apply_locks(validated_context)
        
        return {
            'creative_bible_ref': self.creative_bible.id,
            'context_snapshot': locked_context,
            'validation_token': await self.generate_validation_token(locked_context),
            'usage_guidelines': await self.get_usage_guidelines(target_agent)
        }
    
    async def get_agent_relevant_context(self, agent_type: str, request: dict) -> dict:
        """Get only relevant context for specific agent"""
        
        context_map = {
            'screenwriter': ['dramatic_question', 'central_theme', 'character_bibles'],
            'art_director': ['visual_motifs', 'aesthetic_guidelines', 'symbol_library'],
            'casting_director': ['character_bibles', 'emotional_beat_sheet'],
            'prop_master': ['visual_motifs', 'symbol_library', 'aesthetic_guidelines'],
            'costume_designer': ['character_bibles', 'visual_motifs', 'emotional_beat_sheet'],
            'shot_designer': ['emotional_beat_sheet', 'visual_motifs', 'aesthetic_guidelines']
        }
        
        relevant_sections = context_map.get(agent_type, ['central_theme'])
        
        return {
            section: section
            for section in relevant_sections
            if section in self.creative_bible.sections
        }
    
    async def validate_context_usage(self, agent_output: dict, context: dict) -> ValidationResult:
        """Validate that agent output respects creative context"""
        
        validation = ValidationResult()
        
        # Check theme consistency
        theme_check = await self.validate_theme_consistency(agent_output, context)
        validation.theme_score = theme_check.score
        validation.theme_issues = theme_check.issues
        
        # Check emotional consistency
        emotional_check = await self.validate_emotional_consistency(agent_output, context)
        validation.emotional_score = emotional_check.score
        validation.emotional_issues = emotional_check.issues
        
        # Check visual consistency
        visual_check = await self.validate_visual_consistency(agent_output, context)
        validation.visual_score = visual_check.score
        validation.visual_issues = visual_check.issues
        
        return validation
```

### Agentic Crew 2.0 Architecture
```python
class AgenticCrewV2:
    """Hierarchical agentic crew with feedback loops"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.producer_agent = ProducerAgent()
        self.crew_members = {
            'screenwriter': ScreenwriterAgent(),
            'art_director': ArtDirectorAgent(),
            'casting_director': CastingDirectorAgent(),
            'dramaturg': DramaturgAgent(),
            'prop_master': PropMasterAgent(),
            'costume_designer': CostumeDesignerAgent(),
            'vfx_supervisor': VFXSupervisorAgent(),
            'shot_designer': ShotDesignerAgent()
        }
        self.collaboration_engine = CollaborationEngine()
    
    async def run_digital_table_read(self, initial_concept: dict) -> TableReadResult:
        """Run complete digital table read process"""
        
        # Phase 1: Dramaturg Analysis
        dramaturg_result = await self.crew_members['dramaturg'].perform_analysis(initial_concept)
        
        # Phase 2: Producer Review
        producer_approval = await self.producer_agent.review_dramaturg_output(dramaturg_result)
        
        if not producer_approval['approved']:
            return await self.handle_revision_request(producer_approval)
        
        # Phase 3: Creative Bible Generation
        creative_bible = await self.crew_members['dramaturg'].generate_creative_bible(dramaturg_result)
        
        # Phase 4: Agent Crew Formation
        crew_plan = await self.form_agent_crew(creative_bible)
        
        # Phase 5: Collaborative Pre-Production Meeting
        final_plan = await self.collaboration_engine.run_pre_production_meeting(
            crew_plan, creative_bible
        )
        
        return TableReadResult(
            creative_bible=creative_bible,
            crew_plan=final_plan,
            requires_human_approval=final_plan['requires_approval']
        )
    
    async def run_pre_production_meeting(self, crew_plan: dict, creative_bible: CreativeBible) -> dict:
        """Virtual pre-production meeting with all agents"""
        
        meeting_minutes = []
        
        # Check for conflicts
        conflicts = await self.identify_conflicts(crew_plan)
        
        for conflict in conflicts:
            resolution = await self.collaboration_engine.resolve_conflict(
                conflict, crew_plan, creative_bible
            )
            meeting_minutes.append({
                'conflict': conflict,
                'resolution': resolution,
                'agents_involved': resolution['agents']
            })
        
        # Optimize final plan
        optimized_plan = await self.optimize_plan(crew_plan, creative_bible)
        
        return {
            'final_plan': optimized_plan,
            'meeting_minutes': meeting_minutes,
            'requires_approval': len(conflicts) > 0
        }
```

### Human Approval System
```python
class HumanApprovalSystem:
    """Gates human approval at critical creative milestones"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.approval_gates = {
            'dramaturg_analysis': {
                'description': 'Dramaturg creative analysis',
                'criticality': 'high',
                'required_fields': ['dramatic_question', 'central_theme']
            },
            'creative_bible': {
                'description': 'Complete creative bible',
                'criticality': 'critical',
                'required_fields': ['all_sections']
            },
            'crew_plan': {
                'description': 'Agentic crew plan',
                'criticality': 'medium',
                'required_fields': ['agent_assignments', 'timeline']
            }
        }
    
    async def request_approval(self, gate_name: str, data: dict) -> ApprovalRequest:
        """Create approval request for human review"""
        
        gate = self.approval_gates[gate_name]
        
        approval_request = ApprovalRequest(
            gate_name=gate_name,
            description=gate['description'],
            data=data,
            required_fields=gate['required_fields'],
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        # Create human-readable summary
        approval_request.summary = await self.create_human_summary(data)
        
        # Store for review
        await self.store_approval_request(approval_request)
        
        # Send notification
        await self.notify_stakeholders(approval_request)
        
        return approval_request
    
    async def process_approval_response(self, response: ApprovalResponse) -> dict:
        """Process human approval response"""
        
        if response.approved:
            return {
                'status': 'approved',
                'next_phase': await self.determine_next_phase(response.gate_name),
                'context_lock': await self.lock_context(response.data)
            }
        else:
            return {
                'status': 'rejected',
                'revision_required': True,
                'feedback': response.feedback,
                'next_action': await self.determine_revision_action(response)
            }
```

### Creative Intent Validation
```python
class CreativeIntentValidator:
    """Validates that all outputs align with creative intent"""
    
    def __init__(self, creative_bible: CreativeBible):
        self.creative_bible = creative_bible
        self.validation_rules = self.load_validation_rules()
    
    async def validate_agent_output(self, agent_type: str, output: dict) -> ValidationResult:
        """Validate agent output against creative bible"""
        
        validation = ValidationResult(
            is_valid=True,
            issues=[],
            suggestions=[],
            confidence_score=1.0
        )
        
        # Theme consistency check
        theme_valid = await self.validate_theme_consistency(output)
        if not theme_valid['is_valid']:
            validation.is_valid = False
            validation.issues.extend(theme_valid['issues'])
        
        # Emotional arc consistency check
        emotional_valid = await self.validate_emotional_arc(output)
        if not emotional_valid['is_valid']:
            validation.is_valid = False
            validation.issues.extend(emotional_valid['issues'])
        
        # Visual style consistency check
        visual_valid = await self.validate_visual_style(output)
        if not visual_valid['is_valid']:
            validation.is_valid = False
            validation.issues.extend(visual_valid['issues'])
        
        validation.confidence_score = self.calculate_confidence_score(validation)
        
        return validation
    
    async def detect_creative_drift(self, current_output: dict, original_intent: dict) -> DriftReport:
        """Detect if creative output has drifted from original intent"""
        
        drift_indicators = []
        
        # Check for theme drift
        theme_drift = await self.detect_theme_drift(current_output, original_intent)
        if theme_drift['score'] < 0.8:
            drift_indicators.append({
                'type': 'theme_drift',
                'severity': 'medium',
                'description': 'Theme has deviated from original intent',
                'suggested_correction': theme_drift['correction']
            })
        
        # Check for character drift
        character_drift = await self.detect_character_drift(current_output, original_intent)
        if character_drift['score'] < 0.9:
            drift_indicators.append({
                'type': 'character_drift',
                'severity': 'high',
                'description': 'Character behavior inconsistent with bible',
                'suggested_correction': character_drift['correction']
            })
        
        return DriftReport(
            has_drift=len(drift_indicators) > 0,
            indicators=drift_indicators,
            overall_score=self.calculate_drift_score(drift_indicators)
        )
```

### API Integration
```python
# Digital Table Read API
POST /api/v1/digital-table-read
{
    "project_id": "proj-123",
    "initial_concept": {
        "title": "The Last Detective",
        "logline": "A grizzled detective must confront his past while solving his final case",
        "theme": "Redemption through sacrifice",
        "tone": "Neo-noir with existential dread",
        "characters": [...],
        "setting": "Rain-soaked 1940s city"
    }
}

# Get creative bible
GET /api/v1/projects/{project_id}/creative-bible

# Validate agent output
POST /api/v1/validate-creative-intent
{
    "project_id": "proj-123",
    "agent_type": "screenwriter",
    "output": {
        "scene_description": "...",
        "character_actions": [...],
        "dialogue": [...]
    }
}

# Request human approval
POST /api/v1/approval-requests
{
    "project_id": "proj-123",
    "gate_name": "creative_bible",
    "data": {...},
    "stakeholders": ["director@studio.com", "producer@studio.com"]
}
```

### Testing Strategy

#### Creative Validation Testing
```python
class DigitalTableReadTests:
    async def test_dramaturg_analysis():
        dramaturg = DramaturgAgent("test-project")
        
        concept = {
            "title": "Test Film",
            "logline": "A hero must face their past",
            "theme": "Redemption",
            "characters": [{"name": "Hero", "arc": "redemption"}]
        }
        
        result = await dramaturg.perform_digital_table_read(concept)
        
        assert result.creative_bible is not None
        assert "dramatic_question" in result.creative_bible.sections
        assert "central_theme" in result.creative_bible.sections
        assert result.validation_score >= 0.9
    
    async test_context_propagation():
        propagation = ContextPropagationSystem(creative_bible)
        
        context = await propagation.propagate_context("screenwriter", {})
        
        assert "creative_bible_ref" in context
        assert "context_snapshot" in context
        assert "validation_token" in context
    
    async test_creative_drift_detection():
        validator = CreativeIntentValidator(creative_bible)
        
        original = {"theme": "redemption", "tone": "dark"}
        current = {"theme": "revenge", "tone": "light"}
        
        drift = await validator.detect_creative_drift(current, original)
        
        assert drift.has_drift is True
        assert len(drift.indicators) > 0
        assert drift.overall_score < 0.8
```

## Story Size: **Extra Large (21 story points)**

## Sprint Assignment: **Sprint 7-8 (Phase 4)**

## Dependencies
- **STORY-083**: Expanded Asset System for character/prop definitions
- **STORY-084**: Structured GenerativeShotList for emotional beats
- **STORY-085**: Agent Integration Bridge for crew coordination
- **STORY-086**: Breakdown View Interface for creative input
- **STORY-087**: Storyboard integration for visual context
- **Agent Framework**: Agentic crew system infrastructure
- **NLP Engine**: Natural language processing capabilities
- **Validation Engine**: Creative consistency checking

## Success Criteria
- Dramaturg agent successfully analyzes all creative concepts
- Creative bible generated with 95%+ completeness
- Context propagation works across all agent types
- Creative drift detection catches 90%+ deviations
- Human approval gates functional at all milestones
- Emotional beat sheet accuracy 90%+
- Thematic consistency maintained across 1000+ shots
- User acceptance testing passed with creative professionals
- Cross-agent collaboration efficiency 85%+

## Future Enhancements
- **AI Creative Director**: Advanced creative decision making
- **Emotional AI Models**: Deeper emotional understanding
- **Cultural Context Engine**: Multi-cultural creative adaptation
- **Genre-Specific Modules**: Specialized analysis for genres
- **Collaborative Creative Sessions**: Multi-director input
- **Real-time Creative Adjustments**: Dynamic bible updates