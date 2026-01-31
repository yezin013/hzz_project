import { useState, useRef, useEffect } from "react";
import styles from "./HeroSection.module.css";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";

interface HeroSectionProps {
    onSearch: (query: string) => void;
    onScrollDown: () => void;
}

export default function HeroSection({ onSearch, onScrollDown }: HeroSectionProps) {
    const router = useRouter();
    const [query, setQuery] = useState("");
    const videoRef = useRef<HTMLVideoElement>(null);

    // Search State
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [showDropdown, setShowDropdown] = useState(false);
    const searchTimeout = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
        if (videoRef.current) {
            videoRef.current.playbackRate = 0.8;
        }
    }, []);

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setQuery(value);

        if (searchTimeout.current) clearTimeout(searchTimeout.current);

        if (value.length > 1) {
            searchTimeout.current = setTimeout(async () => {
                try {
                    const data = await api.search.search(value);
                    if (data && data.candidates) {
                        setSearchResults(data.candidates);
                        setShowDropdown(true);
                    } else if (data && data.name) {
                        setSearchResults([{
                            name: data.name,
                            id: 999, // Fallback ID if not provided directly
                            image_url: data.image_url
                        }]);
                        setShowDropdown(true);
                    }
                } catch (err) {
                    console.error("Search failed", err);
                }
            }, 300);
        } else {
            setShowDropdown(false);
        }
    };

    const handleSelectDrink = (drink: any) => {
        // If the drink has an ID, navigate to it. Otherwise just run standard search.
        if (drink.id && drink.id !== 999) {
            router.push(`/drink/${drink.id}`);
        } else {
            onSearch(drink.name);
        }
        setShowDropdown(false);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter") {
            onSearch(query);
            setShowDropdown(false);
        }
    };

    return (
        <section className={styles.heroSection}>
            {/* Background Video */}
            <div className={styles.videoContainer}>
                <div className={styles.overlay} />
                <video
                    ref={videoRef}
                    autoPlay
                    muted
                    loop
                    playsInline
                    className={styles.video}
                >
                    <source src="/main_background.mp4" type="video/mp4" />
                    Your browser does not support the video tag.
                </video>
            </div>

            {/* Main Content */}
            <div className={styles.content}>
                <div className={styles.titleWrapper}>
                    <h2 className={styles.subTitle}>우리 술의 맛과 멋을 찾아서</h2>
                    <h1 className={styles.mainTitle}>전통주 대동여지도</h1>
                </div>

                {/* Glassmorphism Search Bar */}
                <div className={styles.searchWrapper}>
                    <div className={styles.searchBar} style={{ position: 'relative' }}>
                        <span className={styles.searchIcon}>🔍</span>
                        <input
                            type="text"
                            placeholder="어떤 술을 찾으시나요?"
                            value={query}
                            onChange={handleSearchChange}
                            onKeyDown={handleKeyDown}
                            className={styles.searchInput}
                            onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
                            onFocus={() => { if (query.length > 1 && searchResults.length > 0) setShowDropdown(true); }}
                        />
                        <button
                            className={styles.searchButton}
                            onClick={() => onSearch(query)}
                        >
                            검색
                        </button>
                    </div>

                    {/* Autocomplete Dropdown */}
                    {showDropdown && searchResults.length > 0 && (
                        <ul className={styles.autocompleteDropdown}>
                            {searchResults.map((item, idx) => (
                                <li key={idx} onClick={() => handleSelectDrink(item)} className={styles.autocompleteItem}>
                                    {item.image_url ? (
                                        <img src={item.image_url} alt="" />
                                    ) : (
                                        <div style={{ width: 40, height: 40, background: '#eee', borderRadius: 6 }} />
                                    )}
                                    <span>{item.name}</span>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </div>

            {/* Scroll Indicator */}
            <div className={styles.scrollIndicator} onClick={onScrollDown}>
                <div className={styles.mouse}>
                    <div className={styles.wheel} />
                </div>
                <div className={styles.arrow} />
                <div className={styles.scrollText}>내려보기</div>
            </div>
        </section>
    );
}
