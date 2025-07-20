<!--
Element Category Display
STORY-086: Individual element display component

Displays a single production element with editing capabilities
and status management.
-->

<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { BreakdownElement, BreakdownElementStatus } from '$lib/types/breakdown';

  export let element: BreakdownElement;

  const dispatch = createEventDispatcher();

  let isEditing = false;
  let editedElement = { ...element };

  const statusOptions: BreakdownElementStatus[] = [
    'detected',
    'confirmed',
    'linked',
    'created',
    'ignored'
  ];

  const statusColors = {
    detected: 'var(--color-warning)',
    confirmed: 'var(--color-success)',
    linked: 'var(--color-info)',
    created: 'var(--color-primary)',
    ignored: 'var(--color-text-secondary)'
  };

  function startEdit() {
    isEditing = true;
    editedElement = { ...element };
  }

  function cancelEdit() {
    isEditing = false;
    editedElement = { ...element };
  }

  function saveEdit() {
    dispatch('update', editedElement);
    isEditing = false;
  }

  function updateStatus(status: BreakdownElementStatus) {
    dispatch('update', { ...element, status });
  }

  function formatCost(cost: number) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(cost);
  }
</script>

<div class="element-card" class:editing={isEditing}>
  <div class="element-header">
    <div class="element-info">
      <span class="element-type">{element.element_type.toUpperCase()}</span>
      <span class="element-name">{element.name}</span>
      <span 
        class="element-status status-{element.status}" 
        style="color: {statusColors[element.status]}"
      >
        {element.status}
      </span>
    </div>
    
    <div class="element-actions">
      {#if !isEditing}
        <button class="btn btn-sm" on:click={startEdit}>Edit</button>
      {/if}
    </div>
  </div>

  {#if isEditing}
    <div class="edit-form">
      <div class="form-group">
        <label>Name</label>
        <input type="text" bind:value={editedElement.name} />
      </div>
      
      <div class="form-group">
        <label>Description</label>
        <textarea bind:value={editedElement.description} rows="2"></textarea>
      </div>
      
      <div class="form-row">
        <div class="form-group">
          <label>Quantity</label>
          <input type="number" bind:value={editedElement.quantity} min="1" />
        </div>
        
        <div class="form-group">
          <label>Cost</label>
          <input type="number" bind:value={editedElement.estimated_cost} min="0" step="0.01" />
        </div>
      </div>
      
      <div class="form-group">
        <label>Status</label>
        <select bind:value={editedElement.status}>
          {#each statusOptions as status}
            <option value={status}>{status}</option>
          {/each}
        </select>
      </div>
      
      <div class="form-group">
        <label>Notes</label>
        <textarea bind:value={editedElement.notes} rows="2"></textarea>
      </div>
      
      <div class="form-group">
        <label>Special Instructions</label>
        <textarea bind:value={editedElement.special_instructions} rows="2"></textarea>
      </div>
      
      <div class="form-actions">
        <button class="btn btn-primary" on:click={saveEdit}>Save</button>
        <button class="btn btn-secondary" on:click={cancelEdit}>Cancel</button>
      </div>
    </div>
  {:else}
    <div class="element-details">
      <p class="element-description">{element.description}</p>
      
      <div class="element-stats">
        <span class="stat">
          <span class="stat-label">Quantity:</span>
          <span class="stat-value">{element.quantity}</span>
        </span>
        <span class="stat">
          <span class="stat-label">Cost:</span>
          <span class="stat-value">{formatCost(element.estimated_cost)}</span>
        </span>
        <span class="stat">
          <span class="stat-label">Confidence:</span>
          <span class="stat-value">{(element.confidence * 100).toFixed(0)}%</span>
        </span>
      </div>
      
      {#if element.notes}
        <div class="element-notes">
          <strong>Notes:</strong> {element.notes}
        </div>
      {/if}
      
      {#if element.special_instructions}
        <div class="element-instructions">
          <strong>Instructions:</strong> {element.special_instructions}
        </div>
      {/if}
      
      <div class="element-context">
        <strong>Context:</strong>
        <p class="context-text">{element.context_text}</p>
      </div>
    </div>
  {/if}
</div>

<style>
  .element-card {
    border: 1px solid var(--color-border);
    border-radius: 0.5rem;
    padding: 1rem;
    background: var(--color-surface);
    transition: all 0.2s;
  }

  .element-card:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .element-card.editing {
    border-color: var(--color-primary);
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
  }

  .element-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
  }

  .element-info {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .element-type {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--color-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .element-name {
    font-size: 1rem;
    font-weight: 600;
    color: var(--color-text);
  }

  .element-status {
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .element-actions {
    display: flex;
    gap: 0.5rem;
  }

  .btn {
    padding: 0.25rem 0.5rem;
    border: 1px solid var(--color-border);
    border-radius: 0.25rem;
    background: var(--color-surface);
    color: var(--color-text);
    cursor: pointer;
    font-size: 0.75rem;
    transition: all 0.2s;
  }

  .btn:hover {
    background: var(--color-surface-hover);
  }

  .btn-sm {
    padding: 0.125rem 0.25rem;
    font-size: 0.625rem;
  }

  .btn-primary {
    background: var(--color-primary);
    color: white;
    border-color: var(--color-primary);
  }

  .btn-secondary {
    background: var(--color-secondary);
    color: white;
    border-color: var(--color-secondary);
  }

  .edit-form {
    margin-top: 1rem;
  }

  .form-group {
    margin-bottom: 0.75rem;
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
  }

  label {
    display: block;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--color-text);
    margin-bottom: 0.25rem;
  }

  input, select, textarea {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid var(--color-border);
    border-radius: 0.25rem;
    font-size: 0.875rem;
    background: var(--color-background);
    color: var(--color-text);
  }

  textarea {
    resize: vertical;
    min-height: 60px;
  }

  .form-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
    margin-top: 1rem;
  }

  .element-details {
    font-size: 0.875rem;
  }

  .element-description {
    margin-bottom: 0.75rem;
    color: var(--color-text-secondary);
    line-height: 1.5;
  }

  .element-stats {
    display: flex;
    gap: 1rem;
    margin-bottom: 0.75rem;
  }

  .stat {
    display: flex;
    flex-direction: column;
  }

  .stat-label {
    font-size: 0.75rem;
    color: var(--color-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .stat-value {
    font-weight: 600;
    color: var(--color-text);
  }

  .element-notes,
  .element-instructions,
  .element-context {
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
    line-height: 1.5;
  }

  .element-context strong,
  .element-notes strong,
  .element-instructions strong {
    color: var(--color-text);
  }

  .context-text {
    font-style: italic;
    color: var(--color-text-secondary);
    margin-top: 0.25rem;
  }
</style>