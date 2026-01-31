"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { getApiUrl } from "@/lib/api";
import styles from "./RealTimeSearchRanking.module.css";

interface SearchRank {
  query: string;
  count: number;
  drink_id?: number;
}

interface AutocompleteItem {
  id: number;
  name: string;
  image_url: string;
  score: number;
}

export default function RealTimeSearchRanking() {
  const [topSearches, setTopSearches] = useState<SearchRank[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isHovered, setIsHovered] = useState(false);
  const [loading, setLoading] = useState(true);

  // Autocomplete state
  const [searchQuery, setSearchQuery] = useState("");
  const [autocompleteResults, setAutocompleteResults] = useState<AutocompleteItem[]>([]);
  const [showAutocomplete, setShowAutocomplete] = useState(false);
  const searchTimeout = useRef<NodeJS.Timeout | null>(null);

  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);

  // Top10 검색어 가져오기
  const fetchTopSearches = async () => {
    try {
      setLoading(true);
      const response = await fetch(getApiUrl("/search/top-searches?limit=10"));
      if (response.ok) {
        const data = await response.json();
        setTopSearches(data.top_searches || []);
      }
    } catch (error) {
      console.error("Failed to fetch top searches:", error);
    } finally {
      setLoading(false);
    }
  };

  // 초기 로드 및 주기적 업데이트
  useEffect(() => {
    fetchTopSearches();
    const interval = setInterval(fetchTopSearches, 60000); // 1분마다 업데이트
    return () => clearInterval(interval);
  }, []);

  // 순환 표시 (1-10등 반복)
  useEffect(() => {
    if (topSearches.length === 0 || isHovered) return;

    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % topSearches.length);
    }, 3000); // 3초마다 변경

    return () => clearInterval(timer);
  }, [topSearches.length, isHovered]);

  const handleSearchClick = (search: SearchRank) => {
    // drink_id가 있으면 상세 페이지로, 없으면 검색 페이지로
    if (search.drink_id) {
      router.push(`/drink/${search.drink_id}`);
    } else {
      router.push(`/info?q=${encodeURIComponent(search.query)}`);
    }
  };

  // Autocomplete search handler with debounce
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);

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
    setSearchQuery("");
    setShowAutocomplete(false);
  };

  // 마우스가 container 영역 밖으로 나갔는지 확인
  const handleMouseLeave = (e: React.MouseEvent) => {
    // 관련된 요소(container 또는 fullList)로 이동했는지 확인
    const relatedTarget = e.relatedTarget as Node;
    if (containerRef.current && !containerRef.current.contains(relatedTarget)) {
      setIsHovered(false);
    }
  };

  // 데이터가 없어도 컴포넌트는 표시 (로딩 상태)
  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.label}>실시간 검색어</div>
        <div className={styles.currentItem}>
          <span className={styles.query} style={{ fontSize: '0.85rem', color: '#999' }}>로딩 중...</span>
        </div>
      </div>
    );
  }

  if (topSearches.length === 0) {
    return (
      <div className={styles.container}>
        <div className={styles.label}>실시간 검색어</div>
        <div className={styles.currentItem}>
          <span className={styles.query} style={{ fontSize: '0.85rem', color: '#999' }}>검색 데이터 없음</span>
        </div>
      </div>
    );
  }

  const currentSearch = topSearches[currentIndex];

  return (
    <div
      ref={containerRef}
      className={styles.container}
    >
      <div className={styles.label}>실시간 검색어</div>

      {/* Scroll Wrapper - Only this part unfurls */}
      <div
        className={styles.scrollWrapper}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={handleMouseLeave}
      >
        {!isHovered ? (
          // 기본: 현재 순위만 표시
          <div className={styles.currentItem}>
            <span className={styles.rank}>{currentIndex + 1}</span>
            <span
              className={styles.query}
              onClick={() => handleSearchClick(currentSearch)}
              title={currentSearch.query}
            >
              {currentSearch.query}
            </span>
          </div>
        ) : (
          // 호버: 전체 Top10 표시
          <div className={styles.fullList}>
            {topSearches.map((search, index) => (
              <div
                key={index}
                className={`${styles.rankItem} ${index === currentIndex ? styles.active : ""}`}
                onClick={() => handleSearchClick(search)}
                title={search.query}
              >
                <span className={styles.rankNumber}>{index + 1}</span>
                <span className={styles.queryText}>{search.query}</span>
                <span className={styles.count}>({search.count})</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
