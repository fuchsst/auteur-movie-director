// Canvas Web Worker for performance optimization

class CanvasWorker {
  constructor() {
    this.addEventListener('message', this.handleMessage.bind(this));
  }

  handleMessage(event) {
    const { type, data, id } = event.data;

    switch (type) {
      case 'optimizeLayout':
        this.optimizeLayout(data.nodes, data.options, id);
        break;
      case 'calculateBounds':
        this.calculateBounds(data.nodes, id);
        break;
      case 'findPath':
        this.findPath(data.nodes, data.edges, data.start, data.end, id);
        break;
      case 'validateStructure':
        this.validateStructure(data.nodes, data.edges, id);
        break;
      case 'optimizeEdges':
        this.optimizeEdges(data.edges, id);
        break;
      default:
        this.postMessage({ type: 'error', message: 'Unknown task type', id });
    }
  }

  optimizeLayout(nodes, options = {}, id) {
    const startTime = performance.now();
    
    try {
      const optimized = this.performLayoutOptimization(nodes, options);
      
      const endTime = performance.now();
      this.postMessage({
        type: 'layoutOptimized',
        result: optimized,
        duration: endTime - startTime,
        id
      });
    } catch (error) {
      this.postMessage({
        type: 'error',
        message: error.message,
        id
      });
    }
  }

  performLayoutOptimization(nodes, options) {
    const { algorithm = 'force-directed', iterations = 100 } = options;
    
    switch (algorithm) {
      case 'force-directed':
        return this.forceDirectedLayout(nodes, iterations);
      case 'hierarchical':
        return this.hierarchicalLayout(nodes);
      case 'grid':
        return this.gridLayout(nodes);
      case 'circular':
        return this.circularLayout(nodes);
      default:
        return this.forceDirectedLayout(nodes, iterations);
    }
  }

  forceDirectedLayout(nodes, iterations) {
    const positions = nodes.map(node => ({
      id: node.id,
      x: node.position.x,
      y: node.position.y,
      vx: 0,
      vy: 0
    }));

    const repulsionStrength = 1000;
    const attractionStrength = 0.1;
    const damping = 0.9;

    for (let i = 0; i < iterations; i++) {
      // Apply repulsion forces
      for (let j = 0; j < positions.length; j++) {
        for (let k = j + 1; k < positions.length; k++) {
          const dx = positions[j].x - positions[k].x;
          const dy = positions[j].y - positions[k].y;
          const distance = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = repulsionStrength / (distance * distance);
          
          positions[j].vx += (dx / distance) * force;
          positions[j].vy += (dy / distance) * force;
          positions[k].vx -= (dx / distance) * force;
          positions[k].vy -= (dy / distance) * force;
        }
      }

      // Apply attraction forces (for connected nodes)
      // This would need edge data to be implemented properly

      // Update positions
      positions.forEach(pos => {
        pos.vx *= damping;
        pos.vy *= damping;
        pos.x += pos.vx;
        pos.y += pos.vy;
      });
    }

    return positions.map(pos => ({
      id: pos.id,
      position: { x: pos.x, y: pos.y }
    }));
  }

  hierarchicalLayout(nodes) {
    const levels = this.groupNodesByLevel(nodes);
    const positions = [];
    const levelHeight = 150;
    const nodeSpacing = 200;

    Object.keys(levels).forEach((level, levelIndex) => {
      const levelNodes = levels[level];
      const levelWidth = (levelNodes.length - 1) * nodeSpacing;
      
      levelNodes.forEach((node, nodeIndex) => {
        positions.push({
          id: node.id,
          position: {
            x: nodeIndex * nodeSpacing - levelWidth / 2,
            y: levelIndex * levelHeight
          }
        });
      });
    });

    return positions;
  }

  groupNodesByLevel(nodes) {
    // Simple level grouping based on node type
    const levels = {};
    
    nodes.forEach(node => {
      const level = this.getNodeLevel(node);
      if (!levels[level]) levels[level] = [];
      levels[level].push(node);
    });

    return levels;
  }

  getNodeLevel(node) {
    const type = node.type || node.data?.type;
    
    const levelMap = {
      'act': 0,
      'scene': 1,
      'shot': 2,
      'character-asset': 3,
      'style-asset': 3
    };

    return levelMap[type] || 0;
  }

  gridLayout(nodes) {
    const cols = Math.ceil(Math.sqrt(nodes.length));
    const spacing = 200;
    
    return nodes.map((node, index) => ({
      id: node.id,
      position: {
        x: (index % cols) * spacing,
        y: Math.floor(index / cols) * spacing
      }
    }));
  }

  circularLayout(nodes) {
    const radius = 300;
    const center = { x: 0, y: 0 };
    const angleStep = (2 * Math.PI) / nodes.length;
    
    return nodes.map((node, index) => ({
      id: node.id,
      position: {
        x: center.x + radius * Math.cos(index * angleStep),
        y: center.y + radius * Math.sin(index * angleStep)
      }
    }));
  }

  calculateBounds(nodes, id) {
    if (!nodes || nodes.length === 0) {
      this.postMessage({
        type: 'boundsCalculated',
        result: { minX: 0, maxX: 100, minY: 0, maxY: 100, width: 100, height: 100 },
        id
      });
      return;
    }

    const positions = nodes.map(node => node.position);
    const minX = Math.min(...positions.map(p => p.x));
    const maxX = Math.max(...positions.map(p => p.x));
    const minY = Math.min(...positions.map(p => p.y));
    const maxY = Math.max(...positions.map(p => p.y));

    this.postMessage({
      type: 'boundsCalculated',
      result: {
        minX,
        maxX,
        minY,
        maxY,
        width: maxX - minX,
        height: maxY - minY
      },
      id
    });
  }

  findPath(nodes, edges, start, end, id) {
    // Simple A* pathfinding for canvas connections
    const startTime = performance.now();
    
    try {
      const graph = this.buildGraph(nodes, edges);
      const path = this.aStar(graph, start, end);
      
      const endTime = performance.now();
      this.postMessage({
        type: 'pathFound',
        result: path,
        duration: endTime - startTime,
        id
      });
    } catch (error) {
      this.postMessage({
        type: 'error',
        message: error.message,
        id
      });
    }
  }

  buildGraph(nodes, edges) {
    const graph = {};
    
    nodes.forEach(node => {
      graph[node.id] = { neighbors: [], position: node.position };
    });
    
    edges.forEach(edge => {
      if (graph[edge.source] && graph[edge.target]) {
        graph[edge.source].neighbors.push(edge.target);
        graph[edge.target].neighbors.push(edge.source);
      }
    });
    
    return graph;
  }

  aStar(graph, start, end) {
    const openSet = new Set([start]);
    const cameFrom = {};
    const gScore = { [start]: 0 };
    const fScore = { [start]: this.heuristic(graph, start, end) };

    while (openSet.size > 0) {
      let current = null;
      let lowestFScore = Infinity;

      for (const node of openSet) {
        if (fScore[node] < lowestFScore) {
          lowestFScore = fScore[node];
          current = node;
        }
      }

      if (current === end) {
        return this.reconstructPath(cameFrom, current);
      }

      openSet.delete(current);

      for (const neighbor of graph[current].neighbors) {
        const tentativeGScore = gScore[current] + 1;
        
        if (!gScore[neighbor] || tentativeGScore < gScore[neighbor]) {
          cameFrom[neighbor] = current;
          gScore[neighbor] = tentativeGScore;
          fScore[neighbor] = gScore[neighbor] + this.heuristic(graph, neighbor, end);
          openSet.add(neighbor);
        }
      }
    }

    return null; // No path found
  }

  heuristic(graph, a, b) {
    const posA = graph[a].position;
    const posB = graph[b].position;
    
    return Math.sqrt(
      Math.pow(posA.x - posB.x, 2) + Math.pow(posA.y - posB.y, 2)
    ) / 200; // Normalize distance
  }

  reconstructPath(cameFrom, current) {
    const path = [current];
    
    while (cameFrom[current]) {
      current = cameFrom[current];
      path.unshift(current);
    }
    
    return path;
  }

  validateStructure(nodes, edges, id) {
    const startTime = performance.now();
    
    try {
      const validation = {
        isValid: true,
        errors: [],
        warnings: []
      };

      // Check for orphaned nodes
      const connectedNodes = new Set();
      edges.forEach(edge => {
        connectedNodes.add(edge.source);
        connectedNodes.add(edge.target);
      });

      nodes.forEach(node => {
        if (!connectedNodes.has(node.id) && edges.length > 0) {
          validation.warnings.push(`Node ${node.id} is not connected`);
        }
      });

      // Check for circular dependencies
      const cycles = this.detectCycles(nodes, edges);
      if (cycles.length > 0) {
        validation.errors.push(`Circular dependencies detected: ${cycles.length}`);
      }

      const endTime = performance.now();
      this.postMessage({
        type: 'structureValidated',
        result: validation,
        duration: endTime - startTime,
        id
      });
    } catch (error) {
      this.postMessage({
        type: 'error',
        message: error.message,
        id
      });
    }
  }

  detectCycles(nodes, edges) {
    const graph = this.buildGraph(nodes, edges);
    const visited = new Set();
    const recStack = new Set();
    const cycles = [];

    const dfs = (node, path = []) => {
      if (recStack.has(node)) {
        const cycleStart = path.indexOf(node);
        if (cycleStart !== -1) {
          cycles.push(path.slice(cycleStart));
        }
        return;
      }

      if (visited.has(node)) return;

      visited.add(node);
      recStack.add(node);
      path.push(node);

      for (const neighbor of graph[node]?.neighbors || []) {
        dfs(neighbor, [...path]);
      }

      recStack.delete(node);
    };

    Object.keys(graph).forEach(node => {
      if (!visited.has(node)) {
        dfs(node);
      }
    });

    return cycles;
  }

  optimizeEdges(edges, id) {
    const startTime = performance.now();
    
    try {
      // Remove duplicate edges
      const uniqueEdges = edges.filter((edge, index, self) =
        index === self.findIndex(e =
          e.source === edge.source && e.target === edge.target
        )
      );

      // Optimize edge routing
      const optimizedEdges = uniqueEdges.map(edge => ({
        ...edge,
        type: this.optimizeEdgeType(edge)
      }));

      const endTime = performance.now();
      this.postMessage({
        type: 'edgesOptimized',
        result: optimizedEdges,
        duration: endTime - startTime,
        id
      });
    } catch (error) {
      this.postMessage({
        type: 'error',
        message: error.message,
        id
      });
    }
  }

  optimizeEdgeType(edge) {
    // Simple optimization based on edge length
    const source = edge.source;
    const target = edge.target;
    
    // In a real implementation, we'd calculate actual distance
    return 'smoothstep';
  }
}

// Initialize worker
const worker = new CanvasWorker();

// Export for use
export default CanvasWorker;