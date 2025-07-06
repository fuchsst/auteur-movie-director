/**
 * Notification management store
 */

import { writable } from 'svelte/store';
import type { Notification } from '$lib/types';

function createNotificationStore() {
  const { subscribe, update } = writable<Notification[]>([]);

  return {
    subscribe,

    add(notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) {
      const newNotification: Notification = {
        ...notification,
        id: crypto.randomUUID(),
        timestamp: Date.now(),
        read: false
      };

      update((notifications) => {
        // Limit to 50 most recent
        const updated = [newNotification, ...notifications];
        return updated.slice(0, 50);
      });

      // Auto-dismiss low priority after 5 seconds
      if (notification.priority === 'low') {
        setTimeout(() => {
          this.dismiss(newNotification.id);
        }, 5000);
      }
    },

    dismiss(id: string) {
      update((notifications) => notifications.filter((n) => n.id !== id));
    },

    markRead(id: string) {
      update((notifications) => notifications.map((n) => (n.id === id ? { ...n, read: true } : n)));
    },

    markAllRead() {
      update((notifications) => notifications.map((n) => ({ ...n, read: true })));
    },

    clearRead() {
      update((notifications) => notifications.filter((n) => !n.read));
    }
  };
}

export const notificationStore = createNotificationStore();
