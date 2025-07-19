<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { X } from 'lucide-svelte';

  export let open = false;
  export let title = '';
  export let size: 'small' | 'medium' | 'large' = 'medium';
  export let showClose = true;

  const dispatch = createEventDispatcher();

  function handleClose() {
    dispatch('close');
  }

  function handleBackdropClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      handleClose();
    }
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      handleClose();
    }
  }

  import { onMount } from 'svelte';
  import { browser } from '$app/environment';

  onMount(() => {
    const handleKeydown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        handleClose();
      }
    };

    if (open) {
      document.addEventListener('keydown', handleKeydown);
    }

    return () => {
      document.removeEventListener('keydown', handleKeydown);
    };
  });
</script>

{#if open}
  <div class="dialog-backdrop" on:click={handleBackdropClick} role="dialog" aria-modal="true">
    <div class="dialog {size}" role="document">
      {#if title || showClose}
        <div class="dialog-header">
          {#if title}
            <h3 class="dialog-title">{title}</h3>
          {/if}
          {#if showClose}
            <button class="dialog-close" on:click={handleClose} type="button" aria-label="Close dialog">
              <X size={20} />
            </button>
          {/if}
        </div>
      {/if}
      <div class="dialog-content">
        <slot />
      </div>
    </div>
  </div>
{/if}

<style>
  .dialog-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    animation: fadeIn 0.2s ease-out;
  }

  .dialog {
    background: var(--bg-primary, #fff);
    border-radius: 8px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
    max-height: 90vh;
    overflow: hidden;
    animation: slideIn 0.2s ease-out;
  }

  .dialog.small {
    width: 400px;
    max-width: 90vw;
  }

  .dialog.medium {
    width: 600px;
    max-width: 90vw;
  }

  .dialog.large {
    width: 800px;
    max-width: 90vw;
  }

  .dialog-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--border-color, #e5e7eb);
  }

  .dialog-title {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 600;
  }

  .dialog-close {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: transparent;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    color: var(--text-secondary, #6b7280);
    transition: all 0.2s;
  }

  .dialog-close:hover {
    background: var(--surface-hover, #f3f4f6);
    color: var(--text-primary, #111827);
  }

  .dialog-content {
    padding: 1.5rem;
    overflow-y: auto;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  @keyframes slideIn {
    from {
      transform: translateY(-20px);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }
</style>