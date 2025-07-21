/**
 * Quality Tier Mapping Utilities
 * 
 * Maps between the three-tier quality system (low/standard/high)
 * and function runner's quality levels (draft/standard/high/ultra)
 */

import type { QualityLevel } from '$lib/api/functionRunner/types';

export const QUALITY_TIER_MAPPING = {
  low: 'draft',
  standard: 'standard',
  high: 'high'
} as const;

export type QualityTier = keyof typeof QUALITY_TIER_MAPPING;

/**
 * Convert three-tier quality to function runner quality level
 */
export function mapQualityTierToFunctionRunner(tier: QualityTier): QualityLevel {
  return QUALITY_TIER_MAPPING[tier];
}

/**
 * Get display name for quality tier
 */
export function getQualityDisplayName(tier: QualityTier): string {
  const names = {
    low: 'Low',
    standard: 'Standard',
    high: 'High'
  };
  return names[tier];
}

/**
 * Get description for quality tier
 */
export function getQualityDescription(tier: QualityTier): string {
  const descriptions = {
    low: 'Fast generation, basic quality',
    standard: 'Balanced quality and speed',
    high: 'Maximum quality, slower generation'
  };
  return descriptions[tier];
}

/**
 * Get all available quality tiers
 */
export function getAvailableTiers(): QualityTier[] {
  return Object.keys(QUALITY_TIER_MAPPING) as QualityTier[];
}