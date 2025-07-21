import { writable } from 'svelte/store';
import { persistent } from '$lib/stores/persistent';

export interface QualityPreferences {
  [taskType: string]: {
    preferredTier: string;
    lastUsed: string;
  };
}

export interface UserPreferences {
  quality: QualityPreferences;
  theme: 'light' | 'dark' | 'auto';
  language: string;
  autoSave: boolean;
  notifications: boolean;
}

const defaultQualityPreferences: QualityPreferences = {
  character_portrait: { preferredTier: 'standard', lastUsed: new Date().toISOString() },
  character_fullbody: { preferredTier: 'standard', lastUsed: new Date().toISOString() },
  scene_generation: { preferredTier: 'standard', lastUsed: new Date().toISOString() },
  style_generation: { preferredTier: 'standard', lastUsed: new Date().toISOString() },
  video_generation: { preferredTier: 'standard', lastUsed: new Date().toISOString() },
  lighting_generation: { preferredTier: 'standard', lastUsed: new Date().toISOString() }
};

const defaultPreferences: UserPreferences = {
  quality: defaultQualityPreferences,
  theme: 'auto',
  language: 'en',
  autoSave: true,
  notifications: true
};

export const userPreferences = {
  // Quality preferences
  quality: persistent<QualityPreferences>('quality-preferences', defaultQualityPreferences),

  setQualityPreference(taskType: string, tier: string): void {
    userPreferences.quality.update(prefs => ({
      ...prefs,
      [taskType]: {
        preferredTier: tier,
        lastUsed: new Date().toISOString()
      }
    }));
  },

  getQualityPreference(taskType: string): string {
    const prefs = userPreferences.quality.get();
    return prefs[taskType]?.preferredTier || 'standard';
  },

  // General preferences
  ...persistent<UserPreferences>('user-preferences', defaultPreferences)
};

export const qualityPreferences = {
  set: userPreferences.setQualityPreference,
  get: userPreferences.getQualityPreference,
  getAll: () => userPreferences.quality.get(),
  reset: (taskType?: string) => {
    if (taskType) {
      userPreferences.quality.update(prefs => {
        const updated = { ...prefs };
        delete updated[taskType];
        return { ...defaultQualityPreferences, ...updated };
      });
    } else {
      userPreferences.quality.set(defaultQualityPreferences);
    }
  }
};