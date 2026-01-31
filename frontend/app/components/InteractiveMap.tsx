import React, { useEffect, useState, useRef, useMemo } from 'react';
import * as d3 from 'd3-geo';
import { select } from 'd3-selection';
import 'd3-transition'; // Import for side effects
import styles from './KoreaMap.module.css';

interface InteractiveMapProps {
    selectedRegion: string | null;
    onSelectRegion: (region: string) => void;
    onSelectCity: (city: string) => void;
}

export default function InteractiveMap({ selectedRegion, onSelectRegion, onSelectCity }: InteractiveMapProps) {
    const [mapData, setMapData] = useState<any[]>([]);
    const [cityGeo, setCityGeo] = useState<any>(null);
    const [provinceFeatures, setProvinceFeatures] = useState<Record<string, any[]>>({});
    const [isDataLoaded, setIsDataLoaded] = useState(false);
    const svgRef = useRef<SVGSVGElement>(null);
    const gRef = useRef<SVGGElement>(null);

    // Mapping from KR-ID to Korean Name
    const ID_TO_NAME: Record<string, string> = {
        "KR-11": "서울특별시",
        "KR-26": "부산광역시",
        "KR-27": "대구광역시",
        "KR-28": "인천광역시",
        "KR-29": "광주광역시",
        "KR-30": "대전광역시",
        "KR-31": "울산광역시",
        "KR-41": "경기도",
        "KR-42": "강원도",
        "KR-43": "충청북도",
        "KR-44": "충청남도",
        "KR-45": "전라북도",
        "KR-46": "전라남도",
        "KR-47": "경상북도",
        "KR-48": "경상남도",
        "KR-49": "제주도",
        "KR-50": "세종특별자치시"
    };

    const PROVINCE_PREFIXES: Record<string, string[]> = {
        "서울특별시": ["11"],
        "부산광역시": ["26"],
        "대구광역시": ["27"],
        "인천광역시": ["28"],
        "광주광역시": ["29"],
        "대전광역시": ["30"],
        "울산광역시": ["31"],
        "경기도": ["41"],
        "강원도": ["51"],
        "충청북도": ["43"],
        "충청남도": ["44"],
        "전라북도": ["45"],
        "전라남도": ["46"],
        "경상북도": ["47"],
        "경상남도": ["48"],
        "제주도": ["50"],
        "세종특별자치시": ["36"]
    };

    // 1. Load Main Map & Pre-process City Data
    useEffect(() => {
        // Load Main Map
        fetch('/korea_map_data.json')
            .then(res => res.json())
            .then(data => setMapData(data))
            .catch(err => console.error("Failed to load korea map data:", err));

        // Load City Map & Pre-group
        fetch('/sig.json')
            .then(res => res.json())
            .then(data => {
                setCityGeo(data);

                // Pre-group features by province to avoid heavy filtering on click
                const grouped: Record<string, any[]> = {};
                const features = data.features;

                // Create a reverse mapping for fast prefix lookup
                const prefixToProvince: Record<string, string> = {};
                Object.entries(PROVINCE_PREFIXES).forEach(([prov, prefixes]) => {
                    prefixes.forEach(p => prefixToProvince[p] = prov);
                });

                features.forEach((f: any) => {
                    const code = f.properties.SIG_CD;
                    const prefix2 = code.substring(0, 2);
                    const province = prefixToProvince[prefix2];

                    if (province) {
                        if (!grouped[province]) grouped[province] = [];
                        grouped[province].push(f);
                    }
                });

                setProvinceFeatures(grouped);
                setIsDataLoaded(true);
                console.log("Optimization: City features pre-grouped by province.");
            })
            .catch(err => console.error("Failed to load city map:", err));
    }, []);

    // D3 Projection for City View
    const projection = useMemo(() => {
        if (!selectedRegion || !provinceFeatures[selectedRegion]) return null;

        const features = provinceFeatures[selectedRegion];

        if (features.length === 0) return null;

        const featureCollection = { type: "FeatureCollection", features: features };

        // Use fitExtent with padding
        const padding = 40;
        const proj = d3.geoMercator();
        proj.fitExtent([[padding, padding], [400 - padding, 500 - padding]], featureCollection as any);

        // [NEW] Region-Specific Scaling Configuration
        // Define custom multipliers for regions that need specific zoom levels
        // You can adjust these numbers to zoom in/out for any region
        const REGION_SCALES: Record<string, number> = {
            // Metropolitan Cities (Gwangyeoksi) & Special Cities
            "서울특별시": 1.2,
            "부산광역시": 1.2,
            "대구광역시": 1.2,
            "인천광역시": 2.6, // User requested larger
            "광주광역시": 1.2,
            "대전광역시": 1.15,
            "울산광역시": 1.1,
            "세종특별자치시": 1.1,

            // Provinces (Do)
            "경기도": 1.2,
            "강원도": 1.1,
            "충청북도": 1.0,
            "충청남도": 1.4,
            "전라북도": 1.4, // User requested larger
            "전라남도": 1.7, // User requested larger (islands)
            "경상북도": 2.3, // User requested larger
            "경상남도": 1.0,
            "제주도": 1.0
        };

        const multiplier = REGION_SCALES[selectedRegion] || 1.0;

        const currentScale = proj.scale();
        if (multiplier !== 1.0) {
            console.log(`[InteractiveMap] Region: ${selectedRegion}, Base Scale: ${currentScale}, Multiplier: ${multiplier}`);
        }

        // To zoom in correctly on the center of the region:
        // 1. Get the geographic centroid of the features
        const center = d3.geoCentroid(featureCollection as any);

        // 2. Set the projection center to that centroid
        proj.center(center);

        // 3. Translate to the center of the SVG (200, 250)
        proj.translate([200, 250]);

        // 4. Apply the magnified scale
        proj.scale(currentScale * multiplier);

        if (multiplier !== 1.0) {
            console.log(`[InteractiveMap] New Scale: ${proj.scale()}`);
        }

        // LIMIT MAX ZOOM: 
        // Increased from 12000 to 500000 to prevent clamping on city views
        const MAX_SCALE = 500000;
        if (proj.scale() > MAX_SCALE) {
            console.log(`[InteractiveMap] Scale ${proj.scale()} clamped to ${MAX_SCALE}`);
            // If we limit scale, we must re-center
            const center = d3.geoCentroid(featureCollection as any);
            proj.center(center);
            proj.translate([200, 250]); // Center of 400x500 box
            proj.scale(MAX_SCALE);
        }

        return proj;
    }, [selectedRegion, provinceFeatures]);

    const pathGenerator = useMemo(() => {
        if (!projection) return null;
        return d3.geoPath().projection(projection);
    }, [projection]);


    // Determine what to render
    const isCityView = !!(selectedRegion && cityGeo && pathGenerator);

    let featuresToRender: any[] = [];
    if (isCityView) {
        featuresToRender = provinceFeatures[selectedRegion!] || [];
    }

    return (
        <div className={styles.mapContainer}>
            {/* Left: Main Korea Map (Dynamic Resizing) */}
            <div className={`${styles.mapPanel} ${(isCityView || (selectedRegion && !isDataLoaded)) ? styles.collapsed : styles.expanded}`} style={{ position: 'relative' }}>
                {/* User Guidance Overlay - Only visible when NO region is selected */}
                {!selectedRegion && (
                    <div className={styles.guideOverlay}>
                        <span className={styles.guideIcon}>👆</span>
                        <p className={styles.guideText}>원하는 지역을 선택해보세요!</p>
                    </div>
                )}
                <h3 className={styles.mapTitle}></h3>
                <svg
                    viewBox="-50 -50 600 750"
                    className={styles.mapSvg}
                    shapeRendering="geometricPrecision"
                    style={{ width: selectedRegion ? '100%' : '85%', height: 'auto' }}
                >
                    <g>
                        {mapData.map((item) => {
                            const name = ID_TO_NAME[item.id] || item.title;
                            const isSelected = selectedRegion === name;

                            return (
                                <path
                                    key={item.id}
                                    d={item.d}
                                    className={`${styles.province} ${isSelected ? styles.active : ''}`}
                                    onClick={() => onSelectRegion(name)}
                                >
                                    <title>{name}</title>
                                </path>
                            );
                        })}
                    </g>
                </svg>
            </div>

            {/* Right: Detailed City View (Slide In) */}
            <div className={`${styles.detailPanel} ${isCityView || (selectedRegion && !isDataLoaded) ? styles.active : ''}`}>
                {(isCityView || (selectedRegion && !isDataLoaded)) && (
                    <>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', marginBottom: '10px' }}>
                            <h3 className={styles.mapTitle} style={{ margin: 0, fontSize: '1.2rem' }}>{selectedRegion}</h3>
                            <button onClick={() => onSelectRegion("")} className={styles.backButton}>
                                뒤로가기
                            </button>
                        </div>
                        <p style={{ textAlign: 'center', color: '#8d6e63', fontSize: '0.9rem', margin: '0 0 15px 0' }}>
                            원하는 지역을 선택하여 전통주를 확인할 수 있습니다.
                        </p>

                        {!isDataLoaded ? (
                            <div className={styles.loadingContainer}>
                                <video
                                    className={styles.loadingVideo}
                                    autoPlay
                                    loop
                                    muted
                                    playsInline
                                >
                                    <source src="/maploading.mp4" type="video/mp4" />
                                </video>
                                <div className={styles.videoOverlay}></div>
                            </div>
                        ) : (
                            <svg
                                ref={svgRef}
                                viewBox={`0 0 400 500`}
                                className={styles.mapSvg}
                                shapeRendering="geometricPrecision"
                                style={{ width: '100%', height: 'auto' }}
                            >
                                <g ref={gRef}>
                                    {featuresToRender.map((feature: any) => {
                                        const d = pathGenerator!(feature);
                                        const name = feature.properties.SIG_KOR_NM;
                                        const code = feature.properties.SIG_CD;

                                        return (
                                            <path
                                                key={code}
                                                d={d || ""}
                                                className={styles.province}
                                                onClick={() => onSelectCity(name)}
                                            >
                                                <title>{name}</title>
                                            </path>
                                        );
                                    })}
                                </g>
                            </svg>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
