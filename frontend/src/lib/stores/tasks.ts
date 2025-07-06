/**
 * Task management store for tracking progress
 */

import { writable } from 'svelte/store';
import type { Task } from '$lib/types';
import { api } from '$lib/api/client';

function createTaskStore() {
  const { subscribe, update } = writable<Task[]>([]);

  return {
    subscribe,

    add(task: Omit<Task, 'id' | 'createdAt' | 'status'>) {
      const newTask: Task = {
        ...task,
        id: crypto.randomUUID(),
        createdAt: Date.now(),
        status: 'pending',
        progress: 0
      };

      update((tasks) => [...tasks, newTask]);
      return newTask.id;
    },

    updateProgress(taskId: string, progress: Partial<Task>) {
      update((tasks) => tasks.map((t) => (t.id === taskId ? { ...t, ...progress } : t)));
    },

    async cancel(taskId: string) {
      try {
        await api.post(`/tasks/${taskId}/cancel`);
        this.updateProgress(taskId, {
          status: 'cancelled',
          completedAt: Date.now()
        });
      } catch (error) {
        console.error('Failed to cancel task:', error);
      }
    },

    clearCompleted() {
      update((tasks) =>
        tasks.filter(
          (t) =>
            t.status === 'running' ||
            t.status === 'pending' ||
            (t.completedAt && t.completedAt > Date.now() - 5000)
        )
      );
    }
  };
}

export const taskStore = createTaskStore();
