# Test Fixtures

This directory contains test files used by integration tests.

## Required Files

Create or add the following test files:

### Images
- `test-image.png` - Small test image (< 1MB)
- `character.png` - Character portrait image
- `john-base-face.png` - Base face for character tests
- `sarah_base_face.png` - Another character base face

### Models
- `style.safetensors` - Mock LoRA/style model file

### Videos
- `test-video.mp4` - Small test video
- `large-video.mp4` - Large video file (> 50MB) for Git LFS testing

### Scripts
- `test-script.fountain` - Sample screenplay in Fountain format

## Creating Mock Files

For testing purposes, you can create minimal mock files:

```bash
# Create small test image
convert -size 100x100 xc:white test-image.png

# Create mock safetensors file
echo "mock safetensors data" > style.safetensors

# Create small test video (requires ffmpeg)
ffmpeg -f lavfi -i testsrc=duration=1:size=320x240:rate=30 test-video.mp4

# Create large video for LFS testing
ffmpeg -f lavfi -i testsrc=duration=10:size=1920x1080:rate=30 large-video.mp4
```

## Note

These files are not tracked in Git. Each developer should create their own test fixtures or download from a shared location.