<script lang="ts">
	import { onMount } from 'svelte';
	import { Card } from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { Progress } from '$lib/components/ui/progress';
	import { Tabs, TabsContent, TabsList, TabsTrigger } from '$lib/components/ui/tabs';
	import { Clock, Cpu, DollarSign, BarChart3 } from 'lucide-svelte';
	import type { ComparisonResult } from '$lib/types/quality';
	import { qualityApi } from '$lib/api/quality';

	export let templateId: string;
	export let inputs: Record<string, any>;
	export let presets: string[] = ['draft', 'standard', 'high', 'ultra'];
	export let onComplete: (result: ComparisonResult) => void = () => {};

	let comparing = false;
	let comparisonResult: ComparisonResult | null = null;
	let error: string | null = null;

	async function startComparison() {
		try {
			comparing = true;
			error = null;
			
			comparisonResult = await qualityApi.compareQuality({
				template_id: templateId,
				inputs,
				presets,
				include_analysis: true
			});
			
			onComplete(comparisonResult);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Comparison failed';
			console.error('Comparison error:', err);
		} finally {
			comparing = false;
		}
	}

	function getQualityScore(preset: string): number {
		if (!comparisonResult?.analysis.quality_metrics[preset]) return 0;
		return comparisonResult.analysis.quality_metrics[preset].overall || 0;
	}

	function formatTime(seconds: number): string {
		if (seconds < 60) return `${seconds.toFixed(1)}s`;
		const minutes = Math.floor(seconds / 60);
		const secs = seconds % 60;
		return `${minutes}m ${secs.toFixed(0)}s`;
	}

	function getPresetColor(preset: string): string {
		const colors = {
			draft: 'text-blue-500',
			standard: 'text-green-500',
			high: 'text-orange-500',
			ultra: 'text-purple-500'
		};
		return colors[preset] || 'text-gray-500';
	}
</script>

<div class="space-y-4">
	{#if !comparisonResult}
		<Card class="p-6">
			<div class="text-center space-y-4">
				<BarChart3 class="w-12 h-12 mx-auto text-muted-foreground" />
				<div>
					<h3 class="font-semibold text-lg">Quality Comparison</h3>
					<p class="text-sm text-muted-foreground mt-1">
						Compare output quality across different presets
					</p>
				</div>
				<Button 
					on:click={startComparison} 
					disabled={comparing}
					size="lg"
				>
					{comparing ? 'Comparing...' : 'Start Comparison'}
				</Button>
			</div>
		</Card>
	{:else}
		<div class="space-y-4">
			<!-- Summary Cards -->
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<Card class="p-4">
					<h4 class="font-medium mb-2">Best Value</h4>
					<p class="text-2xl font-bold {getPresetColor(comparisonResult.analysis.best_value_preset || 'standard')}">
						{comparisonResult.analysis.best_value_preset || 'Standard'}
					</p>
					<p class="text-sm text-muted-foreground">
						Optimal quality per time ratio
					</p>
				</Card>
				
				<Card class="p-4">
					<h4 class="font-medium mb-2">Fastest Acceptable</h4>
					<p class="text-2xl font-bold {getPresetColor(comparisonResult.analysis.fastest_acceptable_preset || 'draft')}">
						{comparisonResult.analysis.fastest_acceptable_preset || 'Draft'}
					</p>
					<p class="text-sm text-muted-foreground">
						Minimum time with good quality
					</p>
				</Card>
			</div>

			<!-- Detailed Comparison -->
			<Card>
				<Tabs defaultValue="overview" class="w-full">
					<TabsList class="grid w-full grid-cols-3">
						<TabsTrigger value="overview">Overview</TabsTrigger>
						<TabsTrigger value="quality">Quality</TabsTrigger>
						<TabsTrigger value="performance">Performance</TabsTrigger>
					</TabsList>
					
					<TabsContent value="overview" class="p-4">
						<div class="space-y-4">
							{#each presets as preset}
								{@const timing = comparisonResult.timings[preset]}
								{@const hasError = comparisonResult.results[preset]?.error}
								
								<div class="flex items-center justify-between p-3 rounded-lg border">
									<div class="flex items-center gap-3">
										<Badge variant={hasError ? 'destructive' : 'default'}>
											{preset}
										</Badge>
										<span class="font-medium capitalize">{preset}</span>
									</div>
									
									{#if hasError}
										<span class="text-sm text-destructive">
											Failed
										</span>
									{:else if timing}
										<div class="flex items-center gap-4 text-sm">
											<div class="flex items-center gap-1">
												<Clock class="w-4 h-4" />
												{formatTime(timing)}
											</div>
											<div class="flex items-center gap-1">
												<BarChart3 class="w-4 h-4" />
												{(getQualityScore(preset) * 100).toFixed(0)}%
											</div>
										</div>
									{/if}
								</div>
							{/each}
						</div>
					</TabsContent>
					
					<TabsContent value="quality" class="p-4">
						<div class="space-y-4">
							{#each Object.entries(comparisonResult.analysis.quality_metrics) as [preset, metrics]}
								<div class="space-y-2">
									<h5 class="font-medium capitalize">{preset}</h5>
									<div class="space-y-2">
										{#each Object.entries(metrics) as [metric, score]}
											<div class="flex items-center justify-between">
												<span class="text-sm capitalize">
													{metric.replace('_', ' ')}
												</span>
												<div class="flex items-center gap-2">
													<Progress 
														value={score * 100} 
														class="w-24 h-2"
													/>
													<span class="text-sm text-muted-foreground">
														{(score * 100).toFixed(0)}%
													</span>
												</div>
											</div>
										{/each}
									</div>
								</div>
							{/each}
						</div>
					</TabsContent>
					
					<TabsContent value="performance" class="p-4">
						<div class="space-y-4">
							<!-- Time Ratios -->
							<div>
								<h5 class="font-medium mb-2">Time Ratios</h5>
								<div class="space-y-2">
									{#each Object.entries(comparisonResult.analysis.time_ratios) as [preset, ratio]}
										<div class="flex items-center justify-between">
											<span class="capitalize">{preset}</span>
											<Badge variant="outline">{ratio}x</Badge>
										</div>
									{/each}
								</div>
							</div>
							
							<!-- Resource Usage -->
							{#if Object.keys(comparisonResult.analysis.resource_usage).length > 0}
								<div>
									<h5 class="font-medium mb-2">Resource Usage</h5>
									<div class="space-y-2">
										{#each Object.entries(comparisonResult.analysis.resource_usage) as [preset, resources]}
											<div class="border rounded p-2">
												<p class="font-medium text-sm capitalize mb-1">{preset}</p>
												<div class="grid grid-cols-3 gap-2 text-xs">
													<div>
														<Cpu class="w-3 h-3 inline mr-1" />
														{resources.cpu?.toFixed(1) || 0}%
													</div>
													<div>
														Memory: {resources.memory_gb?.toFixed(1) || 0}GB
													</div>
													<div>
														VRAM: {resources.vram_gb?.toFixed(1) || 0}GB
													</div>
												</div>
											</div>
										{/each}
									</div>
								</div>
							{/if}
						</div>
					</TabsContent>
				</Tabs>
			</Card>

			<!-- Recommendations -->
			{#if comparisonResult.analysis.recommendations.length > 0}
				<Card class="p-4">
					<h4 class="font-medium mb-2">Recommendations</h4>
					<ul class="space-y-1 text-sm text-muted-foreground">
						{#each comparisonResult.analysis.recommendations as recommendation}
							<li class="flex items-start">
								<span class="mr-2">•</span>
								<span>{recommendation}</span>
							</li>
						{/each}
					</ul>
				</Card>
			{/if}
			
			<!-- Retry Button -->
			<div class="flex justify-center">
				<Button 
					variant="outline" 
					on:click={startComparison}
					disabled={comparing}
				>
					Run New Comparison
				</Button>
			</div>
		</div>
	{/if}
	
	{#if error}
		<Card class="p-4 border-destructive">
			<p class="text-sm text-destructive">{error}</p>
		</Card>
	{/if}
</div>