import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, fireEvent, waitFor } from '@testing-library/svelte';
import GitTimeline from './GitTimeline.svelte';
import { gitApi } from '$lib/api/git';
import type { EnhancedGitCommit } from '$lib/api/git';

// Mock the git API
vi.mock('$lib/api/git', () => ({
  gitApi: {
    getEnhancedHistory: vi.fn()
  }
}));

describe('GitTimeline', () => {
  const mockCommits: EnhancedGitCommit[] = [
    {
      hash: 'abc123def456',
      shortHash: 'abc123d',
      message: 'feat: Add new feature',
      author: 'John Doe',
      email: 'john@example.com',
      date: new Date().toISOString(),
      stats: {
        additions: 50,
        deletions: 10,
        files: 3
      },
      files: [
        {
          path: 'src/app.js',
          changeType: 'M',
          additions: 30,
          deletions: 5
        },
        {
          path: 'styles.css',
          changeType: 'A',
          additions: 20,
          deletions: 0
        }
      ],
      parentHashes: ['parent123']
    },
    {
      hash: 'def789ghi012',
      shortHash: 'def789g',
      message: 'fix: Resolve bug',
      author: 'Jane Smith',
      email: 'jane@example.com',
      date: new Date(Date.now() - 86400000).toISOString(), // Yesterday
      stats: {
        additions: 10,
        deletions: 20,
        files: 1
      },
      files: [
        {
          path: 'src/utils.js',
          changeType: 'M',
          additions: 10,
          deletions: 20
        }
      ],
      parentHashes: ['abc123def456']
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    (gitApi.getEnhancedHistory as any).mockResolvedValue(mockCommits);
  });

  it('renders timeline with commits', async () => {
    const { getByText, container } = render(GitTimeline, {
      props: { projectId: 'test-project' }
    });

    await waitFor(() => {
      expect(getByText('feat: Add new feature')).toBeInTheDocument();
      expect(getByText('fix: Resolve bug')).toBeInTheDocument();
    });

    expect(gitApi.getEnhancedHistory).toHaveBeenCalledWith('test-project', 100);
  });

  it('groups commits by time scale', async () => {
    const { container } = render(GitTimeline, {
      props: { projectId: 'test-project' }
    });

    await waitFor(() => {
      const groupLabels = container.querySelectorAll('.group-label');
      expect(groupLabels.length).toBeGreaterThan(0);
    });
  });

  it('filters commits by search query', async () => {
    const { getByPlaceholderText, getByText, queryByText } = render(GitTimeline, {
      props: { projectId: 'test-project' }
    });

    await waitFor(() => {
      expect(getByText('feat: Add new feature')).toBeInTheDocument();
    });

    const searchInput = getByPlaceholderText('Search commits...');
    await fireEvent.input(searchInput, { target: { value: 'bug' } });

    await waitFor(() => {
      expect(queryByText('feat: Add new feature')).not.toBeInTheDocument();
      expect(getByText('fix: Resolve bug')).toBeInTheDocument();
    });
  });

  it('shows commit details when node is clicked', async () => {
    const { getByText, container } = render(GitTimeline, {
      props: { projectId: 'test-project' }
    });

    await waitFor(() => {
      expect(getByText('feat: Add new feature')).toBeInTheDocument();
    });

    const commitNode = container.querySelector('[data-commit-hash="abc123def456"]');
    if (commitNode) {
      await fireEvent.click(commitNode);
    }

    await waitFor(() => {
      expect(container.querySelector('.details-panel')).toBeInTheDocument();
    });
  });

  it('supports keyboard navigation', async () => {
    const { container } = render(GitTimeline, {
      props: { projectId: 'test-project' }
    });

    await waitFor(() => {
      const nodes = container.querySelectorAll('.commit-node');
      expect(nodes.length).toBe(2);
    });

    // Test arrow key navigation
    await fireEvent.keyDown(window, { key: 'ArrowDown' });

    const selectedNode = container.querySelector('.commit-node.selected');
    expect(selectedNode).toBeInTheDocument();
  });

  it('filters by file type', async () => {
    const { getByText, container } = render(GitTimeline, {
      props: { projectId: 'test-project' }
    });

    await waitFor(() => {
      expect(getByText('feat: Add new feature')).toBeInTheDocument();
    });

    // Open filters
    const filterButton = container.querySelector('.filter-button');
    if (filterButton) {
      await fireEvent.click(filterButton);
    }

    // Select file type
    const fileTypeSelect = container.querySelector('#file-type-filter') as HTMLSelectElement;
    if (fileTypeSelect) {
      await fireEvent.change(fileTypeSelect, { target: { value: 'css' } });
    }

    await waitFor(() => {
      expect(getByText('feat: Add new feature')).toBeInTheDocument();
      expect(container.querySelectorAll('.commit-node').length).toBe(1);
    });
  });

  it('refreshes commit history', async () => {
    const { container } = render(GitTimeline, {
      props: { projectId: 'test-project' }
    });

    await waitFor(() => {
      expect(gitApi.getEnhancedHistory).toHaveBeenCalledTimes(1);
    });

    const refreshButton = container.querySelector('.refresh-button');
    if (refreshButton) {
      await fireEvent.click(refreshButton);
    }

    await waitFor(() => {
      expect(gitApi.getEnhancedHistory).toHaveBeenCalledTimes(2);
    });
  });

  it('loads more commits when scrolled to bottom', async () => {
    // Mock returning 100 commits initially
    const manyCommits = Array(100)
      .fill(null)
      .map((_, i) => ({
        ...mockCommits[0],
        hash: `commit${i}`,
        shortHash: `commit${i}`.substring(0, 7)
      }));

    (gitApi.getEnhancedHistory as any).mockResolvedValue(manyCommits);

    const { getByText } = render(GitTimeline, {
      props: { projectId: 'test-project' }
    });

    await waitFor(() => {
      expect(getByText('Load More')).toBeInTheDocument();
    });

    const loadMoreButton = getByText('Load More');
    await fireEvent.click(loadMoreButton);

    expect(gitApi.getEnhancedHistory).toHaveBeenCalledWith('test-project', 200);
  });

  it('handles empty commit history', async () => {
    (gitApi.getEnhancedHistory as any).mockResolvedValue([]);

    const { getByText } = render(GitTimeline, {
      props: { projectId: 'test-project' }
    });

    await waitFor(() => {
      expect(getByText('No commits yet')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    (gitApi.getEnhancedHistory as any).mockRejectedValue(new Error('Network error'));

    const { getByText } = render(GitTimeline, {
      props: { projectId: 'test-project' }
    });

    await waitFor(() => {
      expect(getByText('Failed to load commit history')).toBeInTheDocument();
      expect(getByText('Retry')).toBeInTheDocument();
    });
  });
});
