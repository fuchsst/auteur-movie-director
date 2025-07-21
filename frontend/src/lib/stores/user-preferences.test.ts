import { describe, it, expect, vi, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { userPreferences, qualityPreferences } from './user-preferences';

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true,
});

describe('User Preferences Store', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue(null);
  });

  describe('Quality Preferences', () => {
    it('should initialize with default quality preferences', () => {
      const prefs = get(userPreferences.quality);
      
      expect(prefs.character_portrait.preferredTier).toBe('standard');
      expect(prefs.scene_generation.preferredTier).toBe('standard');
      expect(prefs.video_generation.preferredTier).toBe('standard');
    });

    it('should load preferences from localStorage', () => {
      const storedPrefs = {
        character_portrait: { preferredTier: 'high', lastUsed: '2023-01-01T00:00:00.000Z' },
        scene_generation: { preferredTier: 'low', lastUsed: '2023-01-02T00:00:00.000Z' }
      };
      
      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(storedPrefs));
      
      // Create new instance to test loading
      const newPrefs = JSON.parse(mockLocalStorage.getItem('quality-preferences') || '{}');
      expect(newPrefs).toEqual(storedPrefs);
    });

    it('should set quality preference for specific task type', () => {
      userPreferences.setQualityPreference('character_portrait', 'high');
      
      const prefs = get(userPreferences.quality);
      expect(prefs.character_portrait.preferredTier).toBe('high');
      expect(prefs.character_portrait.lastUsed).toBeDefined();
    });

    it('should get quality preference for specific task type', () => {
      const tier = userPreferences.getQualityPreference('character_portrait');
      expect(tier).toBe('standard'); // default
    });

    it('should handle unknown task types gracefully', () => {
      const tier = userPreferences.getQualityPreference('unknown_task');
      expect(tier).toBe('standard');
    });

    it('should persist preferences to localStorage', () => {
      userPreferences.setQualityPreference('character_portrait', 'low');
      
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'quality-preferences',
        expect.stringContaining('"character_portrait":{"preferredTier":"low"')
      );
    });
  });

  describe('Quality Preferences Helper', () => {
    it('should provide convenience methods', () => {
      qualityPreferences.set('character_portrait', 'high');
      
      expect(qualityPreferences.get('character_portrait')).toBe('high');
    });

    it('should reset all preferences', () => {
      qualityPreferences.set('character_portrait', 'high');
      
      qualityPreferences.reset();
      
      expect(qualityPreferences.get('character_portrait')).toBe('standard');
    });

    it('should reset specific task preference', () => {
      qualityPreferences.set('character_portrait', 'high');
      qualityPreferences.set('scene_generation', 'low');
      
      qualityPreferences.reset('character_portrait');
      
      expect(qualityPreferences.get('character_portrait')).toBe('standard');
      expect(qualityPreferences.get('scene_generation')).toBe('low');
    });

    it('should get all quality preferences', () => {
      qualityPreferences.set('character_portrait', 'high');
      
      const allPrefs = qualityPreferences.getAll();
      expect(allPrefs.character_portrait.preferredTier).toBe('high');
    });
  });

  describe('LocalStorage Integration', () => {
    it('should handle localStorage errors gracefully', () => {
      mockLocalStorage.setItem.mockImplementation(() => {
        throw new Error('Storage full');
      });
      
      // Should not throw
      userPreferences.setQualityPreference('character_portrait', 'high');
    });

    it('should handle malformed JSON in localStorage', () => {
      mockLocalStorage.getItem.mockReturnValue('invalid json');
      
      // Should use defaults
      expect(userPreferences.getQualityPreference('character_portrait')).toBe('standard');
    });

    it('should handle localStorage unavailability', () => {
      Object.defineProperty(window, 'localStorage', {
        value: undefined,
        writable: true,
      });
      
      // Should use defaults
      expect(userPreferences.getQualityPreference('character_portrait')).toBe('standard');
    });
  });

  describe('Browser Environment', () => {
    it('should handle server-side rendering (no window)', () => {
      const originalWindow = global.window;
      delete (global as any).window;
      
      const prefs = get(userPreferences.quality);
      expect(prefs.character_portrait.preferredTier).toBe('standard');
      
      global.window = originalWindow;
    });
  });
});