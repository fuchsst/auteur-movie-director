import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent } from '@testing-library/svelte';
import AudioNode from './AudioNode.svelte';
import EffectNode from './EffectNode.svelte';
import CompositeNode from './CompositeNode.svelte';
import { NodeStatus, NodeType, BlendMode } from '$lib/types/nodes';
import type { AudioNodeData, EffectNodeData, CompositeNodeData } from '$lib/types/nodes';

describe('AudioNode', () => {
  const defaultAudioData: AudioNodeData = {
    label: 'Audio Test',
    status: NodeStatus.IDLE,
    inputs: [],
    outputs: [],
    parameters: {},
    audioSource: 'file',
    volume: 1
  };

  it('renders with default props', () => {
    const { getByText } = render(AudioNode, {
      props: {
        data: defaultAudioData,
        selected: false
      }
    });

    expect(getByText('Audio Test')).toBeInTheDocument();
    expect(getByText('🎵')).toBeInTheDocument();
  });

  it('handles audio source change', async () => {
    const mockDispatch = vi.fn();
    const { getByLabelText, component } = render(AudioNode, {
      props: {
        data: defaultAudioData,
        selected: false
      }
    });

    component.$on('parameterChange', mockDispatch);

    const sourceSelect = getByLabelText(/Source:/);
    await fireEvent.change(sourceSelect, { target: { value: 'generate' } });

    expect(mockDispatch).toHaveBeenCalledWith(
      expect.objectContaining({
        detail: {
          parameter: 'audioSource',
          value: 'generate'
        }
      })
    );
  });

  it('shows text input when source is generate', () => {
    const { getByPlaceholderText } = render(AudioNode, {
      props: {
        data: {
          ...defaultAudioData,
          audioSource: 'generate'
        },
        selected: false
      }
    });

    expect(getByPlaceholderText('Enter text for voice synthesis...')).toBeInTheDocument();
  });

  it('displays duration when provided', () => {
    const { getByText } = render(AudioNode, {
      props: {
        data: {
          ...defaultAudioData,
          duration: 5.5
        },
        selected: false
      }
    });

    expect(getByText('Duration: 5.5s')).toBeInTheDocument();
  });

  it('shows progress bar when executing', () => {
    const { container } = render(AudioNode, {
      props: {
        data: {
          ...defaultAudioData,
          status: NodeStatus.EXECUTING,
          progress: 50
        },
        selected: false
      }
    });

    const progressBar = container.querySelector('.progress-bar');
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveStyle('width: 50%');
  });

  it('displays error message when error exists', () => {
    const { getByText } = render(AudioNode, {
      props: {
        data: {
          ...defaultAudioData,
          error: 'Audio generation failed'
        },
        selected: false
      }
    });

    expect(getByText('Audio generation failed')).toBeInTheDocument();
  });
});

describe('EffectNode', () => {
  const defaultEffectData: EffectNodeData = {
    label: 'Effect Test',
    status: NodeStatus.IDLE,
    inputs: [],
    outputs: [],
    parameters: {
      brightness: 0,
      contrast: 0,
      saturation: 0,
      hue: 0
    },
    effectType: 'color',
    intensity: 100
  };

  it('renders with default props', () => {
    const { getByText } = render(EffectNode, {
      props: {
        data: defaultEffectData,
        selected: false
      }
    });

    expect(getByText('Effect Test')).toBeInTheDocument();
    expect(getByText('🎨')).toBeInTheDocument();
  });

  it('handles effect type change', async () => {
    const mockDispatch = vi.fn();
    const { getByLabelText, component } = render(EffectNode, {
      props: {
        data: defaultEffectData,
        selected: false
      }
    });

    component.$on('parameterChange', mockDispatch);

    const typeSelect = getByLabelText(/Effect Type:/);
    await fireEvent.change(typeSelect, { target: { value: 'blur' } });

    expect(mockDispatch).toHaveBeenCalledWith(
      expect.objectContaining({
        detail: {
          parameter: 'effectType',
          value: 'blur'
        }
      })
    );
  });

  it('displays effect-specific parameters', () => {
    const { getByText } = render(EffectNode, {
      props: {
        data: {
          ...defaultEffectData,
          effectType: 'color'
        },
        selected: false
      }
    });

    expect(getByText('Brightness:')).toBeInTheDocument();
    expect(getByText('Contrast:')).toBeInTheDocument();
    expect(getByText('Saturation:')).toBeInTheDocument();
    expect(getByText('Hue Shift:')).toBeInTheDocument();
  });

  it('shows preview image when provided', () => {
    const { getByAltText } = render(EffectNode, {
      props: {
        data: {
          ...defaultEffectData,
          preview: 'preview.jpg'
        },
        selected: false
      }
    });

    const preview = getByAltText('Effect preview');
    expect(preview).toBeInTheDocument();
    expect(preview).toHaveAttribute('src', 'preview.jpg');
  });

  it('applies correct status class', () => {
    const { container } = render(EffectNode, {
      props: {
        data: {
          ...defaultEffectData,
          status: NodeStatus.COMPLETE
        },
        selected: false
      }
    });

    const node = container.querySelector('.effect-node');
    expect(node).toHaveClass('status-complete');
  });
});

describe('CompositeNode', () => {
  const defaultCompositeData: CompositeNodeData = {
    label: 'Composite Test',
    status: NodeStatus.IDLE,
    inputs: [],
    outputs: [],
    parameters: {},
    layers: [
      {
        id: 'layer-1',
        name: 'Layer 1',
        visible: true,
        opacity: 1,
        blendMode: BlendMode.NORMAL,
        transform: { x: 0, y: 0, scale: 1, rotation: 0 }
      }
    ],
    blendMode: BlendMode.NORMAL,
    outputFormat: 'image'
  };

  it('renders with default props', () => {
    const { getByText } = render(CompositeNode, {
      props: {
        data: defaultCompositeData,
        selected: false
      }
    });

    expect(getByText('Composite Test')).toBeInTheDocument();
    expect(getByText('🎬')).toBeInTheDocument();
    expect(getByText('Layers (1)')).toBeInTheDocument();
  });

  it('handles add layer', async () => {
    const mockDispatch = vi.fn();
    const { getByText, component } = render(CompositeNode, {
      props: {
        data: defaultCompositeData,
        selected: false
      }
    });

    component.$on('parameterChange', mockDispatch);

    const addButton = getByText('+');
    await fireEvent.click(addButton);

    expect(mockDispatch).toHaveBeenCalledWith(
      expect.objectContaining({
        detail: {
          parameter: 'layers',
          value: expect.arrayContaining([
            expect.objectContaining({
              name: 'Layer 2'
            })
          ])
        }
      })
    );
  });

  it('handles layer visibility toggle', async () => {
    const mockDispatch = vi.fn();
    const { container, component } = render(CompositeNode, {
      props: {
        data: defaultCompositeData,
        selected: false
      }
    });

    component.$on('parameterChange', mockDispatch);

    const visibilityButton = container.querySelector('.visibility-toggle');
    await fireEvent.click(visibilityButton!);

    expect(mockDispatch).toHaveBeenCalledWith(
      expect.objectContaining({
        detail: {
          parameter: 'layers',
          value: expect.arrayContaining([
            expect.objectContaining({
              visible: false
            })
          ])
        }
      })
    );
  });

  it('handles layer opacity change', async () => {
    const mockDispatch = vi.fn();
    const { getByLabelText, component } = render(CompositeNode, {
      props: {
        data: defaultCompositeData,
        selected: false
      }
    });

    component.$on('parameterChange', mockDispatch);

    const opacitySlider = getByLabelText(/Opacity:/);
    await fireEvent.input(opacitySlider, { target: { value: '0.5' } });

    expect(mockDispatch).toHaveBeenCalledWith(
      expect.objectContaining({
        detail: {
          parameter: 'layers',
          value: expect.arrayContaining([
            expect.objectContaining({
              opacity: 0.5
            })
          ])
        }
      })
    );
  });

  it('handles output format change', async () => {
    const mockDispatch = vi.fn();
    const { getByLabelText, component } = render(CompositeNode, {
      props: {
        data: defaultCompositeData,
        selected: false
      }
    });

    component.$on('parameterChange', mockDispatch);

    const outputSelect = getByLabelText(/Output:/);
    await fireEvent.change(outputSelect, { target: { value: 'video' } });

    expect(mockDispatch).toHaveBeenCalledWith(
      expect.objectContaining({
        detail: {
          parameter: 'outputFormat',
          value: 'video'
        }
      })
    );
  });

  it('displays multiple input handles', () => {
    const { container } = render(CompositeNode, {
      props: {
        data: defaultCompositeData,
        selected: false
      }
    });

    const handles = container.querySelectorAll('[data-handlepos="left"]');
    expect(handles.length).toBeGreaterThan(1);
  });
});
