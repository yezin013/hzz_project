"use client";

import { useState, useCallback, useRef, useEffect } from 'react';

interface TasteData {
    sweet: number;
    sour: number;
    body: number;
    scent: number;
    throat: number;
}

interface InteractiveTasteRadarChartProps {
    data: TasteData;
    onChange: (data: TasteData) => void;
}

const TASTE_LABELS = [
    { key: 'sweet', label: '🍯 단맛', angle: -90 },
    { key: 'sour', label: '🍋 신맛', angle: -18 },
    { key: 'body', label: '🏋️ 바디감', angle: 54 },
    { key: 'scent', label: '🌸 향', angle: 126 },
    { key: 'throat', label: '💧 목넘김', angle: 198 },
] as const;

const CENTER = 150;
const MAX_RADIUS = 100;
const LEVELS = 5;

export default function InteractiveTasteRadarChart({ data, onChange }: InteractiveTasteRadarChartProps) {
    const svgRef = useRef<SVGSVGElement>(null);
    const [hoveredAxis, setHoveredAxis] = useState<string | null>(null);

    // Convert angle to radians
    const toRadians = (angle: number) => (angle * Math.PI) / 180;

    // Get point position for a value on an axis
    const getPoint = (angle: number, value: number) => {
        const radius = (value / LEVELS) * MAX_RADIUS;
        const rad = toRadians(angle);
        return {
            x: CENTER + radius * Math.cos(rad),
            y: CENTER + radius * Math.sin(rad),
        };
    };

    // Generate polygon points for the data shape
    const getPolygonPoints = () => {
        return TASTE_LABELS.map(({ key, angle }) => {
            const value = data[key as keyof TasteData];
            const point = getPoint(angle, value);
            return `${point.x},${point.y}`;
        }).join(' ');
    };

    // Generate grid polygons
    const getGridPolygon = (level: number) => {
        return TASTE_LABELS.map(({ angle }) => {
            const point = getPoint(angle, level);
            return `${point.x},${point.y}`;
        }).join(' ');
    };

    // Handle click on axis to set value
    const handleAxisClick = (key: string, event: React.MouseEvent<SVGGElement>) => {
        if (!svgRef.current) return;

        const svg = svgRef.current;
        const rect = svg.getBoundingClientRect();
        const clickX = event.clientX - rect.left;
        const clickY = event.clientY - rect.top;

        // Calculate distance from center
        const dx = clickX - CENTER;
        const dy = clickY - CENTER;
        const distance = Math.sqrt(dx * dx + dy * dy);

        // Convert distance to value (1-5)
        const value = Math.min(LEVELS, Math.max(1, Math.round((distance / MAX_RADIUS) * LEVELS)));

        onChange({
            ...data,
            [key]: value,
        });
    };

    // Render grid lines
    const renderGrid = () => {
        const elements = [];

        // Concentric pentagons
        for (let level = 1; level <= LEVELS; level++) {
            elements.push(
                <polygon
                    key={`grid-${level}`}
                    points={getGridPolygon(level)}
                    fill="none"
                    stroke="#d7ccc8"
                    strokeWidth={level === LEVELS ? 1.5 : 0.5}
                    strokeOpacity={0.6}
                />
            );
        }

        // Axis lines from center to each vertex
        TASTE_LABELS.forEach(({ angle }, idx) => {
            const endPoint = getPoint(angle, LEVELS);
            elements.push(
                <line
                    key={`axis-${idx}`}
                    x1={CENTER}
                    y1={CENTER}
                    x2={endPoint.x}
                    y2={endPoint.y}
                    stroke="#d7ccc8"
                    strokeWidth={0.5}
                    strokeOpacity={0.6}
                />
            );
        });

        return elements;
    };

    // Render labels and interactive handles
    const renderLabelsAndHandles = () => {
        return TASTE_LABELS.map(({ key, label, angle }) => {
            const value = data[key as keyof TasteData];
            const labelPoint = getPoint(angle, LEVELS + 1.2);
            const handlePoint = getPoint(angle, value);
            const isHovered = hoveredAxis === key;

            return (
                <g
                    key={key}
                    onClick={(e) => handleAxisClick(key, e)}
                    onMouseEnter={() => setHoveredAxis(key)}
                    onMouseLeave={() => setHoveredAxis(null)}
                    style={{ cursor: 'pointer' }}
                >
                    {/* Clickable axis area */}
                    <line
                        x1={CENTER}
                        y1={CENTER}
                        x2={getPoint(angle, LEVELS).x}
                        y2={getPoint(angle, LEVELS).y}
                        stroke="transparent"
                        strokeWidth={20}
                    />

                    {/* Handle circle */}
                    <circle
                        cx={handlePoint.x}
                        cy={handlePoint.y}
                        r={isHovered ? 10 : 7}
                        fill={isHovered ? '#6d4c41' : '#8d6e63'}
                        stroke="white"
                        strokeWidth={2}
                        style={{
                            transition: 'r 0.15s, fill 0.15s',
                            filter: isHovered ? 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))' : 'none',
                        }}
                    />

                    {/* Value indicator */}
                    <text
                        x={handlePoint.x}
                        y={handlePoint.y}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill="white"
                        fontSize={10}
                        fontWeight="bold"
                        pointerEvents="none"
                    >
                        {value}
                    </text>

                    {/* Label */}
                    <text
                        x={labelPoint.x}
                        y={labelPoint.y}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill={isHovered ? '#5d4037' : '#4e342e'}
                        fontSize={14}
                        fontWeight={isHovered ? 800 : 600}
                        style={{ transition: 'fill 0.15s, font-weight 0.15s' }}
                    >
                        {label}
                    </text>
                </g>
            );
        });
    };

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            padding: '10px 0',
        }}>
            <svg
                ref={svgRef}
                width="300"
                height="300"
                viewBox="0 0 300 300"
                style={{
                    maxWidth: '100%',
                    touchAction: 'none',
                }}
            >
                {/* Grid */}
                {renderGrid()}

                {/* Data polygon */}
                <polygon
                    points={getPolygonPoints()}
                    fill="#a1887f"
                    fillOpacity={0.5}
                    stroke="#8d6e63"
                    strokeWidth={2}
                />

                {/* Labels and handles */}
                {renderLabelsAndHandles()}
            </svg>

            <p style={{
                marginTop: '8px',
                fontSize: '0.85rem',
                color: '#888',
                textAlign: 'center',
            }}>
                각 축을 클릭하여 값을 조절하세요
            </p>
        </div>
    );
}
