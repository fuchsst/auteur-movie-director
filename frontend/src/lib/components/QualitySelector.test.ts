import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, fireEvent, screen, waitFor } from '@testing-library/svelte';
import QualitySelector from './QualitySelector.svelte';
import { qualityTiersApi } from '$lib/api/quality-tiers';
import { userPreferences } from '$lib/stores/user-preferences';

// Mock API and stores
vi.mock('$lib/api/quality-tiers', () => ({
  qualityTiersApi: {
    getQualityTiers: vi.fn()
  }
}));

vi.mock('$lib/stores/user-preferences', () => ({
  userPreferences: {
    getQualityPreference: vi.fn(),
    setQualityPreference: vi.fn()
  }
}));

describe('QualitySelector', () => {
  const mockTiers = [
    {
      tier: 'low',
      description: 'Fast generation, basic quality',
      estimated_time: '30-45s',
      parameters_preview: { steps: 20, cfg_scale: 7.0 }
    },
    {
      tier: 'standard',
      description: 'Balanced quality and speed',
      estimated_time: '60-90s',
      parameters_preview: { steps: 35, cfg_scale: 7.5 }
    },
    {
      tier: 'high',
      description: 'Maximum quality, slower generation',
      estimated_time: '120-180s',
      parameters_preview: { steps: 60, cfg_scale: 8.0 }
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    
    (qualityTiersApi.getQualityTiers as any).mockResolvedValue({
      task_type: 'character_portrait',
      available_tiers: mockTiers
    });
    
    (userPreferences.getQualityPreference as any).mockReturnValue('standard');
  });

  it('should render loading state initially', () => {
    render(QualitySelector, { props: { taskType: 'character_portrait' } });
    
    expect(screen.getByText('Loading quality options...')).toBeInTheDocument();
  });

  it('should load and display quality tiers', async () => {
    render(QualitySelector, { props: { taskType: 'character_portrait' } });
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText('Loading quality options...')).not.toBeInTheDocument();
    });
    
    expect(screen.getAllByText('Low').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Standard').length).toBeGreaterThan(0);
    expect(screen.getAllByText('High').length).toBeGreaterThan(0);
  });

  it('should select default tier from user preferences', async () => {
    (userPreferences.getQualityPreference as any).mockReturnValue('high');
    
    render(QualitySelector, { props: { taskType: 'character_portrait' } });
    
    await waitFor(() => {
      expect(screen.queryByText('Loading quality options...')).not.toBeInTheDocument();
    });
    
    const highButton = screen.getAllByRole('button').find(btn => 
      btn.textContent?.includes('High')
    );
    expect(highButton).toHaveClass('selected');
  });

  it('should select tier on click', async () => {
    render(QualitySelector, { props: { taskType: 'character_portrait' } });
    
    await waitFor(() => {
      expect(screen.queryByText('Loading quality options...')).not.toBeInTheDocument();
    });
    
    const lowButton = screen.getAllByRole('button').find(btn => 
      btn.textContent?.includes('Low')
    );
    await fireEvent.click(lowButton!);
    
    expect(userPreferences.setQualityPreference).toHaveBeenCalledWith('character_portrait', 'low');
  });

  it('should dispatch qualityChange event on selection', async () => {
    const { component } = render(QualitySelector, { props: { taskType: 'character_portrait' } });
    
    const mockHandler = vi.fn();
    component.$on('qualityChange', mockHandler);
    
    await waitFor(() => {
      expect(screen.queryByText('Loading quality options...')).not.toBeInTheDocument();
    });
    
    const lowButton = screen.getAllByRole('button').find(btn => 
      btn.textContent?.includes('Low')
    );
    await fireEvent.click(lowButton!);
    
    expect(mockHandler).toHaveBeenCalledWith(
      expect.objectContaining({
        detail: expect.objectContaining({
          tier: 'low',
          taskType: 'character_portrait'
        })
      })
    );
  });

  it('should display error message on API failure', async () => {
    (qualityTiersApi.getQualityTiers as any).mockRejectedValue(new Error('API Error'));
    
    render(QualitySelector, { props: { taskType: 'character_portrait' } });
    
    await waitFor(() => {
      expect(screen.queryByText('Loading quality options...')).not.toBeInTheDocument();
    });
    
    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument();
    });
  });

  it('should display tier descriptions', async () => {
    render(QualitySelector, { props: { taskType: 'character_portrait' } });
    
    await waitFor(() => {
      expect(screen.queryByText('Loading quality options...')).not.toBeInTheDocument();
    });
    
    const buttons = screen.getAllByRole('button');
    const descriptions = buttons.map(btn => btn.getAttribute('title')).filter(Boolean);
    
    expect(descriptions).toContain('Fast generation, basic quality');
    expect(descriptions).toContain('Balanced quality and speed');
    expect(descriptions).toContain('Maximum quality, slower generation');
  });

  it('should display estimated times', async () => {
    render(QualitySelector, { props: { taskType: 'character_portrait' } });
    
    await waitFor(() => {
      expect(screen.queryByText('Loading quality options...')).not.toBeInTheDocument();
    });
    
    const buttons = screen.getAllByRole('button');
    const times = buttons.map(btn => {
      const timeSpan = btn.querySelector('.tier-time');
      return timeSpan?.textContent;
    }).filter(Boolean);
    
    expect(times).toContain('30-45s');
    expect(times).toContain('60-90s');
    expect(times).toContain('120-180s');
  });

  it('should handle task type changes', async () => {
    const { rerender } = render(QualitySelector, { props: { taskType: 'character_portrait' } });
    
    await waitFor(() => {
      expect(qualityTiersApi.getQualityTiers).toHaveBeenCalledWith('character_portrait');
    });
    
    await rerender({ taskType: 'scene_generation' });
    
    expect(qualityTiersApi.getQualityTiers).toHaveBeenCalledWith('scene_generation');
  });

  it('should show selected tier details', async () => {
    render(QualitySelector, { props: { taskType: 'character_portrait' } });
    
    await waitFor(() => {
      expect(screen.getAllByRole('button').length).toBeGreaterThan(0);
    });
    
    const standardButton = screen.getAllByRole('button').find(btn => 
      btn.textContent?.includes('Standard')
    );
    await fireEvent.click(standardButton!);
    
    expect(screen.getByText('Balanced quality and speed')).toBeInTheDocument();
    expect(screen.getByText('Est. time: 60-90s')).toBeInTheDocument();
  });

  it('should handle empty tier list', async () => {
    (qualityTiersApi.getQualityTiers as any).mockResolvedValue({
      task_type: 'invalid_task',
      available_tiers: []
    });
    
    render(QualitySelector, { props: { taskType: 'invalid_task' } });
    
    await waitFor(() => {
      expect(screen.queryByText('Low')).not.toBeInTheDocument();
      expect(screen.queryByText('Standard')).not.toBeInTheDocument();
      expect(screen.queryByText('High')).not.toBeInTheDocument();
    });
  });
});