# User Story: STORY-074 - Professional Metadata Standards (Enhanced)

## Story Description
**As a** professional post-production supervisor
**I want** assembly outputs to meet industry metadata standards including CMX3600 EDL, SMPTE 258M-2004, and comprehensive color/audio metadata
**So that** our deliverables integrate seamlessly with professional post-production workflows (Premiere Pro, DaVinci Resolve, Final Cut Pro)

## Acceptance Criteria

### Functional Requirements
- [ ] **Enhanced CMX3600 EDL Compliance** with extended metadata fields
- [ ] **SMPTE 258M-2004 Standard Support** for professional interchange
- [ ] **Comprehensive Color Space Metadata** (Rec. 709, Rec. 2020, HDR10, Dolby Vision)
- [ ] **Professional Audio Track Mapping** (up to 32 channels, surround formats)
- [ ] **File Naming Convention** following industry standards (scene_shot_take_reel_v###)
- [ ] **Reel and Source Information** with professional metadata
- [ ] **Timecode Standards** (Drop Frame, Non-Drop Frame, 23.976p, 24p, 25p, 29.97p)
- [ ] **Frame Rate and Resolution Metadata** (4K, 8K support)
- [ ] **HDR Metadata** (PQ, HLG, HDR10+ dynamic metadata)
- [ ] **Professional Delivery Formats** (ProRes, DNxHD, XAVC)

### Technical Requirements
- [ ] **CMX3600 Extended Format** with custom metadata fields
- [ ] **SMPTE Timecode Calculation** with frame-accurate positioning
- [ ] **Color Space Detection and Preservation** throughout pipeline
- [ ] **Audio Configuration Profiles** (Stereo, 5.1, 7.1, Atmos)
- [ ] **Professional Naming Convention Engine**
- [ ] **Metadata Schema Validation** against industry standards
- [ ] **Cross-Platform Compatibility Testing** (Premiere, Resolve, FCP)
- [ ] **Frame Rate Conversion** with proper timecode adjustment
- [ ] **HDR to SDR Conversion** with tone mapping
- [ ] **Audio Loudness Standards** (ITU-R BS.1770-4)

### Quality Requirements
- [ ] **Industry Standard Compliance Tests** (SMPTE, CMX3600)
- [ ] **NLE Compatibility Verification** across major platforms
- [ ] **Metadata Round-trip Testing** (export → import → export)
- [ ] **Color Accuracy Validation** with color checker charts
- [ ] **Audio Sync Verification** with frame-accurate testing
- [ ] **Performance Testing** for large project metadata (1000+ shots)
- [ ]**HDR Validation** with professional monitoring
- [ ] **File Size and Quality Balance** optimization

## Implementation Notes

### Enhanced Professional Standards
```python
class EnhancedProfessionalMetadata:
    standard: str = "CMX3600"
    smpte_version: str = "SMPTE 258M-2004"
    smpte_timecode: str = "SMPTE 12M"
    
    # Color Space Support
    color_spaces = {
        "rec_709": "Rec. 709 (HD)",
        "rec_2020": "Rec. 2020 (UHD)",
        "dci_p3": "DCI-P3",
        "srgb": "sRGB"
    }
    
    # HDR Formats
    hdr_formats = {
        "hdr10": "HDR10 Static Metadata",
        "hdr10_plus": "HDR10+ Dynamic Metadata",
        "dolby_vision": "Dolby Vision",
        "hlg": "Hybrid Log-Gamma"
    }
    
    # Audio Configurations
    audio_configs = {
        "stereo": {"channels": 2, "format": "L R"},
        "surround_5_1": {"channels": 6, "format": "L R C LFE Ls Rs"},
        "surround_7_1": {"channels": 8, "format": "L R C LFE Ls Rs Lb Rb"},
        "atmos": {"channels": 128, "format": "Object-based"}
    }
```

### Enhanced CMX3600 EDL Format
```
TITLE: MyFilm_Professional_Assembly_v1.2
FCM: DROP FRAME

001  REEL001   V     C        01:00:00:00 01:00:05:12 00:00:00:00 00:00:05:12
* FROM CLIP NAME: Scene_01_Shot_001_Take_01_v003
* SOURCE FILE: Scene_01_Shot_001_Take_01_v003.mov
* REEL: REEL001
* COL: Rec. 709
* AUD: 1,2,3,4,5,6
* FPS: 23.976
* RESOLUTION: 3840x2160
* COLOR_SPACE: Rec. 709
* HDR_FORMAT: HDR10
* MASTER_DISPLAY: G(13250,34500)B(7500,3000)R(34000,16000)WP(15635,16450)L(10000000,1)
* MAX_CLL: 1000,400
* MAX_FALL: 400,150
* COMMENT: Scene 1, Shot 1 - Establishing shot with HDR10 metadata

002  REEL001   V     C        01:00:05:12 01:00:12:15 00:00:05:12 00:00:12:15
* FROM CLIP NAME: Scene_01_Shot_002_Take_03_v002
* SOURCE FILE: Scene_01_Shot_002_Take_03_v002.mov
* REEL: REEL001
* COL: Rec. 709
* AUD: 1,2
* FPS: 23.976
* RESOLUTION: 3840x2160
* AUDIO_FORMAT: 5.1 Surround
* AUDIO_LOUDNESS: -23 LUFS
* COMMENT: Scene 1, Shot 2 - Dialogue with 5.1 audio
```

### Advanced Metadata Schema
```python
class ProfessionalShotMetadata:
    def __init__(self):
        self.edl_entry = EDLBuilder()
        self.color_metadata = ColorMetadata()
        self.audio_metadata = AudioMetadata()
        self.file_metadata = FileMetadata()
    
    def generate_edl_entry(self, shot_data: dict) -> str:
        """Generate complete CMX3600 EDL entry"""
        entry = self.edl_entry.build_entry(shot_data)
        return self.format_professional_edl(entry)
    
    def generate_color_metadata(self, color_space: str, hdr_format: str) -> dict:
        """Generate comprehensive color metadata"""
        return {
            "color_space": color_space,
            "hdr_format": hdr_format,
            "master_display": self.get_master_display(color_space),
            "max_cll": self.get_max_cll(hdr_format),
            "max_fall": self.get_max_fall(hdr_format),
            "gamma": self.get_gamma_curve(color_space, hdr_format)
        }
    
    def generate_audio_metadata(self, config: str) -> dict:
        """Generate professional audio metadata"""
        return {
            "format": config,
            "channels": self.audio_configs[config]["channels"],
            "layout": self.audio_configs[config]["format"],
            "sample_rate": 48000,
            "bit_depth": 24,
            "loudness": {
                "integrated": -23.0,
                "true_peak": -1.0,
                "lra": 7.0
            }
        }
```

### Color Space Management
```python
class ColorSpaceManager:
    def __init__(self):
        self.color_spaces = {
            "rec_709": {
                "primaries": {"r": [0.64, 0.33], "g": [0.30, 0.60], "b": [0.15, 0.06]},
                "white_point": [0.3127, 0.3290],
                "gamma": 2.4,
                "max_nits": 100
            },
            "rec_2020": {
                "primaries": {"r": [0.708, 0.292], "g": [0.170, 0.797], "b": [0.131, 0.046]},
                "white_point": [0.3127, 0.3290],
                "gamma": 2.4,
                "max_nits": 10000
            }
        }
    
    def validate_color_space(self, color_space: str, resolution: str) -> bool:
        """Validate color space compatibility with resolution"""
        if resolution in ["3840x2160", "7680x4320"] and color_space == "rec_709":
            # Warning: Rec. 709 might be limiting for UHD
            return True
        return True
    
    def generate_hdr_metadata(self, hdr_format: str, max_nits: int) -> dict:
        """Generate HDR metadata based on format"""
        if hdr_format == "hdr10":
            return {
                "master_display": {
                    "red": [34000, 16000],
                    "green": [13250, 34500],
                    "blue": [7500, 3000],
                    "white_point": [15635, 16450],
                    "max_luminance": 10000000,
                    "min_luminance": 1
                },
                "max_cll": max_nits,
                "max_fall": max_nits // 2
            }
        return {}
```

### Professional Naming Convention
```python
class ProfessionalNamingConvention:
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.template = "{project}_{act}_{scene}_{shot}_{take}_{version}_{reel}"
    
    def generate_filename(self, metadata: dict) -> str:
        """Generate professional filename"""
        return self.template.format(
            project=self.project_name,
            act=f"A{metadata['act']:02d}",
            scene=f"S{metadata['scene']:03d}",
            shot=f"SH{metadata['shot']:03d}",
            take=f"T{metadata['take']:02d}",
            version=f"V{metadata['version']:03d}",
            reel=f"R{metadata['reel']:02d}"
        )
    
    def parse_filename(self, filename: str) -> dict:
        """Parse filename back to metadata"""
        pattern = r"(\w+)_A(\d+)_S(\d+)_SH(\d+)_T(\d+)_V(\d+)_R(\d+)"
        match = re.match(pattern, filename)
        if match:
            return {
                "project": match.group(1),
                "act": int(match.group(2)),
                "scene": int(match.group(3)),
                "shot": int(match.group(4)),
                "take": int(match.group(5)),
                "version": int(match.group(6)),
                "reel": int(match.group(7))
            }
        return {}
```

### NLE Integration Profiles
```python
class NLEIntegrationProfiles:
    def __init__(self):
        self.profiles = {
            "premiere_pro": {
                "edl_format": "cmx3600",
                "color_space": "rec_709",
                "preferred_codecs": ["ProRes 422 HQ", "ProRes 4444"],
                "audio_format": "48kHz 24-bit WAV"
            },
            "davinci_resolve": {
                "edl_format": "cmx3600",
                "color_space": "rec_709",
                "preferred_codecs": ["DNxHD 220x", "ProRes 4444"],
                "audio_format": "48kHz 24-bit WAV"
            },
            "final_cut_pro": {
                "edl_format": "xml",
                "color_space": "rec_709",
                "preferred_codecs": ["ProRes 422 HQ", "ProRes 4444"],
                "audio_format": "48kHz 24-bit WAV"
            }
        }
    
    def generate_edl_for_nle(self, shots: list, nle_type: str) -> str:
        """Generate NLE-specific EDL"""
        profile = self.profiles[nle_type]
        
        if profile["edl_format"] == "cmx3600":
            return self.generate_cmx3600_edl(shots, profile)
        elif profile["edl_format"] == "xml":
            return self.generate_xml_edl(shots, profile)
        
        raise ValueError(f"Unsupported NLE: {nle_type}")
```

### API Endpoints

#### Metadata Generation
```python
POST /api/v1/metadata/edl
{
  "project_id": "proj-123",
  "format": "cmx3600",
  "color_space": "rec_709",
  "hdr_format": "hdr10",
  "audio_config": "5.1_surround"
}

POST /api/v1/metadata/validate
{
  "edl_content": "...",
  "standard": "cmx3600"
}

POST /api/v1/metadata/nle-export
{
  "project_id": "proj-123",
  "nle_type": "premiere_pro",
  "format_settings": {
    "color_space": "rec_709",
    "resolution": "3840x2160",
    "frame_rate": 23.976
  }
}
```

### Testing Strategy

#### Compliance Testing
```python
def test_cmx3600_compliance():
    generator = ProfessionalMetadata()
    edl = generator.generate_edl_entry({
        "shot_id": "test-001",
        "reel": "REEL001",
        "source_in": "01:00:00:00",
        "source_out": "01:00:05:12",
        "record_in": "00:00:00:00",
        "record_out": "00:00:05:12"
    })
    
    # Validate CMX3600 format
    assert edl.startswith("001  REEL001")
    assert "FCM: DROP FRAME" in edl
    assert "* FROM CLIP NAME:" in edl

def test_hdr_metadata_generation():
    manager = ColorSpaceManager()
    hdr_meta = manager.generate_hdr_metadata("hdr10", 1000)
    
    assert hdr_meta["max_cll"] == 1000
    assert hdr_meta["master_display"]["red"] == [34000, 16000]
    assert "max_fall" in hdr_meta

def test_nle_compatibility():
    profiles = NLEIntegrationProfiles()
    
    # Test Premiere Pro compatibility
    edl = profiles.generate_edl_for_nle([], "premiere_pro")
    assert "TITLE:" in edl
    assert "FCM:" in edl
    
    # Test DaVinci Resolve compatibility
    edl = profiles.generate_edl_for_nle([], "davinci_resolve")
    assert edl is not None
```

## Story Size: **Large (13 story points)**

## Sprint Assignment: **Sprint 3-4 (Phase 2)**

## Dependencies
- **STORY-083**: Expanded Asset System for asset metadata
- **STORY-084**: Structured GenerativeShotList for shot metadata
- **STORY-071**: EDL generation foundation
- **STORY-073**: Take metadata for source information
- **Professional Standards**: SMPTE 258M-2004 validation tools

## Success Criteria
- 100% CMX3600 EDL compliance with extended metadata
- SMPTE 258M-2004 standard validation passed
- Color space preservation verified across formats
- Audio track mapping accurate for all configurations
- Professional NLE compatibility confirmed (Premiere, Resolve, FCP)
- HDR metadata correctly embedded and preserved
- File naming convention follows industry standards
- Performance tested with 1000+ shot projects
- Metadata round-trip testing passed without data loss

## Future Enhancements
- **Dolby Vision Profile 5** support
- **IMF Package** generation
- **ACES Color Space** integration
- **Netflix Delivery Specifications** compliance
- **Disney+ HDR** specifications
- **Apple ProRes RAW** metadata support