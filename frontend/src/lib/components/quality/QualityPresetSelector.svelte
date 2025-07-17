<script lang="ts">
	import { onMount } from 'svelte';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Card } from '$lib/components/ui/card';
	import { Label } from '$lib/components/ui/label';
	import { Select } from '$lib/components/ui/select';
	import { Sparkles, Zap, Gauge, Rocket } from 'lucide-svelte';
	import type { QualityPreset } from '$lib/types/quality';
	import { qualityApi } from '$lib/api/quality';

	export let value: string = 'standard';
	export let templateId: string | null = null;
	export let showDetails: boolean = true;
	export let disabled: boolean = false;
	export let onChange: (presetId: string) => void = () => {};

	let presets: QualityPreset[] = [];
	let selectedPreset: QualityPreset | null = null;
	let loading = true;

	const qualityIcons = {
		1: Zap,
		2: Gauge,
		3: Sparkles,
		4: Rocket
	};

	const qualityColors = {
		1: 'text-blue-500',
		2: 'text-green-500',
		3: 'text-orange-500',
		4: 'text-purple-500'
	};

	onMount(async () => {
		await loadPresets();
	});

	async function loadPresets() {
		try {
			loading = true;
			presets = await qualityApi.listPresets();
			
			// Select current preset
			if (value) {
				selectedPreset = presets.find(p => p.id === value) || null;
			}
		} catch (error) {
			console.error('Failed to load quality presets:', error);
		} finally {
			loading = false;
		}
	}

	function handlePresetChange(presetId: string) {
		value = presetId;
		selectedPreset = presets.find(p => p.id === presetId) || null;
		onChange(presetId);
	}

	function formatMultiplier(value: number): string {
		if (value === 1) return '1x';
		return `${value}x`;
	}

	function getPresetBadgeColor(level: number): string {
		switch (level) {
			case 1: return 'default';
			case 2: return 'secondary';
			case 3: return 'warning';
			case 4: return 'destructive';
			default: return 'default';
		}
	}
</script>

<div class="space-y-4">
	<div class="space-y-2">
		<Label for="quality-preset">Quality Preset</Label>
		
		{#if loading}
			<div class="animate-pulse h-10 bg-muted rounded" />
		{:else}
			<div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
				{#each presets.filter(p => !p.is_custom) as preset}
					<Button
						variant={value === preset.id ? 'default' : 'outline'}
						size="sm"
						class="justify-start"
						on:click={() => handlePresetChange(preset.id)}
						{disabled}
					>
						<svelte:component 
							this={qualityIcons[preset.level]} 
							class="w-4 h-4 mr-2 {qualityColors[preset.level]}" 
						/>
						{preset.name}
					</Button>
				{/each}
			</div>

			{#if presets.some(p => p.is_custom)}
				<div class="mt-2">
					<Label class="text-xs text-muted-foreground">Custom Presets</Label>
					<div class="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-1">
						{#each presets.filter(p => p.is_custom) as preset}
							<Button
								variant={value === preset.id ? 'default' : 'outline'}
								size="sm"
								class="justify-start"
								on:click={() => handlePresetChange(preset.id)}
								{disabled}
							>
								{preset.name}
							</Button>
						{/each}
					</div>
				</div>
			{/if}
		{/if}
	</div>

	{#if showDetails && selectedPreset && !loading}
		<Card class="p-4">
			<div class="space-y-3">
				<div class="flex items-center justify-between">
					<h4 class="font-medium">{selectedPreset.name}</h4>
					<Badge variant={getPresetBadgeColor(selectedPreset.level)}>
						Level {selectedPreset.level}
					</Badge>
				</div>

				<p class="text-sm text-muted-foreground">
					{selectedPreset.description}
				</p>

				<div class="grid grid-cols-3 gap-4 pt-2">
					<div class="space-y-1">
						<p class="text-xs text-muted-foreground">Time</p>
						<p class="text-sm font-medium">
							{formatMultiplier(selectedPreset.time_multiplier)}
						</p>
					</div>
					<div class="space-y-1">
						<p class="text-xs text-muted-foreground">Resources</p>
						<p class="text-sm font-medium">
							{formatMultiplier(selectedPreset.resource_multiplier)}
						</p>
					</div>
					<div class="space-y-1">
						<p class="text-xs text-muted-foreground">Cost</p>
						<p class="text-sm font-medium">
							{formatMultiplier(selectedPreset.cost_multiplier)}
						</p>
					</div>
				</div>

				{#if selectedPreset.is_custom && selectedPreset.base_preset}
					<div class="pt-2 border-t">
						<p class="text-xs text-muted-foreground">
							Based on: {selectedPreset.base_preset}
						</p>
					</div>
				{/if}
			</div>
		</Card>
	{/if}
</div>

<style>
	/* Custom styles if needed */
</style>