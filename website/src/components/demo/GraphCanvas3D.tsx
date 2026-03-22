"use client";

import { useRef, useState, useEffect, useCallback, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Html, Line } from "@react-three/drei";
import * as THREE from "three";
import {
  INITIAL_NODES,
  EDGES,
  STATUS_HEX,
  STATUS_EMISSIVE,
  type PipelineNodeData,
  type NodeStatus,
} from "./pipelineData";

// ---------------------------------------------------------------------------
// 3D positions: map 2D percentage coords to world-space
// ---------------------------------------------------------------------------
function toWorld(node: PipelineNodeData): [number, number, number] {
  const x = ((node.x - 50) / 50) * 6;
  const y = ((50 - node.y) / 50) * 2.5;
  return [x, y, node.z];
}

// ---------------------------------------------------------------------------
// Single 3D Node
// ---------------------------------------------------------------------------
interface NodeMeshProps {
  node: PipelineNodeData;
  onClick: (node: PipelineNodeData) => void;
}

function NodeMesh({ node, onClick }: NodeMeshProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);
  const pos = useMemo(() => toWorld(node), [node]);

  const baseScale = 0.22;
  const targetScale = hovered ? baseScale * 1.3 : baseScale;

  useFrame(() => {
    if (!meshRef.current) return;
    const s = meshRef.current.scale.x;
    const next = THREE.MathUtils.lerp(s, targetScale, 0.12);
    meshRef.current.scale.setScalar(next);
  });

  const emissiveColor = STATUS_EMISSIVE[node.status];
  const emissiveIntensity = node.status === "running" ? 1.8 : node.status === "success" ? 0.8 : 0.2;

  return (
    <group position={pos}>
      {node.status === "running" && <PointGlow color="#4f46e5" />}

      <mesh
        ref={meshRef}
        scale={baseScale}
        onClick={(e) => { e.stopPropagation(); onClick(node); }}
        onPointerOver={(e) => { e.stopPropagation(); setHovered(true); document.body.style.cursor = "pointer"; }}
        onPointerOut={() => { setHovered(false); document.body.style.cursor = "auto"; }}
      >
        <sphereGeometry args={[1, 24, 24]} />
        <meshStandardMaterial
          color={STATUS_HEX[node.status]}
          emissive={emissiveColor}
          emissiveIntensity={emissiveIntensity}
          roughness={0.35}
          metalness={0.6}
          toneMapped={false}
        />
      </mesh>

      <Html
        center
        distanceFactor={8}
        style={{ pointerEvents: "none", whiteSpace: "nowrap" }}
        position={[0, -0.38, 0]}
      >
        <div className="select-none text-center">
          <div className="text-[11px] font-semibold" style={{ color: STATUS_HEX[node.status] }}>
            {node.label}
          </div>
          <div className="text-[9px] text-zinc-600">{node.duration}</div>
        </div>
      </Html>
    </group>
  );
}

// ---------------------------------------------------------------------------
// Glow point light for running nodes
// ---------------------------------------------------------------------------
function PointGlow({ color }: { color: string }) {
  const ref = useRef<THREE.PointLight>(null);
  useFrame(({ clock }) => {
    if (!ref.current) return;
    ref.current.intensity = 1.5 + Math.sin(clock.getElapsedTime() * 3) * 0.8;
  });
  return <pointLight ref={ref} color={color} intensity={1.5} distance={3} decay={2} />;
}

// ---------------------------------------------------------------------------
// Edges between nodes
// ---------------------------------------------------------------------------
interface EdgeLineProps {
  fromNode: PipelineNodeData;
  toNode: PipelineNodeData;
}

function EdgeLine({ fromNode, toNode }: EdgeLineProps) {
  const from = toWorld(fromNode);
  const to = toWorld(toNode);
  const isActive = fromNode.status === "success" && (toNode.status === "running" || toNode.status === "success");

  return (
    <Line
      points={[from, to]}
      color={isActive ? "#6366f1" : "#3f3f46"}
      lineWidth={isActive ? 2 : 1}
      opacity={isActive ? 0.7 : 0.3}
      transparent
      dashed={!isActive}
      dashSize={0.15}
      gapSize={0.1}
    />
  );
}

// ---------------------------------------------------------------------------
// Particle that travels along an edge
// ---------------------------------------------------------------------------
interface EdgeParticleProps {
  fromNode: PipelineNodeData;
  toNode: PipelineNodeData;
  speed?: number;
}

function EdgeParticle({ fromNode, toNode, speed = 1.2 }: EdgeParticleProps) {
  const ref = useRef<THREE.Mesh>(null);
  const from = useMemo(() => new THREE.Vector3(...toWorld(fromNode)), [fromNode]);
  const to = useMemo(() => new THREE.Vector3(...toWorld(toNode)), [toNode]);

  const isActive = fromNode.status === "success" && (toNode.status === "running" || toNode.status === "success");

  useFrame(({ clock }) => {
    if (!ref.current || !isActive) {
      if (ref.current) ref.current.visible = false;
      return;
    }
    ref.current.visible = true;
    const t = (clock.getElapsedTime() * speed) % 1;
    ref.current.position.lerpVectors(from, to, t);
  });

  return (
    <mesh ref={ref} visible={false}>
      <sphereGeometry args={[0.04, 8, 8]} />
      <meshBasicMaterial color="#818cf8" toneMapped={false} />
    </mesh>
  );
}

// ---------------------------------------------------------------------------
// Ambient scene decoration: faint grid + environment
// ---------------------------------------------------------------------------
function SceneEnvironment() {
  return (
    <>
      <ambientLight intensity={0.25} />
      <directionalLight position={[5, 8, 5]} intensity={0.6} />
      <directionalLight position={[-3, -4, -5]} intensity={0.15} color="#6366f1" />
      <fog attach="fog" args={["#09090b", 6, 18]} />
    </>
  );
}

// ---------------------------------------------------------------------------
// Main exported component
// ---------------------------------------------------------------------------
interface Props {
  onNodeClick: (node: PipelineNodeData) => void;
}

export default function GraphCanvas3D({ onNodeClick }: Props) {
  const [nodes, setNodes] = useState<PipelineNodeData[]>(
    () => INITIAL_NODES.map((n) => ({ ...n }))
  );
  const hasRunRef = useRef(false);

  const runSimulation = useCallback(() => {
    if (hasRunRef.current) return;
    hasRunRef.current = true;

    INITIAL_NODES.forEach((_, i) => {
      setTimeout(() => {
        setNodes((prev) =>
          prev.map((n, j) => (j === i ? { ...n, status: "running" as NodeStatus } : n))
        );
      }, i * 600);

      setTimeout(() => {
        setNodes((prev) =>
          prev.map((n, j) => (j === i ? { ...n, status: "success" as NodeStatus } : n))
        );
      }, i * 600 + 500);
    });
  }, []);

  useEffect(() => {
    const timer = setTimeout(runSimulation, 800);
    return () => clearTimeout(timer);
  }, [runSimulation]);

  return (
    <div className="pipeline-3d-container relative h-[320px] w-full overflow-hidden rounded-2xl sm:h-[400px]">
      <Canvas
        camera={{ position: [0, 0.5, 7], fov: 40, near: 0.1, far: 50 }}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
        style={{ background: "transparent" }}
        dpr={[1, 1.5]}
      >
        <SceneEnvironment />

        {nodes.map((node) => (
          <NodeMesh key={node.id} node={node} onClick={onNodeClick} />
        ))}

        {EDGES.map(([from, to], i) => (
          <EdgeLine key={`edge-${i}`} fromNode={nodes[from]} toNode={nodes[to]} />
        ))}

        {EDGES.map(([from, to], i) => (
          <EdgeParticle
            key={`particle-${i}`}
            fromNode={nodes[from]}
            toNode={nodes[to]}
            speed={1.0 + i * 0.15}
          />
        ))}

        <OrbitControls
          enableDamping
          dampingFactor={0.08}
          enablePan={false}
          minDistance={4}
          maxDistance={12}
          minPolarAngle={Math.PI / 4}
          maxPolarAngle={Math.PI / 1.8}
          autoRotate
          autoRotateSpeed={0.3}
        />
      </Canvas>
    </div>
  );
}
