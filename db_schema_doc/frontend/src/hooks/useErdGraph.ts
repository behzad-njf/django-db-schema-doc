import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
} from "@xyflow/react";
import { applyNodeFilter } from "../lib/applyNodeFilter";
import { parseGraphPayload } from "../lib/parseGraph";
import {
  clearGraphSession,
  loadGraphSession,
  saveGraphSession,
} from "../lib/graphStorage";
import type { GraphPayload, TableDetail, TableNodeData } from "../types/graph";

export function useErdGraph() {
  const [meta, setMeta] = useState("");
  const [sourceLabel, setSourceLabel] = useState("");
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [focusId, setFocusId] = useState<string | null>(null);
  const [detailTableId, setDetailTableId] = useState<string | null>(null);

  const [nodes, setNodes, onNodesChange] = useNodesState<Node<TableNodeData>>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [allNodes, setAllNodes] = useState<Node<TableNodeData>[]>([]);
  const [allEdges, setAllEdges] = useState<Edge[]>([]);
  const nodesRef = useRef(nodes);
  nodesRef.current = nodes;
  const allNodesRef = useRef(allNodes);
  allNodesRef.current = allNodes;
  const sourceLabelRef = useRef(sourceLabel);
  sourceLabelRef.current = sourceLabel;
  const focusIdRef = useRef(focusId);
  focusIdRef.current = focusId;
  const detailTableIdRef = useRef(detailTableId);
  detailTableIdRef.current = detailTableId;

  const dragMovedRef = useRef(false);
  const dragStartPosRef = useRef<{ x: number; y: number } | null>(null);

  const DRAG_CLICK_THRESHOLD_PX = 4;

  const hasGraph = allNodes.length > 0;

  const resetGraph = useCallback(() => {
    setAllNodes([]);
    setAllEdges([]);
    setNodes([]);
    setEdges([]);
    setFocusId(null);
    setDetailTableId(null);
    setQuery("");
    setSourceLabel("");
    setMeta("");
    setError("");
    clearGraphSession();
  }, [setNodes, setEdges]);

  const applyGraph = useCallback(
    (data: GraphPayload, label: string, persist = true) => {
      const { nodes: loadedNodes, edges: loadedEdges, meta: graphMeta } =
        parseGraphPayload(data);

      if (!loadedNodes.length) {
        throw new Error("graph.json has no nodes");
      }

      setAllNodes(loadedNodes);
      setAllEdges(loadedEdges);
      setNodes(loadedNodes);
      setEdges(loadedEdges);
      setFocusId(null);
      setDetailTableId(null);
      setQuery("");
      setSourceLabel(label);
      setMeta(graphMeta);
      setError("");

      if (persist) {
        saveGraphSession(data, label);
      }
    },
    [setNodes, setEdges]
  );

  const restoreSession = useCallback((): boolean => {
    const session = loadGraphSession();
    if (!session) return false;
    try {
      applyGraph(session.payload, session.sourceLabel, false);
      return true;
    } catch {
      clearGraphSession();
      return false;
    }
  }, [applyGraph]);

  const loadFromFile = useCallback(
    (file: File, onSuccess?: () => void) => {
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const text = reader.result;
          if (typeof text !== "string") {
            throw new Error("Could not read file");
          }
          const data = JSON.parse(text) as GraphPayload;
          applyGraph(data, file.name);
          onSuccess?.();
        } catch (err) {
          setError(err instanceof Error ? err.message : "Invalid graph.json");
        }
      };
      reader.onerror = () => setError("Failed to read file");
      reader.readAsText(file);
    },
    [applyGraph]
  );

  const runFilter = useCallback(() => {
    if (!hasGraph) return;
    const { nodes: nextNodes, edges: nextEdges } = applyNodeFilter({
      allNodes,
      allEdges,
      currentNodes: nodesRef.current,
      query,
      focusId,
    });
    setNodes(nextNodes);
    setEdges(nextEdges);
  }, [allNodes, allEdges, query, focusId, hasGraph, setNodes, setEdges]);

  useEffect(() => {
    runFilter();
  }, [runFilter]);

  const onNodeDragStart = useCallback(
    (_event: React.MouseEvent, node: Node<TableNodeData>) => {
      dragMovedRef.current = false;
      dragStartPosRef.current = { x: node.position.x, y: node.position.y };
    },
    []
  );

  const onNodeDragStop = useCallback(
    (_event: React.MouseEvent, node: Node<TableNodeData>) => {
      const start = dragStartPosRef.current;
      if (start) {
        const dx = Math.abs(node.position.x - start.x);
        const dy = Math.abs(node.position.y - start.y);
        if (dx > DRAG_CLICK_THRESHOLD_PX || dy > DRAG_CLICK_THRESHOLD_PX) {
          dragMovedRef.current = true;
        }
      }
      dragStartPosRef.current = null;

      setAllNodes((prev) => {
        const next = prev.map((n) =>
          n.id === node.id ? { ...n, position: { ...node.position } } : n
        );
        const session = loadGraphSession();
        if (session) {
          saveGraphSession(
            { ...session.payload, nodes: next },
            sourceLabelRef.current
          );
        }
        return next;
      });
    },
    []
  );

  const onNodeDoubleClick = useCallback(
    (_event: React.MouseEvent, node: Node<TableNodeData>) => {
      if (dragMovedRef.current) {
        dragMovedRef.current = false;
        return;
      }
      setDetailTableId(node.id);
      setFocusId(node.id);
    },
    []
  );

  const onPaneClick = useCallback(() => {
    setFocusId(null);
  }, []);

  const clearFocus = useCallback(() => {
    setFocusId(null);
  }, []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      if (focusIdRef.current) {
        setFocusId(null);
      } else if (detailTableIdRef.current) {
        setDetailTableId(null);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const closeDetailPanel = useCallback(() => {
    setDetailTableId(null);
  }, []);

  const selectedTable = useMemo((): TableDetail | null => {
    if (!detailTableId) return null;
    const node = allNodes.find((n) => n.id === detailTableId);
    return node?.data?.table ?? null;
  }, [detailTableId, allNodes]);

  const selectedSummary = useMemo(() => {
    if (!detailTableId) return null;
    return allNodes.find((n) => n.id === detailTableId)?.data ?? null;
  }, [detailTableId, allNodes]);

  const visibleCount = useMemo(
    () => nodes.filter((n) => !n.hidden).length,
    [nodes]
  );

  return {
    meta,
    sourceLabel,
    error,
    setError,
    query,
    setQuery,
    hasGraph,
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onNodeDragStart,
    onNodeDragStop,
    onNodeDoubleClick,
    onPaneClick,
    loadFromFile,
    restoreSession,
    resetGraph,
    clearFocus,
    closeDetailPanel,
    detailTableId,
    selectedTable,
    selectedSummary,
    visibleCount,
    tableCount: allNodes.length,
  };
}
