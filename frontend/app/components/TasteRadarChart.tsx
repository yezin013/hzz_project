"use client";

import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, Tooltip } from 'recharts';

interface TasteData {
    sweetness: number;
    sourness: number;
    freshness: number;
    body: number;
    balance: number;
    aroma: number;
}

interface TasteRadarChartProps {
    data: TasteData;
}

export default function TasteRadarChart({ data }: TasteRadarChartProps) {
    // Transform data into recharts format with icons embedded in category names
    const chartData = [
        { category: '🍯 단맛', value: data.sweetness, fullMark: 5 },
        { category: '🍋 신맛', value: data.sourness, fullMark: 5 },
        { category: '💧 청량감', value: data.freshness, fullMark: 5 },
        { category: '🏋️ 바디감', value: data.body, fullMark: 5 },
        { category: '⚖️ 균형감', value: data.balance, fullMark: 5 },
        { category: '🌸 향', value: data.aroma, fullMark: 5 }
    ];

    return (
        <div style={{
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            marginTop: '10px'
        }}>
            {/* Title removed or minimized since it's now context-aware */}
            <h3 style={{
                margin: '0 0 10px 0',
                color: '#5d4037',
                fontSize: '1.1rem',
                fontWeight: '800',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
            }}>

            </h3>

            <div style={{
                width: '100%',
                height: '300px', // Reduced height
                position: 'relative'
            }}>
                <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="75%" data={chartData}>
                        <PolarGrid stroke="#8d6e63" strokeOpacity={0.3} />
                        <PolarAngleAxis
                            dataKey="category"
                            tick={{ fill: '#4e342e', fontSize: 16, fontWeight: 700 }} // Increased fontSize to 16
                        />
                        <PolarRadiusAxis
                            angle={90}
                            domain={[0, 5]}
                            tick={false}
                            axisLine={false}
                        />
                        <Radar
                            name="맛 지표"
                            dataKey="value"
                            stroke="#8d6e63"
                            fill="#a1887f"
                            fillOpacity={0.7}
                            strokeWidth={2}
                        />
                        <Tooltip
                            contentStyle={{
                                background: 'rgba(255, 255, 255, 0.95)',
                                border: '1px solid #d7ccc8',
                                borderRadius: '8px',
                                padding: '8px 12px',
                                boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                            }}
                            itemStyle={{ color: '#5d4037', fontWeight: '600', fontSize: '1.1rem' }} // Increased value font size
                            formatter={(value: number | undefined) => [`${value ?? 0}/5`, '점수']}
                        />
                    </RadarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
