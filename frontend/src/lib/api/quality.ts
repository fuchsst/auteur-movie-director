/**
 * Quality Preset API Client
 * 
 * Handles all quality preset related API calls including:
 * - Preset management (CRUD operations)
 * - Quality comparison
 * - Recommendations
 * - Impact estimation
 */

import { API_BASE_URL } from '$lib/config';
import type {
	QualityPreset,
	CreatePresetRequest,
	UpdatePresetRequest,
	ApplyPresetRequest,
	ComparisonRequest,
	ComparisonResult,
	RecommendationRequest,
	QualityRecommendation,
	ImpactEstimateRequest,
	QualityImpact
} from '$lib/types/quality';

class QualityApi {
	private baseUrl: string;

	constructor(baseUrl: string = API_BASE_URL) {
		this.baseUrl = `${baseUrl}/api/v1/quality`;
	}

	private async request<T>(
		path: string,
		options: RequestInit = {}
	): Promise<T> {
		const response = await fetch(`${this.baseUrl}${path}`, {
			...options,
			headers: {
				'Content-Type': 'application/json',
				...options.headers
			}
		});

		if (!response.ok) {
			const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
			throw new Error(error.detail || `HTTP ${response.status}`);
		}

		return response.json();
	}

	/**
	 * List all available quality presets
	 */
	async listPresets(includeCustom = true, includeShared = true): Promise<QualityPreset[]> {
		const params = new URLSearchParams({
			include_custom: includeCustom.toString(),
			include_shared: includeShared.toString()
		});
		
		return this.request<QualityPreset[]>(`/presets?${params}`);
	}

	/**
	 * Get a specific quality preset
	 */
	async getPreset(presetId: string): Promise<QualityPreset> {
		return this.request<QualityPreset>(`/presets/${presetId}`);
	}

	/**
	 * Create a custom quality preset
	 */
	async createPreset(request: CreatePresetRequest): Promise<QualityPreset> {
		return this.request<QualityPreset>('/presets', {
			method: 'POST',
			body: JSON.stringify(request)
		});
	}

	/**
	 * Update a custom quality preset
	 */
	async updatePreset(presetId: string, request: UpdatePresetRequest): Promise<QualityPreset> {
		return this.request<QualityPreset>(`/presets/${presetId}`, {
			method: 'PUT',
			body: JSON.stringify(request)
		});
	}

	/**
	 * Delete a custom quality preset
	 */
	async deletePreset(presetId: string): Promise<void> {
		await this.request(`/presets/${presetId}`, {
			method: 'DELETE'
		});
	}

	/**
	 * Apply a quality preset to function inputs
	 */
	async applyPreset(request: ApplyPresetRequest): Promise<{
		template_id: string;
		preset_id: string;
		final_parameters: Record<string, any>;
	}> {
		return this.request('/apply', {
			method: 'POST',
			body: JSON.stringify(request)
		});
	}

	/**
	 * Compare outputs across different quality presets
	 */
	async compareQuality(request: ComparisonRequest): Promise<ComparisonResult> {
		return this.request<ComparisonResult>('/compare', {
			method: 'POST',
			body: JSON.stringify(request)
		});
	}

	/**
	 * Get a previous comparison result
	 */
	async getComparison(comparisonId: string): Promise<ComparisonResult> {
		return this.request<ComparisonResult>(`/compare/${comparisonId}`);
	}

	/**
	 * Get quality preset recommendation based on context
	 */
	async getRecommendation(request: RecommendationRequest): Promise<QualityRecommendation> {
		return this.request<QualityRecommendation>('/recommend', {
			method: 'POST',
			body: JSON.stringify(request)
		});
	}

	/**
	 * Estimate the impact of quality settings
	 */
	async estimateImpact(request: ImpactEstimateRequest): Promise<QualityImpact> {
		return this.request<QualityImpact>('/estimate', {
			method: 'POST',
			body: JSON.stringify(request)
		});
	}

	/**
	 * Share a custom preset with all users
	 */
	async sharePreset(presetId: string): Promise<void> {
		await this.request(`/presets/${presetId}/share`, {
			method: 'POST'
		});
	}

	/**
	 * Export a preset for sharing
	 */
	async exportPreset(presetId: string): Promise<{ export_path: string }> {
		return this.request(`/presets/${presetId}/export`, {
			method: 'POST'
		});
	}

	/**
	 * Import a preset from exported data
	 */
	async importPreset(presetData: Record<string, any>): Promise<QualityPreset> {
		return this.request<QualityPreset>('/presets/import', {
			method: 'POST',
			body: JSON.stringify(presetData)
		});
	}
}

// Export singleton instance
export const qualityApi = new QualityApi();