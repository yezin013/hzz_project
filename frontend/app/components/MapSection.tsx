"use client";

import { useState, useRef, useEffect } from "react";
import Image from "next/image";
import { getApiUrl } from "@/lib/api";
import styles from "./MapSection.module.css";
import InteractiveMap from './InteractiveMap';
import WeatherBanner from "./WeatherBanner";

interface Liquor {
    id: number;
    name: string;
    type: string;
    alcohol: string;
    image_url: string;
    price: number;
    volume: string;
}

interface Product {
    name: string;
    price: number;
    shop: string;
    url: string;
    image_url: string;
}

export default function MapSection() {
    const [selectedRegion, setSelectedRegion] = useState<string | null>(null);
    const [selectedCity, setSelectedCity] = useState<string | null>(null);
    const [selectedSeason, setSelectedSeason] = useState<string | null>(null);
    const [sortField, setSortField] = useState<'price' | 'alcohol' | 'weather' | null>(null);
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
    const [liquors, setLiquors] = useState<Liquor[]>([]);
    const [loading, setLoading] = useState(false);
    const [weatherRec, setWeatherRec] = useState<any>(null);
    const [weatherSource, setWeatherSource] = useState<'user' | 'map'>('user');
    const [selectedLiquor, setSelectedLiquor] = useState<Liquor | null>(null);
    const [products, setProducts] = useState<Product[]>([]);
    const [loadingProducts, setLoadingProducts] = useState(false);
    const [drinkDetails, setDrinkDetails] = useState<any>(null);

    // Refs for scrolling
    const mapRef = useRef<HTMLDivElement>(null);
    const listRef = useRef<HTMLDivElement>(null);

    // Pagination
    const [currentPage, setCurrentPage] = useState(1);
    const ITEMS_PER_PAGE = 5;

    // Helper to determine weather condition from weather data
    const getWeatherCondition = (weather: any): string => {
        if (!weather) return 'clear';
        const rain = weather.PCPTTN_SHP || '';
        const temp = parseFloat(weather.NOW_AIRTP || '20');

        if (rain.includes('비') || rain === '1' || rain === '2') return 'rain';
        if (rain.includes('눈') || rain === '3') return 'snow';
        if (temp < 5) return 'cold';
        if (temp > 28) return 'hot';
        return 'clear';
    };

    const fetchLiquors = async (province: string, city: string | null = null, season: string | null = null) => {
        setLoading(true);
        try {
            let url = getApiUrl(`/search/region?province=${encodeURIComponent(province)}&size=1000`);
            if (city) {
                url += `&city=${encodeURIComponent(city)}`;
            }
            if (season) {
                url += `&season=${encodeURIComponent(season)}`;
            }

            // Add weather sorting if enabled
            if (sortField === 'weather' && weatherRec?.weather) {
                const condition = getWeatherCondition(weatherRec.weather);
                url += `&weather_condition=${condition}&weather_sort=true`;
            }

            const response = await fetch(url);
            if (response.ok) {
                const data = await response.json();
                setLiquors(data);
            } else {
                setLiquors([]);
            }
        } catch (error) {
            console.error("Failed to fetch regional liquors:", error);
            setLiquors([]);
        } finally {
            setLoading(false);
            setCurrentPage(1);
        }
    };

    const fetchProducts = async (drinkName: string) => {
        setLoadingProducts(true);
        try {
            const response = await fetch(getApiUrl(`/search/products/${encodeURIComponent(drinkName)}`));
            if (response.ok) {
                const data = await response.json();
                setProducts(data.products || []);
            } else {
                setProducts([]);
            }
        } catch (error) {
            console.error("Failed to fetch products:", error);
            setProducts([]);
        } finally {
            setLoadingProducts(false);
        }
    };

    const fetchDrinkDetails = async (drinkId: number) => {
        if (!drinkId) return;

        try {
            const response = await fetch(getApiUrl(`/search/detail/${drinkId}`));
            if (response.ok) {
                const data = await response.json();
                setDrinkDetails(data);
            } else {
                setDrinkDetails(null);
            }
        } catch (error) {
            console.error("Failed to fetch drink details:", error);
            setDrinkDetails(null);
        }
    };

    const handleSelectRegion = (region: string) => {
        if (selectedRegion === region) return;

        setSelectedRegion(region);
        setSelectedCity(null);
        setSelectedLiquor(null);
        setProducts([]);
        fetchLiquors(region, null, selectedSeason);
    };

    const handleSelectCity = (city: string) => {
        setSelectedCity(city);
        if (selectedRegion) {
            fetchLiquors(selectedRegion, city, selectedSeason);
        }
    };

    // Mobile Auto-Scroll Effect
    useEffect(() => {
        // Only run on mobile
        if (typeof window !== 'undefined' && window.innerWidth <= 768) {
            if (selectedRegion && !selectedCity) {
                // When region selected (and not city yet), scroll to map (detail view)
                // Small delay to allow render
                setTimeout(() => {
                    mapRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 100);
            } else if (selectedCity) {
                // When city selected, scroll to list
                setTimeout(() => {
                    listRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 100);
            }
        }
    }, [selectedRegion, selectedCity]);

    return (
        <div className={styles.mapSectionContainer}>
            {/* Background - Controlled by CSS now */}
            <div className={styles.background} />

            <div className={styles.heroContent}>
                {/* Left: Maps Container */}
                <div className={styles.mapSection} ref={mapRef}>
                    <InteractiveMap
                        selectedRegion={selectedRegion}
                        onSelectRegion={handleSelectRegion}
                        onSelectCity={handleSelectCity}
                    />
                </div>

                {/* Right: Content Panels Container */}
                <div className={styles.contentPanels}>
                    {/* Panel 1: Weather Banner */}
                    <div style={{ flex: '0 0 auto' }}>
                        <WeatherBanner
                            onRecommendationUpdate={setWeatherRec}
                            onRegionSelect={(province, city) => {
                                handleSelectRegion(province);
                                if (city) handleSelectCity(city);
                            }}
                            activeProvinceName={selectedRegion}
                            activeCityName={selectedCity}
                        />
                    </div>

                    {/* Panel 2: Liquor List */}
                    <div className={styles.listContainer} ref={listRef}>
                        <h2 className={styles.sectionTitle} style={{ color: '#333', marginTop: 0 }}>
                            {selectedRegion ? `${selectedRegion} ${selectedCity || ''}의 전통주` : "지역을 선택해주세요"}
                        </h2>

                        {/* Season Tabs */}
                        {selectedRegion && (
                            <div className={styles.seasonTabs} style={{ marginBottom: '4px' }}>
                                {['전체', '봄', '여름', '가을', '겨울'].map((season) => (
                                    <button
                                        key={season}
                                        className={`${styles.seasonChip} ${((selectedSeason === null && season === '전체') || selectedSeason === season) ? styles.active : ''}`}
                                        onClick={() => {
                                            const newSeason = season === '전체' ? null : season;
                                            setSelectedSeason(newSeason);
                                            if (selectedRegion) {
                                                fetchLiquors(selectedRegion, selectedCity, newSeason);
                                            }
                                        }}
                                    >
                                        {season}
                                    </button>
                                ))}
                            </div>
                        )}

                        {/* Sort Buttons */}
                        {selectedRegion && (
                            <div className={styles.sortButtons} style={{ marginBottom: '6px' }}>
                                <button
                                    className={sortField === 'price' ? styles.activeSortBtn : ''}
                                    onClick={() => {
                                        if (sortField === 'price') {
                                            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                                        } else {
                                            setSortField('price');
                                            setSortOrder('asc');
                                        }
                                    }}
                                >
                                    💰 가격 {sortField === 'price' ? (sortOrder === 'asc' ? '↑' : '↓') : ''}
                                </button>
                                <button
                                    className={sortField === 'alcohol' ? styles.activeSortBtn : ''}
                                    onClick={() => {
                                        if (sortField === 'alcohol') {
                                            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                                        } else {
                                            setSortField('alcohol');
                                            setSortOrder('asc');
                                        }
                                    }}
                                >
                                    🍶 도수 {sortField === 'alcohol' ? (sortOrder === 'asc' ? '↑' : '↓') : ''}
                                </button>
                                <button
                                    className={sortField === 'weather' ? styles.activeSortBtn : ''}
                                    onClick={() => {
                                        setSortField('weather');
                                        if (selectedRegion) fetchLiquors(selectedRegion, selectedCity, selectedSeason);
                                    }}
                                >
                                    날씨 추천순 ☀️
                                </button>
                            </div>
                        )}



                        <div className={styles.liquorList}>
                            {selectedRegion ? (
                                loading ? (
                                    <div className={styles.loadingMessage}>불러오는 중... 🍶</div>
                                ) : liquors && liquors.length > 0 ? (
                                    <>
                                        {(() => {
                                            // Apply sorting
                                            let sortedLiquors = [...liquors];
                                            if (sortField === 'price') {
                                                sortedLiquors.sort((a, b) => {
                                                    const priceA = a.price || 0;
                                                    const priceB = b.price || 0;
                                                    return sortOrder === 'asc' ? priceA - priceB : priceB - priceA;
                                                });
                                            } else if (sortField === 'alcohol') {
                                                sortedLiquors.sort((a, b) => {
                                                    const alcoholA = parseFloat(a.alcohol) || 0;
                                                    const alcoholB = parseFloat(b.alcohol) || 0;
                                                    return sortOrder === 'asc' ? alcoholA - alcoholB : alcoholB - alcoholA;
                                                });
                                            }
                                            return sortedLiquors.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE);
                                        })().map((liquor) => (
                                            <div
                                                key={liquor.id}
                                                className={`${styles.liquorCard} ${selectedLiquor?.id === liquor.id ? styles.selectedCard : ''}`}
                                                onClick={() => {
                                                    setSelectedLiquor(liquor);
                                                    fetchProducts(liquor.name);
                                                    if (liquor.id) {
                                                        fetchDrinkDetails(liquor.id);
                                                    }
                                                }}
                                            >
                                                <div
                                                    className={styles.liquorImagePlaceholder}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        window.location.href = `/drink/${liquor.id}`;
                                                    }}
                                                    style={{ cursor: 'pointer' }}
                                                >
                                                    {liquor.image_url ? (
                                                        <img src={`/api/image-proxy?url=${encodeURIComponent(liquor.image_url)}`} alt={liquor.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                                                    ) : (
                                                        <span>🍶</span>
                                                    )}
                                                </div>
                                                <div className={styles.liquorInfo}>
                                                    <h3>{liquor.name}</h3>
                                                    <p>{liquor.type} | {liquor.alcohol}</p>
                                                    <p style={{ color: '#d32f2f', fontWeight: 'bold' }}>
                                                        {liquor.price ? `${liquor.price.toLocaleString()}원~` : '가격 확인'}
                                                    </p>
                                                </div>
                                                <button
                                                    className={styles.detailButton}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        window.location.href = `/drink/${liquor.id}`;
                                                    }}
                                                >
                                                    상세보기 →
                                                </button>
                                            </div>
                                        ))}

                                        {/* Pagination Controls */}
                                        {liquors.length > ITEMS_PER_PAGE && (
                                            <div className={styles.pagination}>
                                                {(() => {
                                                    const totalPages = Math.ceil(liquors.length / ITEMS_PER_PAGE);
                                                    const pageGroupSize = 5;
                                                    const currentGroup = Math.ceil(currentPage / pageGroupSize);
                                                    const startPage = (currentGroup - 1) * pageGroupSize + 1;
                                                    const endPage = Math.min(startPage + pageGroupSize - 1, totalPages);

                                                    return (
                                                        <>
                                                            {startPage > 1 && (
                                                                <button
                                                                    className={styles.pageButton}
                                                                    onClick={() => setCurrentPage(startPage - 1)}
                                                                >
                                                                    &lt;&lt;
                                                                </button>
                                                            )}
                                                            <button
                                                                className={styles.pageButton}
                                                                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                                                                disabled={currentPage === 1}
                                                            >
                                                                &lt;
                                                            </button>
                                                            {Array.from({ length: endPage - startPage + 1 }, (_, i) => startPage + i).map((pageNum) => (
                                                                <button
                                                                    key={pageNum}
                                                                    className={`${styles.pageButton} ${currentPage === pageNum ? styles.activePage : ''}`}
                                                                    onClick={() => setCurrentPage(pageNum)}
                                                                >
                                                                    {pageNum}
                                                                </button>
                                                            ))}
                                                            <button
                                                                className={styles.pageButton}
                                                                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                                                                disabled={currentPage === totalPages}
                                                            >
                                                                &gt;
                                                            </button>
                                                            {endPage < totalPages && (
                                                                <button
                                                                    className={styles.pageButton}
                                                                    onClick={() => setCurrentPage(endPage + 1)}
                                                                >
                                                                    &gt;&gt;
                                                                </button>
                                                            )}
                                                        </>
                                                    );
                                                })()}
                                            </div>
                                        )}
                                    </>
                                ) : (
                                    <p className={styles.emptyMessage}>등록된 전통주 정보가 없습니다.</p>
                                )
                            ) : (
                                <div className={styles.instructionMessage}>
                                    <p>👈 왼쪽 지도에서 지역을 선택하면</p>
                                    <p>해당 지역의 대표 전통주가 여기에 표시됩니다.</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Panel 3: Products Comparison / Side Dish */}
                    <div className={styles.sideDishPanel}>
                        {selectedLiquor ? (
                            <>
                                <h2 style={{ color: '#333', marginTop: 0, fontSize: '1.5rem', marginBottom: '15px' }}>
                                    {selectedLiquor.name} 구매처
                                </h2>
                                {loadingProducts ? (
                                    <div style={{ textAlign: 'center', padding: '40px 20px', color: '#999' }}>
                                        <p>불러오는 중...</p>
                                    </div>
                                ) : products.length > 0 ? (
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto', maxHeight: '600px' }}>
                                        {products.map((product, index) => {
                                            const isReference = product.shop === "지식백과 기준 가격" || product.shop === "구매처 검색하기";
                                            return (
                                                <a
                                                    key={index}
                                                    href={product.url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    style={{
                                                        padding: '10px',
                                                        background: isReference ? '#fff8e1' : "url('/한지흰색.jpg') repeat",
                                                        backgroundSize: isReference ? 'auto' : '200px',
                                                        backgroundColor: isReference ? '#fff8e1' : undefined,
                                                        borderRadius: '8px',
                                                        textDecoration: 'none',
                                                        color: '#333',
                                                        border: isReference ? '1px solid #ffca28' : '1px solid #d7ccc8',
                                                        transition: 'transform 0.2s, box-shadow 0.2s',
                                                        display: 'flex',
                                                        gap: '10px',
                                                        alignItems: 'center'
                                                    }}
                                                    onMouseEnter={(e) => {
                                                        e.currentTarget.style.transform = 'translateY(-2px)';
                                                        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                                                    }}
                                                    onMouseLeave={(e) => {
                                                        e.currentTarget.style.transform = 'translateY(0)';
                                                        e.currentTarget.style.boxShadow = 'none';
                                                    }}
                                                >
                                                    {product.image_url && (
                                                        <div style={{ flexShrink: 0, width: '55px', height: '55px', borderRadius: '6px', overflow: 'hidden', background: '#f5f5f5' }}>
                                                            <img
                                                                src={product.image_url}
                                                                alt={product.name}
                                                                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                                                onError={(e) => { e.currentTarget.style.display = 'none'; }}
                                                            />
                                                        </div>
                                                    )}
                                                    <div style={{ flex: 1, minWidth: 0 }}>
                                                        <div style={{ fontSize: '0.75rem', color: isReference ? '#e65100' : '#888', marginBottom: '2px', fontWeight: isReference ? 'bold' : 'normal' }}>
                                                            {product.shop}
                                                        </div>
                                                        <div style={{ fontSize: '0.85rem', fontWeight: '500', marginBottom: '4px', lineHeight: '1.2', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                            {product.name}
                                                        </div>
                                                        <div style={{ fontSize: '1rem', fontWeight: 'bold', color: '#d32f2f' }}>
                                                            {product.price > 0 ? `${product.price.toLocaleString()}원` : '가격 정보 확인'}
                                                        </div>
                                                    </div>
                                                    <div style={{ fontSize: '1.2rem', color: isReference ? '#e65100' : '#8d6e63' }}>→</div>
                                                </a>
                                            );
                                        })}
                                    </div>
                                ) : drinkDetails?.price_is_reference ? (
                                    <div style={{ textAlign: 'center', padding: '30px 20px', background: "url('/한지.jpg')", backgroundSize: 'cover', borderRadius: '12px', border: '2px solid #d7ccc8' }}>
                                        <p style={{ fontSize: '2.5rem', marginBottom: '10px' }}>📚</p>
                                        <h3 style={{ margin: '0 0 10px 0', color: '#333' }}>구매 정보</h3>
                                        <p style={{ margin: '0 0 15px 0', fontSize: '0.95rem', color: '#333' }}>현재 온라인 판매처 정보가 없습니다.</p>
                                        {drinkDetails.encyclopedia_price_text && (
                                            <div style={{ background: 'rgba(255,243,224,0.6)', border: '1px solid #ffca28', borderRadius: '8px', padding: '12px', marginBottom: '15px' }}>
                                                <strong style={{ display: 'block', marginBottom: '8px', color: '#e65100', fontSize: '0.95rem' }}>💰 참고 가격</strong>
                                                <div style={{ fontSize: '0.95rem', color: '#3e2723', fontWeight: '600', lineHeight: '1.6' }}>
                                                    {(() => {
                                                        const priceText = drinkDetails.encyclopedia_price_text.replace(/\(가격은 판매처 별로 상이할 수 있습니다\)/g, '');
                                                        const matches = priceText.match(/(\d+ml\s*￦[\d,]+)/g) || [];
                                                        return matches.map((item: string, idx: number) => (
                                                            <div key={idx} style={{ marginBottom: idx < matches.length - 1 ? '4px' : '0' }}>
                                                                {item.trim()}
                                                            </div>
                                                        ));
                                                    })()}
                                                </div>
                                                <p style={{ margin: '8px 0 0 0', fontSize: '0.75rem', color: '#795548' }}>(가격은 판매처 별로 상이할 수 있습니다)</p>
                                            </div>
                                        )}
                                        <p style={{ fontSize: '0.85rem', color: '#666', marginBottom: '12px' }}>더 자세한 제품 정보는 네이버 지식백과에서 확인하실 수 있습니다.</p>
                                        {drinkDetails.encyclopedia_url && (
                                            <a href={drinkDetails.encyclopedia_url} target="_blank" rel="noopener noreferrer" style={{ display: 'inline-block', background: 'linear-gradient(45deg, #ff6f00, #ffca28)', color: 'white', padding: '10px 20px', borderRadius: '20px', fontSize: '0.9rem', fontWeight: 'bold', textDecoration: 'none', boxShadow: '0 3px 6px rgba(0,0,0,0.1)' }}>
                                                📖 지식백과에서 보기 →
                                            </a>
                                        )}
                                    </div>
                                ) : (
                                    <div style={{ textAlign: 'center', padding: '40px 20px', color: '#888' }}>
                                        <p style={{ fontSize: '2rem', marginBottom: '10px' }}>🍶</p>
                                        <p>온라인 판매처 정보가 없습니다.</p>
                                        <p style={{ fontSize: '0.85rem', color: '#aaa' }}>양조장에 직접 문의해주세요.</p>
                                    </div>
                                )}
                            </>
                        ) : (
                            <div style={{ textAlign: 'center', padding: '60px 20px', color: '#999' }}>
                                <p style={{ fontSize: '3rem', marginBottom: '15px' }}>🍶</p>
                                <p style={{ fontSize: '1.1rem', color: '#666' }}>전통주를 선택하면</p>
                                <p style={{ fontSize: '1.1rem', color: '#666' }}>최저가 판매처가 표시됩니다</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
