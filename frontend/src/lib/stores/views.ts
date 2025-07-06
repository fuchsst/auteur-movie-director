/**
 * View state management for tab system
 */

import { writable } from 'svelte/store';
import { browser } from '$app/environment';

interface ViewState {
  activeTab: string;
  tabHistory: string[];
  viewStates: Record<string, any>;
}

function createViewStore() {
  const defaultState: ViewState = {
    activeTab: 'canvas',
    tabHistory: ['canvas'],
    viewStates: {}
  };

  // Load from localStorage
  const stored = browser ? localStorage.getItem('viewState') : null;
  const initial = stored ? { ...defaultState, ...JSON.parse(stored) } : defaultState;

  const { subscribe, update } = writable<ViewState>(initial);

  return {
    subscribe,

    setActiveTab(tabId: string) {
      update((state) => {
        const newState = {
          ...state,
          activeTab: tabId,
          tabHistory: [...state.tabHistory.slice(-9), tabId]
        };

        if (browser) {
          localStorage.setItem('viewState', JSON.stringify(newState));
        }

        return newState;
      });
    },

    saveViewState(tabId: string, state: any) {
      update((s) => ({
        ...s,
        viewStates: {
          ...s.viewStates,
          [tabId]: state
        }
      }));
    },

    getViewState(tabId: string) {
      let state: any;
      const unsubscribe = subscribe((s) => {
        state = s.viewStates[tabId];
      });
      unsubscribe();
      return state;
    }
  };
}

export const viewStore = createViewStore();
