// KoreaMap.tsx
import React from 'react';
import styles from './KoreaMap.module.css';
import { MAP_PATHS, REGION_TO_PROVINCE } from './KoreaMapData';

interface KoreaMapProps {
    onSelectRegion: (region: string) => void;
    selectedRegion: string | null;
}

export default function KoreaMap({ onSelectRegion, selectedRegion }: KoreaMapProps) {

    // 클릭 핸들러
    const handlePathClick = (regionId: string) => {
        const province = REGION_TO_PROVINCE[regionId];
        if (province) {
            onSelectRegion(province);
        } else {
            console.warn(`Province mapping not found for ID: ${regionId}`);
        }
    };

    // 선택된 지역 확인 로직
    const isRegionSelected = (regionId: string): boolean => {
        const province = REGION_TO_PROVINCE[regionId];
        return province === selectedRegion;
    };

    return (
        <div className={styles.mapContainer}>
            <svg
                viewBox="0 0 524.23737 630.5871"
                className={styles.mapSvg}
                xmlns="http://www.w3.org/2000/svg"
            >
                {MAP_PATHS.map((pathData) => (
                    <path
                        key={pathData.id}
                        d={pathData.d}
                        id={pathData.id}
                        aria-label={pathData.title}
                        className={`${styles.province} ${isRegionSelected(pathData.id) ? styles.active : ''}`}
                        onClick={() => handlePathClick(pathData.id)}
                    />
                ))}
            </svg>
        </div>
    );
}