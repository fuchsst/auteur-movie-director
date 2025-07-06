<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { PropertyDefinition } from '$lib/types/properties';
  import { PropertyType } from '$lib/types/properties';

  export let property: PropertyDefinition;
  export let error: string | undefined = undefined;

  const dispatch = createEventDispatcher();

  let debounceTimer: NodeJS.Timeout;

  function handleChange(event: Event) {
    const target = event.target as HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;
    let value: string | number | boolean | string[] = target.value;

    // Type conversion based on property type
    if (property.type === PropertyType.NUMBER || property.type === PropertyType.RANGE) {
      const numValue = parseFloat(target.value);
      value = isNaN(numValue) ? ((property.defaultValue ?? 0) as number) : numValue;
    } else if (property.type === PropertyType.BOOLEAN) {
      value = (target as HTMLInputElement).checked;
    } else if (property.type === PropertyType.TAGS) {
      value = target.value
        .split(',')
        .map((tag: string) => tag.trim())
        .filter(Boolean);
    }

    // Debounce text inputs
    if (property.type === PropertyType.TEXT || property.type === PropertyType.TEXTAREA) {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        dispatch('change', value);
      }, 300);
    } else {
      dispatch('change', value);
    }
  }

  function formatDate(date: string | Date): string {
    if (!date) return '';
    const d = new Date(date);
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString();
  }
</script>

<div class="property-editor" class:has-error={!!error}>
  <div class="property-header">
    <label for={`prop-${property.key}`} class="property-label">
      {property.label}
      {#if property.required}
        <span class="required">*</span>
      {/if}
    </label>
    {#if property.description}
      <span class="property-help" title={property.description}>?</span>
    {/if}
  </div>

  <div class="property-control">
    {#if !property.editable}
      <div class="read-only-value">
        {#if property.type === PropertyType.DATE}
          {formatDate(property.value)}
        {:else if Array.isArray(property.value)}
          {property.value.join(', ')}
        {:else}
          {property.value ?? '-'}
        {/if}
      </div>
    {:else if property.type === PropertyType.TEXT}
      <input
        type="text"
        id={`prop-${property.key}`}
        value={property.value ?? ''}
        placeholder={property.placeholder}
        on:input={handleChange}
        class="property-input"
      />
    {:else if property.type === PropertyType.NUMBER}
      <input
        type="number"
        id={`prop-${property.key}`}
        value={property.value ?? 0}
        min={property.min}
        max={property.max}
        step={property.step ?? 1}
        on:change={handleChange}
        class="property-input"
      />
    {:else if property.type === PropertyType.SELECT}
      <select
        id={`prop-${property.key}`}
        value={property.value}
        on:change={handleChange}
        class="property-select"
      >
        {#if !property.required}
          <option value="">-- Select --</option>
        {/if}
        {#each property.options || [] as option}
          <option value={option.value}>{option.label}</option>
        {/each}
      </select>
    {:else if property.type === PropertyType.BOOLEAN}
      <label class="property-checkbox">
        <input
          type="checkbox"
          id={`prop-${property.key}`}
          checked={property.value}
          on:change={handleChange}
        />
        <span class="checkbox-label">Enabled</span>
      </label>
    {:else if property.type === PropertyType.COLOR}
      <div class="color-input-wrapper">
        <input
          type="color"
          id={`prop-${property.key}`}
          value={property.value ?? '#000000'}
          on:change={handleChange}
          class="property-color"
        />
        <input
          type="text"
          value={property.value ?? '#000000'}
          on:input={handleChange}
          class="property-input color-text"
          pattern="^#[0-9A-Fa-f]{6}$"
        />
      </div>
    {:else if property.type === PropertyType.TEXTAREA}
      <textarea
        id={`prop-${property.key}`}
        value={property.value ?? ''}
        placeholder={property.placeholder}
        rows={3}
        on:input={handleChange}
        class="property-textarea"
      />
    {:else if property.type === PropertyType.RANGE}
      <div class="range-control">
        <input
          type="range"
          id={`prop-${property.key}`}
          value={property.value ?? property.min ?? 0}
          min={property.min ?? 0}
          max={property.max ?? 100}
          step={property.step ?? 1}
          on:input={handleChange}
          class="property-range"
        />
        <span class="range-value">{property.value ?? property.min ?? 0}</span>
      </div>
    {:else if property.type === PropertyType.TAGS}
      <input
        type="text"
        id={`prop-${property.key}`}
        value={Array.isArray(property.value) ? property.value.join(', ') : ''}
        placeholder={property.placeholder || 'Enter tags separated by commas'}
        on:input={handleChange}
        class="property-input"
      />
    {/if}
  </div>

  {#if error}
    <div class="error-message">{error}</div>
  {/if}
</div>

<style>
  .property-editor {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .property-editor.has-error .property-control {
    border-color: var(--color-error, #ff4444);
  }

  .property-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .property-label {
    font-size: 0.813rem;
    color: var(--color-text-secondary, #b0b0b0);
    font-weight: 500;
  }

  .required {
    color: var(--color-error, #ff4444);
  }

  .property-help {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: var(--color-surface-secondary, #2a2a2a);
    border: 1px solid var(--color-border, #3a3a3a);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    cursor: help;
    color: var(--color-text-tertiary, #808080);
  }

  .property-control {
    position: relative;
  }

  .read-only-value {
    padding: 0.5rem;
    background: var(--color-surface-secondary, #2a2a2a);
    border: 1px solid var(--color-border, #3a3a3a);
    border-radius: 4px;
    font-size: 0.813rem;
    color: var(--color-text-tertiary, #808080);
    font-family: var(--font-mono, monospace);
  }

  .property-input,
  .property-select,
  .property-textarea {
    width: 100%;
    padding: 0.5rem;
    background: var(--color-surface-secondary, #2a2a2a);
    border: 1px solid var(--color-border, #3a3a3a);
    border-radius: 4px;
    font-size: 0.813rem;
    color: var(--color-text-primary, #fff);
    transition: all 0.2s ease;
  }

  .property-input:focus,
  .property-select:focus,
  .property-textarea:focus {
    outline: none;
    border-color: var(--color-primary, #007acc);
    background: var(--color-surface-primary, #1a1a1a);
  }

  .property-textarea {
    resize: vertical;
    min-height: 60px;
    font-family: inherit;
  }

  .property-checkbox {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
  }

  .property-checkbox input[type='checkbox'] {
    width: 16px;
    height: 16px;
    cursor: pointer;
  }

  .checkbox-label {
    font-size: 0.813rem;
    color: var(--color-text-primary, #fff);
  }

  .color-input-wrapper {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .property-color {
    width: 40px;
    height: 32px;
    padding: 2px;
    border: 1px solid var(--color-border, #3a3a3a);
    border-radius: 4px;
    cursor: pointer;
  }

  .color-text {
    flex: 1;
    font-family: var(--font-mono, monospace);
  }

  .range-control {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .property-range {
    flex: 1;
    height: 4px;
    -webkit-appearance: none;
    appearance: none;
    background: var(--color-surface-secondary, #2a2a2a);
    border-radius: 2px;
    outline: none;
  }

  .property-range::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 16px;
    height: 16px;
    background: var(--color-primary, #007acc);
    border-radius: 50%;
    cursor: pointer;
  }

  .property-range::-moz-range-thumb {
    width: 16px;
    height: 16px;
    background: var(--color-primary, #007acc);
    border-radius: 50%;
    cursor: pointer;
    border: none;
  }

  .range-value {
    min-width: 40px;
    text-align: right;
    font-size: 0.813rem;
    color: var(--color-text-secondary, #b0b0b0);
    font-family: var(--font-mono, monospace);
  }

  .error-message {
    font-size: 0.75rem;
    color: var(--color-error, #ff4444);
    margin-top: 0.25rem;
  }
</style>
