/**
 * Quality System Type Definitions
 */

export interface QualityPreset {
	id: string;
	name: string;
	description: string;
	level: number; // 1-4 (draft to ultra)
	is_custom: boolean;
	base_preset?: string;
	time_multiplier: number;
	resource_multiplier: number;
	cost_multiplier: number;
	parameters: Record<string, Record<string, any>>;
	usage_count: number;
	created_at?: string;
	updated_at?: string;
}

export interface CreatePresetRequest {
	name: string;
	description: string;
	level: number;
	base_preset?: string;
	time_multiplier?: number;
	resource_multiplier?: number;
	cost_multiplier?: number;
	parameters?: Record<string, Record<string, any>>;
}

export interface UpdatePresetRequest {
	name?: string;
	description?: string;
	parameters?: Record<string, Record<string, any>>;
	time_multiplier?: number;
	resource_multiplier?: number;
	cost_multiplier?: number;
}

export interface ApplyPresetRequest {
	template_id: string;
	preset_id: string;
	inputs: Record<string, any>;
}

export interface ComparisonRequest {
	template_id: string;
	inputs: Record<string, any>;
	presets?: string[];
	include_analysis?: boolean;
}

export interface ComparisonAnalysis {
	time_ratios: Record<string, number>;
	quality_metrics: Record<string, Record<string, number>>;
	resource_usage: Record<string, Record<string, number>>;
	recommendations: string[];
	best_value_preset?: string;
	fastest_acceptable_preset?: string;
}

export interface ComparisonResult {
	comparison_id: string;
	template_id: string;
	inputs: Record<string, any>;
	results: Record<string, any>;
	timings: Record<string, number>;
	analysis: ComparisonAnalysis;
	created_at: string;
}

export interface RecommendationRequest {
	use_case?: string;
	output_type?: string;
	target_platform?: string;
	time_constraint?: number;
	budget_constraint?: number;
	quality_requirement?: string;
	resolution?: [number, number];
	duration?: number;
	file_size_limit?: number;
}

export interface TradeOffs {
	time_factor: number;
	cost_factor: number;
	quality_gain: number;
	resource_usage: number;
	file_size_factor: number;
}

export interface QualityRecommendation {
	recommended_preset: string;
	confidence: number;
	reasoning: string;
	trade_offs: TradeOffs;
	alternatives: Array<{
		preset_id: string;
		name: string;
		score: number;
		reason: string;
		time_multiplier: number;
		cost_multiplier: number;
	}>;
	warnings: string[];
}

export interface ImpactEstimateRequest {
	template_id: string;
	preset_id: string;
	inputs: Record<string, any>;
}

export interface TimeEstimate {
	min_seconds: number;
	max_seconds: number;
	expected_seconds: number;
	confidence: number;
}

export interface ResourceEstimate {
	cpu_cores: number;
	memory_gb: number;
	vram_gb: number;
	disk_gb: number;
	network_mbps: number;
}

export interface QualityMetrics {
	resolution?: [number, number];
	detail_level: number;
	artifact_level: number;
	consistency: number;
	accuracy: number;
}

export interface QualityImpact {
	estimated_time: TimeEstimate;
	time_confidence: number;
	resource_requirements: ResourceEstimate;
	quality_metrics: QualityMetrics;
	cost_estimate: number;
	sample_outputs: Array<{
		sample_id: string;
		preset: string;
		execution_time: number;
		quality_metrics: Record<string, any>;
		thumbnail: string;
	}>;
	warnings: string[];
}

export enum QualityLevel {
	DRAFT = 1,
	STANDARD = 2,
	HIGH = 3,
	ULTRA = 4
}

export enum UseCase {
	PREVIEW = 'preview',
	ITERATION = 'iteration',
	REVIEW = 'review',
	CLIENT_PRESENTATION = 'client_presentation',
	FINAL_DELIVERY = 'final_delivery',
	SOCIAL_MEDIA = 'social_media',
	PRINT = 'print',
	BROADCAST = 'broadcast',
	WEB = 'web',
	MOBILE = 'mobile'
}