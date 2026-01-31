"use client";

import { useState, useEffect, Suspense, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { getApiUrl } from "@/lib/api";
import styles from "./page.module.css";

interface Drink {
    id: number;
    name: string;
    image_url?: string;
    type: string;
    alcohol?: string;
    volume?: string;
    price: number;
    intro?: string;
    pairing_foods?: string[];
    selling_shops?: any[];
}

interface DrinkListResponse {
    drinks: Drink[];
    total: number;
    page: number;
    size: number;
    total_pages: number;
}

interface AutocompleteItem {
    id: number;
    name: string;
    image_url: string;
    score: number;
}

function InfoContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [drinks, setDrinks] = useState<Drink[]>([]);
    const [loading, setLoading] = useState(true);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [total, setTotal] = useState(0);
    const [searchQuery, setSearchQuery] = useState("");
    const [searchInput, setSearchInput] = useState("");

    // Autocomplete state
    const [autocompleteResults, setAutocompleteResults] = useState<AutocompleteItem[]>([]);
    const [showAutocomplete, setShowAutocomplete] = useState(false);
    const searchTimeout = useRef<NodeJS.Timeout | null>(null);

    const fetchDrinks = async (page: number = 1, query: string = "") => {
        setLoading(true);
        try {
            const url = getApiUrl(`/search/list?page=${page}&size=15${query ? `&query=${encodeURIComponent(query)}` : ''}`);
            const response = await fetch(url);
            if (response.ok) {
                const data: DrinkListResponse = await response.json();
                setDrinks(data.drinks);
                setCurrentPage(data.page);
                setTotalPages(data.total_pages);
                setTotal(data.total);
            } else {
                console.error("Failed to fetch drinks");
                setDrinks([]);
            }
        } catch (error) {
            console.error("Error fetching drinks:", error);
            setDrinks([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const page = parseInt(searchParams.get('page') || '1', 10);
        const query = searchParams.get('q') || '';
        setSearchInput(query);
        setCurrentPage(page);
        fetchDrinks(page, query);
    }, [searchParams]);

    // Autocomplete handler with debounce
    const handleSearchInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const query = e.target.value;
        setSearchInput(query);

        if (searchTimeout.current) clearTimeout(searchTimeout.current);

        if (query.length > 1) {
            searchTimeout.current = setTimeout(async () => {
                try {
                    const res = await fetch(getApiUrl("/search"), {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ query })
                    });
                    if (res.ok) {
                        const data = await res.json();
                        if (data?.candidates) {
                            setAutocompleteResults(data.candidates);
                            setShowAutocomplete(true);
                        }
                    }
                } catch (err) {
                    console.error("Autocomplete search failed", err);
                }
            }, 300);
        } else {
            setShowAutocomplete(false);
        }
    };

    const selectLiquor = (liquor: AutocompleteItem) => {
        router.push(`/drink/${liquor.id}`);
        setSearchInput("");
        setShowAutocomplete(false);
    };

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        const query = searchInput.trim();
        setCurrentPage(1);
        setShowAutocomplete(false);
        router.push(`/info?page=1${query ? `&q=${encodeURIComponent(query)}` : ''}`);
    };

    const handlePageChange = (page: number) => {
        const query = searchParams.get('q') || '';
        router.push(`/info?page=${page}${query ? `&q=${encodeURIComponent(query)}` : ''}`);
    };

    return (
        <div className={styles.container}>
            <div className={styles.background}>
                <Image
                    src="/jumak.png"
                    alt="Jumak Background"
                    fill
                    quality={100}
                    sizes="100vw"
                    style={{ objectFit: "cover", objectPosition: "center" }}
                    priority
                />
                <div className={styles.overlay} />
            </div>

            <div className={styles.content}>
                <div className={styles.titleSection}>
                    <div className={styles.titleIcon}>🍶</div>
                    <h1 className={styles.title}>전통주 정보 찾기</h1>
                </div>

                <form onSubmit={handleSearch} className={styles.searchForm} style={{ position: 'relative' }}>
                    <input
                        type="text"
                        value={searchInput}
                        onChange={handleSearchInputChange}
                        placeholder="전통주 이름을 검색해보세요..."
                        className={styles.searchInput}
                    />
                    <button type="submit" className={styles.searchButton}>
                        검색
                    </button>

                    {/* Autocomplete Dropdown */}
                    {showAutocomplete && autocompleteResults.length > 0 && (
                        <ul className={styles.autocompleteDropdown}>
                            {autocompleteResults.map((item, idx) => (
                                <li
                                    key={idx}
                                    onClick={() => selectLiquor(item)}
                                    className={styles.autocompleteItem}
                                >
                                    {item.image_url ? (
                                        <img
                                            src={`/api/image-proxy?url=${encodeURIComponent(item.image_url)}`}
                                            alt=""
                                            style={{
                                                width: 40,
                                                height: 40,
                                                marginRight: 12,
                                                borderRadius: 6,
                                                objectFit: 'cover'
                                            }}
                                        />
                                    ) : (
                                        <span
                                            style={{
                                                width: 40,
                                                height: 40,
                                                marginRight: 12,
                                                borderRadius: 6,
                                                background: '#eee',
                                                display: 'inline-block'
                                            }}
                                        />
                                    )}
                                    <span style={{ flex: 1 }}>{item.name}</span>
                                    <span style={{ fontSize: '0.75rem', color: '#999', marginLeft: 10 }}>
                                        {item.score.toFixed(1)}
                                    </span>
                                </li>
                            ))}
                        </ul>
                    )}
                </form>

                {loading ? (
                    <div className={styles.loading}>불러오는 중... 🍶</div>
                ) : (
                    <>
                        <div className={styles.resultInfo}>
                            총 {total.toLocaleString()}개의 전통주
                        </div>

                        {drinks.length > 0 ? (
                            <>
                                <div className={styles.drinkGrid}>
                                    {drinks.map((drink) => (
                                        <Link
                                            href={`/drink/${drink.id}`}
                                            key={drink.id}
                                            className={styles.drinkCard}
                                        >
                                            <div className={styles.drinkImageContainer}>
                                                {drink.image_url ? (
                                                    <Image
                                                        src={`/api/image-proxy?url=${encodeURIComponent(drink.image_url)}`}
                                                        alt={drink.name}
                                                        fill
                                                        style={{ objectFit: "contain" }}
                                                        sizes="300px"
                                                        unoptimized={true}
                                                    />
                                                ) : (
                                                    <div className={styles.placeholderImage}>🍶</div>
                                                )}
                                            </div>
                                            <div className={styles.drinkInfo}>
                                                <h3 className={styles.drinkName}>{drink.name}</h3>
                                                <div className={styles.drinkMeta}>
                                                    {drink.type && (
                                                        <span className={styles.drinkType}>{drink.type}</span>
                                                    )}
                                                    {drink.alcohol && (
                                                        <span className={styles.drinkAlcohol}>{drink.alcohol}</span>
                                                    )}
                                                </div>
                                                {drink.price > 0 ? (
                                                    <div className={styles.drinkPrice}>{drink.price.toLocaleString()}원</div>
                                                ) : (
                                                    <div className={styles.drinkPriceNoInfo}>가격 정보 없음</div>
                                                )}
                                            </div>
                                        </Link>
                                    ))}
                                </div>

                                {totalPages > 1 && (
                                    <div className={styles.pagination}>
                                        <button
                                            onClick={() => handlePageChange(currentPage - 1)}
                                            disabled={currentPage === 1}
                                            className={styles.pageButton}
                                        >
                                            이전
                                        </button>
                                        <div className={styles.pageNumbers}>
                                            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                                                let pageNum;
                                                if (totalPages <= 5) {
                                                    pageNum = i + 1;
                                                } else if (currentPage <= 3) {
                                                    pageNum = i + 1;
                                                } else if (currentPage >= totalPages - 2) {
                                                    pageNum = totalPages - 4 + i;
                                                } else {
                                                    pageNum = currentPage - 2 + i;
                                                }
                                                return (
                                                    <button
                                                        key={pageNum}
                                                        onClick={() => handlePageChange(pageNum)}
                                                        className={`${styles.pageButton} ${currentPage === pageNum ? styles.active : ''}`}
                                                    >
                                                        {pageNum}
                                                    </button>
                                                );
                                            })}
                                        </div>
                                        <button
                                            onClick={() => handlePageChange(currentPage + 1)}
                                            disabled={currentPage === totalPages}
                                            className={styles.pageButton}
                                        >
                                            다음
                                        </button>
                                    </div>
                                )}
                            </>
                        ) : (
                            <div className={styles.noResults}>
                                <p>검색 결과가 없습니다.</p>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}

export default function InfoPage() {
    return (
        <Suspense fallback={
            <div className={styles.container}>
                <div className={styles.background}>
                    <Image
                        src="/jumak.png"
                        alt="Jumak Background"
                        fill
                        quality={100}
                        sizes="100vw"
                        style={{ objectFit: "cover", objectPosition: "center" }}
                        priority
                    />
                    <div className={styles.overlay} />
                </div>
                <div className={styles.content}>
                    <div className={styles.loading}>불러오는 중... 🍶</div>
                </div>
            </div>
        }>
            <InfoContent />
        </Suspense>
    );
}
