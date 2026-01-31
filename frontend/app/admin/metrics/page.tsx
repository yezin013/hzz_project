"use client";

import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getApiUrl } from "@/lib/api";
import styles from "./page.module.css";
import Link from "next/link";

interface MetricsSummary {
    date: string;
    total_requests: number;
    successful_requests: number;
    failed_requests: number;
    success_rate: number;
    total_tokens: number;
    input_tokens: number;
    output_tokens: number;
    avg_tokens_per_request: number;
    avg_latency_seconds: number;
    estimated_cost_usd: number;
}

interface SystemStatus {
    bedrock_available: boolean;
    redis_available: boolean;
    last_error: string | null;
    uptime_seconds: number;
}

interface ErrorLog {
    timestamp: string;
    type: string;
    message: string;
}

export default function MetricsPage() {
    const [todayMetrics, setTodayMetrics] = useState<MetricsSummary | null>(null);
    const [history, setHistory] = useState<MetricsSummary[]>([]);
    const [status, setStatus] = useState<SystemStatus | null>(null);
    const [errors, setErrors] = useState<ErrorLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [currentTime, setCurrentTime] = useState(new Date());

    const fetchData = async () => {
        try {
            // Fetch all data in parallel
            const [metricsRes, historyRes, statusRes, errorsRes] = await Promise.all([
                fetch(getApiUrl('/chatbot/metrics/summary')),
                fetch(getApiUrl('/chatbot/metrics/history?days=7')),
                fetch(getApiUrl('/chatbot/metrics/status')),
                fetch(getApiUrl('/chatbot/metrics/errors?limit=10'))
            ]);

            const metricsData = await metricsRes.json();
            const historyData = await historyRes.json();
            const statusData = await statusRes.json();
            const errorsData = await errorsRes.json();

            setTodayMetrics(metricsData);
            setHistory(historyData.history || []);
            setStatus(statusData);
            setErrors(errorsData.errors || []);
        } catch (err) {
            console.error("Failed to fetch data:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();

        // Auto-refresh every 5 seconds
        const interval = setInterval(() => {
            fetchData();
            setCurrentTime(new Date());
        }, 5000);

        return () => clearInterval(interval);
    }, []);

    const formatUptime = (seconds: number) => {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    const formatTime = (date: Date) => {
        return date.toLocaleTimeString('ko-KR', { hour12: false });
    };

    if (loading) {
        return (
            <div className={styles.terminal}>
                <div className={styles.scanline}></div>
                <div className={styles.boot}>
                    <p>INITIALIZING SYSTEM...</p>
                    <p>LOADING METRICS MODULE<span className={styles.cursor}></span></p>
                </div>
            </div>
        );
    }

    return (
        <div className={styles.terminal}>
            <div className={styles.scanline}></div>

            {/* ASCII Header */}
            <div className={styles.header}>
                <pre className={styles.ascii}>
                    {`
 ██████╗██╗  ██╗ █████╗ ████████╗██████╗  ██████╗ ████████╗
██╔════╝██║  ██║██╔══██╗╚══██╔══╝██╔══██╗██╔═══██╗╚══██╔══╝
██║     ███████║███████║   ██║   ██████╔╝██║   ██║   ██║   
██║     ██╔══██║██╔══██║   ██║   ██╔══██╗██║   ██║   ██║   
╚██████╗██║  ██║██║  ██║   ██║   ██████╔╝╚██████╔╝   ██║   
 ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═════╝  ╚═════╝    ╚═╝   
        METRICS TERMINAL v2.0  •  AWS BEDROCK NOVA
`}
                </pre>
                <div className={styles.systemInfo}>
                    <span>[{formatTime(currentTime)}]</span>
                    <span>AUTO-REFRESH: 5s</span>
                    <Link href="/" className={styles.exit}>[ EXIT ]</Link>
                </div>
            </div>

            {/* System Status */}
            <div className={styles.statusPanel}>
                <div className={styles.statusHeader}>[SYSTEM STATUS]</div>
                <div className={styles.statusGrid}>
                    <div className={styles.statusItem}>
                        <span className={styles.label}>▸ BEDROCK:</span>
                        <span className={status?.bedrock_available ? styles.online : styles.offline}>
                            {status?.bedrock_available ? '● ONLINE' : '● OFFLINE'}
                        </span>
                    </div>
                    <div className={styles.statusItem}>
                        <span className={styles.label}>▸ REDIS:</span>
                        <span className={status?.redis_available ? styles.online : styles.offline}>
                            {status?.redis_available ? '● ONLINE' : '● OFFLINE'}
                        </span>
                    </div>
                    <div className={styles.statusItem}>
                        <span className={styles.label}>▸ UPTIME:</span>
                        <span className={styles.value}>{status ? formatUptime(status.uptime_seconds) : '00:00:00'}</span>
                    </div>
                </div>
            </div>

            {/* Metrics Grid */}
            <div className={styles.metricsGrid}>
                <div className={styles.metricCard}>
                    <div className={styles.metricLabel}>[REQUESTS]</div>
                    <div className={styles.metricValue}>{todayMetrics?.total_requests || 0}</div>
                    <div className={styles.metricSub}>TODAY</div>
                </div>

                <div className={styles.metricCard}>
                    <div className={styles.metricLabel}>[SUCCESS RATE]</div>
                    <div className={styles.metricValue}>{todayMetrics?.success_rate.toFixed(1) || 0}%</div>
                    <div className={styles.metricSub}>{todayMetrics?.successful_requests || 0}/{todayMetrics?.total_requests || 0}</div>
                </div>

                <div className={styles.metricCard}>
                    <div className={styles.metricLabel}>[TOKENS]</div>
                    <div className={styles.metricValue}>{todayMetrics?.total_tokens.toLocaleString() || 0}</div>
                    <div className={styles.metricSub}>IN: {todayMetrics?.input_tokens.toLocaleString() || 0} | OUT: {todayMetrics?.output_tokens.toLocaleString() || 0}</div>
                </div>

                <div className={styles.metricCard}>
                    <div className={styles.metricLabel}>[AVG LATENCY]</div>
                    <div className={styles.metricValue}>{todayMetrics?.avg_latency_seconds.toFixed(2) || 0}s</div>
                    <div className={styles.metricSub}>PER REQUEST</div>
                </div>

                <div className={styles.metricCard}>
                    <div className={styles.metricLabel}>[COST]</div>
                    <div className={styles.metricValue}>${todayMetrics?.estimated_cost_usd.toFixed(4) || 0}</div>
                    <div className={styles.metricSub}>USD TODAY</div>
                </div>

                <div className={styles.metricCard}>
                    <div className={styles.metricLabel}>[AVG TOKENS/REQ]</div>
                    <div className={styles.metricValue}>{Math.round(todayMetrics?.avg_tokens_per_request || 0)}</div>
                    <div className={styles.metricSub}>TOKENS</div>
                </div>
            </div>

            {/* Error Log */}
            {errors.length > 0 && (
                <div className={styles.errorPanel}>
                    <div className={styles.errorHeader}>[ERROR LOG] - LAST {errors.length} EVENTS</div>
                    <div className={styles.errorList}>
                        {errors.map((error, idx) => (
                            <div key={idx} className={styles.errorLine}>
                                <span className={styles.errorTime}>[{new Date(error.timestamp).toLocaleString('ko-KR')}]</span>
                                <span className={styles.errorType}>[{error.type}]</span>
                                <span className={styles.errorMsg}>{error.message}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Usage Graphs */}
            {history.length > 0 && (
                <div className={styles.graphsSection}>
                    <div className={styles.graphsHeader}>[USAGE ANALYTICS] - 7 DAY TRENDS</div>

                    {/* Requests Graph */}
                    <div className={styles.graphCard}>
                        <h3 className={styles.graphTitle}>📊 REQUESTS OVER TIME</h3>
                        <ResponsiveContainer width="100%" height={200}>
                            <LineChart data={[...history].reverse()}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 255, 65, 0.1)" />
                                <XAxis
                                    dataKey="date"
                                    stroke="#00ff41"
                                    style={{ fontSize: '0.75rem' }}
                                />
                                <YAxis
                                    stroke="#00ff41"
                                    style={{ fontSize: '0.75rem' }}
                                />
                                <Tooltip
                                    contentStyle={{
                                        background: '#0a0e27',
                                        border: '1px solid #00ff41',
                                        borderRadius: '4px',
                                        color: '#00ff41',
                                        fontSize: '0.85rem'
                                    }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="total_requests"
                                    stroke="#00ff41"
                                    strokeWidth={2}
                                    dot={{ fill: '#00ff41', r: 4 }}
                                    activeDot={{ r: 6 }}
                                    name="Total Requests"
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Tokens Graph */}
                    <div className={styles.graphCard}>
                        <h3 className={styles.graphTitle}>💎 TOKEN USAGE</h3>
                        <ResponsiveContainer width="100%" height={200}>
                            <LineChart data={[...history].reverse()}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(177, 156, 217, 0.1)" />
                                <XAxis
                                    dataKey="date"
                                    stroke="#b19cd9"
                                    style={{ fontSize: '0.75rem' }}
                                />
                                <YAxis
                                    stroke="#b19cd9"
                                    style={{ fontSize: '0.75rem' }}
                                />
                                <Tooltip
                                    contentStyle={{
                                        background: '#0a0e27',
                                        border: '1px solid #b19cd9',
                                        borderRadius: '4px',
                                        color: '#b19cd9',
                                        fontSize: '0.85rem'
                                    }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="total_tokens"
                                    stroke="#b19cd9"
                                    strokeWidth={2}
                                    dot={{ fill: '#b19cd9', r: 4 }}
                                    activeDot={{ r: 6 }}
                                    name="Tokens"
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Cost Graph */}
                    <div className={styles.graphCard}>
                        <h3 className={styles.graphTitle}>💰 DAILY COST (USD)</h3>
                        <ResponsiveContainer width="100%" height={200}>
                            <LineChart data={[...history].reverse()}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 170, 0, 0.1)" />
                                <XAxis
                                    dataKey="date"
                                    stroke="#ffaa00"
                                    style={{ fontSize: '0.75rem' }}
                                />
                                <YAxis
                                    stroke="#ffaa00"
                                    style={{ fontSize: '0.75rem' }}
                                />
                                <Tooltip
                                    contentStyle={{
                                        background: '#0a0e27',
                                        border: '1px solid #ffaa00',
                                        borderRadius: '4px',
                                        color: '#ffaa00',
                                        fontSize: '0.85rem'
                                    }}
                                    formatter={(value: any) => `$${Number(value).toFixed(4)}`}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="estimated_cost_usd"
                                    stroke="#ffaa00"
                                    strokeWidth={2}
                                    dot={{ fill: '#ffaa00', r: 4 }}
                                    activeDot={{ r: 6 }}
                                    name="Cost"
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}

            {/* History Table */}
            <div className={styles.history}>
                <div className={styles.historyHeader}>[7-DAY HISTORY]</div>
                <div className={styles.historyTable}>
                    <div className={styles.tableRow + ' ' + styles.tableHeaderRow}>
                        <div>DATE</div>
                        <div>REQUESTS</div>
                        <div>TOKENS</div>
                        <div>LATENCY</div>
                        <div>COST</div>
                    </div>
                    {history.map((day, idx) => (
                        <div key={idx} className={styles.tableRow}>
                            <div>{day.date}</div>
                            <div>{day.total_requests}</div>
                            <div>{day.total_tokens.toLocaleString()}</div>
                            <div>{day.avg_latency_seconds.toFixed(2)}s</div>
                            <div>${day.estimated_cost_usd.toFixed(4)}</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Footer */}
            <div className={styles.footer}>
                <span>MONITORING ACTIVE</span>
                <span className={styles.blinkSlow}>●</span>
                <span>NEXT UPDATE IN {5 - (Math.floor(Date.now() / 1000) % 5)}s</span>
            </div>
        </div>
    );
}
