import React, { useEffect, useState, useMemo } from 'react';
import * as d3 from 'd3-geo';
import styles from './KoreaMap.module.css';

interface DetailedKoreaMapProps {
    selectedRegion: string;
    onSelectCity: (city: string) => void;
    onBack: () => void;
}

// Mapping from Province Name to SIG_CD prefixes
const PROVINCE_TO_PREFIX: Record<string, string[]> = {
    "경기도": ["11", "28", "41"], // Seoul, Incheon, Gyeonggi
    "강원도": ["42"],
    "충청북도": ["43"],
    "충청남도": ["30", "44", "36"], // Daejeon, Chungnam, Sejong
    "전라북도": ["45"],
    "전라남도": ["29", "46"], // Gwangju, Jeonnam
    "경상북도": ["27", "47"], // Daegu, Gyeongbuk
    "경상남도": ["26", "31", "48"], // Busan, Ulsan, Gyeongnam
    "제주도": ["50"],
};

export default function DetailedKoreaMap({ selectedRegion, onSelectCity, onBack }: DetailedKoreaMapProps) {
    const [geoJson, setGeoJson] = useState<any>(null);

    useEffect(() => {
        fetch('/sig.json')
            .then(res => res.json())
            .then(data => setGeoJson(data))
            .catch(err => console.error("Failed to load map data:", err));
    }, []);

    const filteredFeatures = useMemo(() => {
        if (!geoJson || !selectedRegion) return [];
        const prefixes = PROVINCE_TO_PREFIX[selectedRegion] || [];
        return geoJson.features.filter((f: any) => {
            const code = f.properties.SIG_CD;
            return prefixes.some(prefix => code.startsWith(prefix));
        });
    }, [geoJson, selectedRegion]);

    // Projection logic
    const { path, projection } = useMemo(() => {
        if (filteredFeatures.length === 0) return { path: null, projection: null };

        // Create a temporary projection to fit the features
        const width = 500;
        const height = 600;

        // Use Mercator or Transverse Mercator (standard for Korea is roughly TM, but Mercator is fine for web)
        const proj = d3.geoMercator().fitSize([width, height], {
            type: "FeatureCollection",
            features: filteredFeatures
        });

        const pathGenerator = d3.geoPath().projection(proj);
        return { path: pathGenerator, projection: proj };
    }, [filteredFeatures]);

    if (!geoJson) return <div>Loading Map...</div>;

    return (
        <div className={styles.mapContainer}>
            <button onClick={onBack} className={styles.backButton}>
                ← 전체 지도 보기
            </button>
            <h3 className={styles.mapTitle}>{selectedRegion} 상세 지도</h3>
            <svg viewBox="0 0 500 600" className={styles.mapSvg}>
                {filteredFeatures.map((feature: any, idx: number) => {
                    const d = path ? path(feature) : "";
                    const name = feature.properties.SIG_KOR_NM;
                    return (
                        <path
                            key={feature.properties.SIG_CD}
                            d={d || ""}
                            className={styles.province} // Reusing province style for now
                            onClick={() => onSelectCity(name)}
                            onMouseEnter={(e) => {
                                // Optional: Add hover effect or tooltip
                                e.currentTarget.style.fill = "#d32f2f";
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.fill = "";
                            }}
                        >
                            <title>{name}</title>
                        </path>
                    );
                })}
            </svg>
        </div>
    );
}
