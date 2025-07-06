/**
 * API client for character asset management.
 * Foundation implementation for character data model.
 */

import { api } from './client';

/**
 * Character asset data model - foundation only
 */
export interface CharacterAsset {
  assetId: string;
  assetType: 'Character';
  name: string;
  description?: string;

  // Placeholders for future features
  triggerWord?: string | null;
  baseFaceImagePath?: string | null;
  loraModelPath?: string | null;
  loraTrainingStatus: 'untrained' | 'training' | 'completed' | 'failed';
  variations: Record<string, string>;
  usage: string[];
}

/**
 * Request to create a character
 */
export interface CreateCharacterRequest {
  name: string;
  description?: string;
}

/**
 * Response from character creation
 */
export interface CreateCharacterResponse {
  success: boolean;
  character: CharacterAsset;
  message: string;
}

/**
 * Response from listing characters
 */
export interface ListCharactersResponse {
  characters: CharacterAsset[];
  total: number;
}

/**
 * Character API client
 */
export const charactersApi = {
  /**
   * Add a character to a project
   * This is foundation only - no LoRA training or generation
   */
  async createCharacter(
    projectId: string,
    data: CreateCharacterRequest
  ): Promise<CreateCharacterResponse> {
    return api.post<CreateCharacterResponse>(`/workspace/projects/${projectId}/characters`, data);
  },

  /**
   * List all characters in a project
   */
  async listCharacters(projectId: string): Promise<ListCharactersResponse> {
    return api.get<ListCharactersResponse>(`/workspace/projects/${projectId}/characters`);
  },

  /**
   * Get a single character by ID (future implementation)
   */
  async getCharacter(projectId: string, characterId: string): Promise<CharacterAsset> {
    // Placeholder for future implementation
    throw new Error('Not implemented yet - part of future PRD');
  },

  /**
   * Update character metadata (future implementation)
   */
  async updateCharacter(
    projectId: string,
    characterId: string,
    data: Partial<CharacterAsset>
  ): Promise<CharacterAsset> {
    // Placeholder for future implementation
    throw new Error('Not implemented yet - part of future PRD');
  },

  /**
   * Delete a character (future implementation)
   */
  async deleteCharacter(projectId: string, characterId: string): Promise<void> {
    // Placeholder for future implementation
    throw new Error('Not implemented yet - part of future PRD');
  }
};
