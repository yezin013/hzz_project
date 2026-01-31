"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { getApiUrl } from "@/lib/api";
import styles from "./ProductGridSection.module.css";

interface Drink {
    id: number;
    name: string;
    image_url: string;
    type: string;
    alcohol: string;
    price: number;
    volume: string;
    province: string;
    city: string;
}

interface ProductGridSectionProps {
    initialQuery?: string;
}

const DRINK_TYPES = [
    "탁주(고도)", "탁주(저도)", "약주, 청주", "과실주", "증류주", "리큐르/기타주류"
];

// ES에 저장된 실제 province 값들 (MariaDB region 테이블 기준)
const PROVINCES = [
    "제주도", "경기도", "전라남도", "강원도", "경상북도", "충청북도",
    "전라북도", "경상남도", "충청남도", "기타"
];


export default function ProductGridSection({ initialQuery = "" }: ProductGridSectionProps) {
    const [drinks, setDrinks] = useState<Drink[]>([]);
    const [loading, setLoading] = useState(false);
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);
    const [sort, setSort] = useState("price_desc");
    const [query, setQuery] = useState(initialQuery);
    const [totalCount, setTotalCount] = useState(0);
    const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
    const [selectedRegions, setSelectedRegions] = useState<string[]>([]);
    const [selectedSeason, setSelectedSeason] = useState<string>("");
    const [selectedAbv, setSelectedAbv] = useState<string>("");
    const [showFilters, setShowFilters] = useState(false);

    // Local state for the search input to avoid triggering fetch on every keystroke
    const [localQuery, setLocalQuery] = useState(initialQuery);

    // Reset when query or sort changes
    useEffect(() => {
        // setPage(1); 
        fetchData(1, sort, query, selectedTypes, selectedRegions, selectedSeason, selectedAbv);
    }, [sort, query, selectedTypes, selectedRegions, selectedSeason, selectedAbv]);

    // Update query if initialQuery prop changes (from parent search)
    useEffect(() => {
        if (initialQuery !== query) {
            setQuery(initialQuery);
            setLocalQuery(initialQuery);
        }
    }, [initialQuery]);

    const handleSearchSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setQuery(localQuery);
        setPage(1);
    };

    const fetchData = async (pageNum: number, sortOrder: string, searchQuery: string, types: string[] = [], regions: string[] = [], season: string = "", abv: string = "") => {
        setLoading(true);
        console.log("Fetching with filters:", { types, regions, season, abv });
        try {
            // Page size 24 for better grid alignment
            let url = getApiUrl(`/search/list?page=${pageNum}&size=24&sort=${sortOrder}`);
            if (searchQuery) url += `&query=${encodeURIComponent(searchQuery)}`;
            // Use pipe | delimiter to avoid conflict with commas in values (e.g. "약주, 청주")
            if (types.length > 0) url += `&type=${encodeURIComponent(types.join("|"))}`;
            if (regions.length > 0) url += `&region=${encodeURIComponent(regions.join("|"))}`;
            if (season) url += `&season=${encodeURIComponent(season)}`;

            // Handle ABV ranges (ES stores as decimal: 0.13 = 13%)
            // Backend will handle conversion from percentage to decimal
            if (abv === "low") { // 0-10%
                url += `&max_abv=0.1`;
            } else if (abv === "medium") { // 10-20%
                url += `&min_abv=0.1&max_abv=0.2`;
            } else if (abv === "high") { // 20%+
                url += `&min_abv=0.2`;
            }

            const res = await fetch(url);
            if (res.ok) {
                const data = await res.json();
                const newDrinks = data.drinks || [];
                setTotalCount(data.total);
                setDrinks(newDrinks);
            }
        } catch (err) {
            console.error("Failed to fetch drinks", err);
        } finally {
            setLoading(false);
        }
    };

    const handlePageChange = (newPage: number) => {
        if (newPage === page) return;
        setPage(newPage);
        fetchData(newPage, sort, query, selectedTypes, selectedRegions, selectedSeason, selectedAbv);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    return (
        <div className={styles.gridSection}>


            {/* Filters Section - Always Visible */}
            <div className={styles.filterContainer}>
                <div className={styles.filterHeader}>
                    {/* Integrated Search Bar */}
                    <form className={styles.searchForm} onSubmit={handleSearchSubmit}>
                        <div className={styles.inputWrapper}>
                            <span className={styles.searchIcon}>🔍</span>
                            <input
                                type="text"
                                placeholder="전통주 이름으로 검색해보세요"
                                value={localQuery}
                                onChange={(e) => setLocalQuery(e.target.value)}
                                className={styles.searchInput}
                            />
                            {localQuery && (
                                <button
                                    type="button"
                                    className={styles.clearButton}
                                    onClick={() => { setLocalQuery(""); setQuery(""); }}
                                >
                                    ✕
                                </button>
                            )}
                        </div>
                        <button type="submit" className={styles.searchButton}>검색</button>
                    </form>
                    {((selectedSeason ? 1 : 0) + (selectedAbv ? 1 : 0)) > 0 &&
                        <span className={styles.filterBadge}>
                            {(selectedSeason ? 1 : 0) + (selectedAbv ? 1 : 0)}
                        </span>
                    }
                    {/* Mobile Toggle Button */}
                    <button
                        className={styles.mobileFilterToggle}
                        onClick={() => setShowFilters(!showFilters)}
                        type="button"
                    >
                        {showFilters ? "접기 ▲" : "펼치기 ▼"}
                    </button>
                </div>

                <div className={`${styles.filterPanel} ${showFilters ? styles.show : ''}`}>
                    <div className={styles.filterRow}>
                        {/* Season Filter */}
                        <div className={styles.filterGroup}>
                            <h4>계절 추천</h4>
                            <div className={styles.filterOptions}>
                                {["봄", "여름", "가을", "겨울"].map(season => (
                                    <label key={season} className={`${styles.filterChip} ${selectedSeason === season ? styles.checked : ''}`}>
                                        <input
                                            type="radio"
                                            name="season"
                                            checked={selectedSeason === season}
                                            onChange={() => {
                                                if (selectedSeason === season) setSelectedSeason("");
                                                else setSelectedSeason(season);
                                            }}
                                            onClick={() => {
                                                if (selectedSeason === season) setSelectedSeason("");
                                            }}
                                        />
                                        {season}
                                    </label>
                                ))}
                            </div>
                        </div>

                        {/* ABV Filter */}
                        <div className={styles.filterGroup}>
                            <h4>도수</h4>
                            <div className={styles.filterOptions}>
                                {[
                                    { label: "순한 술 (~10%)", value: "low" },
                                    { label: "적당한 술 (10~20%)", value: "medium" },
                                    { label: "독한 술 (20%~)", value: "high" }
                                ].map(option => (
                                    <label key={option.value} className={`${styles.filterChip} ${selectedAbv === option.value ? styles.checked : ''}`}>
                                        <input
                                            type="radio"
                                            name="abv"
                                            checked={selectedAbv === option.value}
                                            onChange={() => {
                                                if (selectedAbv === option.value) setSelectedAbv("");
                                                else setSelectedAbv(option.value);
                                            }}
                                            onClick={() => {
                                                if (selectedAbv === option.value) setSelectedAbv("");
                                            }}
                                        />
                                        {option.label}
                                    </label>
                                ))}
                            </div>
                        </div>
                    </div>


                    <div className={styles.filterActions}>
                        <button onClick={() => { setSelectedTypes([]); setSelectedRegions([]); setSelectedSeason(""); setSelectedAbv(""); }} className={styles.resetFilter}>
                            필터 초기화 ⟳
                        </button>
                    </div>
                </div>
            </div>

            <div className={styles.filterBar}>
                <div className={styles.resultCount}>
                    총 <span className={styles.countNumber}>{totalCount}</span>개의 전통주
                    {query && <span className={styles.queryTag}>'{query}' 검색 결과</span>}
                </div>
                <div className={styles.sortOptions}>
                    <select
                        value={sort}
                        onChange={(e) => setSort(e.target.value)}
                        className={styles.sortSelect}
                    >
                        <option value="price_desc">높은 가격순</option>
                        <option value="price_asc">낮은 가격순</option>
                        <option value="alcohol_desc">높은 도수순</option>
                        <option value="alcohol_asc">낮은 도수순</option>
                        <option value="name_asc">가나다순</option>
                    </select>
                </div>
            </div>

            <div className={styles.grid}>
                {drinks.map((drink) => (
                    <div
                        key={`${drink.id}-${drink.name}`}
                        className={styles.card}
                        onClick={() => window.location.href = `/drink/${drink.id}`}
                    >
                        <div className={styles.imageWrapper}>
                            {drink.image_url ? (
                                <Image
                                    src={`/api/image-proxy?url=${encodeURIComponent(drink.image_url)}`}
                                    alt={drink.name}
                                    fill
                                    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                                    className={styles.image}
                                    style={{ objectFit: "cover" }}
                                    unoptimized={true}
                                />
                            ) : (
                                <div className={styles.placeholder}>🍶</div>
                            )}
                        </div>
                        <div className={styles.info}>
                            <div className={styles.meta}>{drink.type} | {drink.alcohol} | {drink.volume}</div>
                            <h3 className={styles.name}>{drink.name}</h3>
                            <div className={styles.brewery}>{drink.province} {drink.city}</div>
                            <div className={styles.price}>
                                {drink.price > 0 ? (
                                    <>
                                        <span className={styles.priceLabel}>최저가</span>
                                        {drink.price.toLocaleString()}원
                                    </>
                                ) : (
                                    <span className={styles.noPrice}>가격 정보 없음</span>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {loading && <div className={styles.loading}>불러오는 중... 🍶</div>}

            {/* Numbered Pagination */}
            {
                !loading && totalCount > 0 && (
                    <div className={styles.pagination}>
                        {(() => {
                            const pageSize = 24; // Must match fetchData size
                            const totalPages = Math.ceil(totalCount / pageSize);
                            const pageGroupSize = 5;
                            const currentGroup = Math.ceil(page / pageGroupSize);
                            const startPage = (currentGroup - 1) * pageGroupSize + 1;
                            const endPage = Math.min(startPage + pageGroupSize - 1, totalPages);

                            return (
                                <>
                                    {startPage > 1 && (
                                        <button
                                            className={styles.pageButton}
                                            onClick={() => handlePageChange(startPage - 1)}
                                        >
                                            &lt;&lt;
                                        </button>
                                    )}
                                    <button
                                        className={styles.pageButton}
                                        onClick={() => handlePageChange(Math.max(1, page - 1))}
                                        disabled={page === 1}
                                    >
                                        &lt;
                                    </button>

                                    {Array.from({ length: endPage - startPage + 1 }, (_, i) => startPage + i).map((pageNum) => (
                                        <button
                                            key={pageNum}
                                            className={`${styles.pageButton} ${page === pageNum ? styles.activePage : ''}`}
                                            onClick={() => handlePageChange(pageNum)}
                                        >
                                            {pageNum}
                                        </button>
                                    ))}

                                    <button
                                        className={styles.pageButton}
                                        onClick={() => handlePageChange(Math.min(totalPages, page + 1))}
                                        disabled={page === totalPages}
                                    >
                                        &gt;
                                    </button>
                                    {endPage < totalPages && (
                                        <button
                                            className={styles.pageButton}
                                            onClick={() => handlePageChange(endPage + 1)}
                                        >
                                            &gt;&gt;
                                        </button>
                                    )}
                                </>
                            );
                        })()}
                    </div>
                )
            }

            {
                !loading && !hasMore && drinks.length > 0 && (
                    <div className={styles.endMessage}>모든 술을 다 보셨어요! 🥂</div>
                )
            }

            {
                !loading && drinks.length === 0 && (
                    <div className={styles.emptyState}>
                        <p>검색 결과가 없습니다.</p>
                        <button onClick={() => setQuery("")} className={styles.resetButton}>전체 목록 보기</button>
                    </div>
                )
            }
        </div >
    );
}
