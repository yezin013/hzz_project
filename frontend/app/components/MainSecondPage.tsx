"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { getApiUrl } from "@/lib/api";
import styles from './MainSecondPage.module.css';

interface Cocktail {
    cocktail_id: number;
    cocktail_title: string;
    cocktail_image_url?: string;
    cocktail_homepage_url?: string;
}

interface Fair {
    fair_id: number;
    fair_year: number;
    fair_image_url: string;
    fair_homepage_url: string;
}

interface Brewery {
    name: string;
    address: string;
    region: string;
    contact: string;
    homepage: string;
}

export default function MainSecondPage() {
    const [cocktails, setCocktails] = useState<Cocktail[]>([]);
    const [fairs, setFairs] = useState<Fair[]>([]);
    const [breweries, setBreweries] = useState<Brewery[]>([]);
    const [loading, setLoading] = useState(false);

    // Fetch initial random cocktails
    const fetchCocktails = async () => {
        if (loading) return;
        setLoading(true);
        try {
            const res = await fetch(getApiUrl("/cocktail/random?limit=10"));
            if (!res.ok) {
                console.error("Fetch failed:", res.status, res.statusText);
                setCocktails([]);
                return;
            }
            const data = await res.json();
            if (Array.isArray(data)) {
                setCocktails(data);
            } else {
                console.error("Data is not an array:", data);
                setCocktails([]);
            }
        } catch (error) {
            console.error("Failed to fetch cocktails:", error);
            setCocktails([]);
        } finally {
            setLoading(false);
        }
    };

    // Fetch random breweries
    const fetchBreweries = async () => {
        try {
            const res = await fetch(getApiUrl("/brewery/random?limit=10"));
            if (!res.ok) {
                console.error("Brewery fetch failed:", res.status);
                setBreweries([]);
                return;
            }
            const data = await res.json();
            if (Array.isArray(data)) {
                setBreweries(data);
            } else {
                console.error("Brewery data is not an array:", data);
                setBreweries([]);
            }
        } catch (error) {
            console.error("Failed to fetch breweries:", error);
            setBreweries([]);
        }
    };

    // Hardcoded Fair Data using local images
    const hardcodedFairs: Fair[] = [
        {
            fair_id: 1,
            fair_year: 2024,
            fair_image_url: "/sool_award/2024품평회.PNG",
            fair_homepage_url: "https://thesool.com/front/publication/M000000090/view.do?bbsId=A000000050&publicationId=C000003159&page=&searchKey=&searchString=&searchCategory="
        },
        {
            fair_id: 2,
            fair_year: 2023,
            fair_image_url: "/sool_award/2023.PNG",
            fair_homepage_url: "https://thesool.com/front/publication/M000000090/view.do?bbsId=A000000050&publicationId=C000002964&page=&searchKey=&searchString=&searchCategory="
        },
        {
            fair_id: 3,
            fair_year: 2022,
            fair_image_url: "/sool_award/2022.PNG",
            fair_homepage_url: "https://thesool.com/front/publication/M000000090/view.do?bbsId=A000000050&publicationId=C000002724&page=&searchKey=&searchString=&searchCategory="
        }
    ];

    // Initialize data
    useEffect(() => {
        setFairs(hardcodedFairs);
        fetchCocktails();
        fetchBreweries();
    }, []);

    return (
        <div className={styles.container}>
            {/* Left: Cocktail List */}
            <div className={styles.leftSection}>
                <h2 className={styles.sectionTitle}>
                    <span className={styles.titleIcon}>🍸</span>
                    오늘의 칵테일 추천
                </h2>

                <div className={styles.cocktailList}>
                    {cocktails.slice(0, 8).map((cocktail, idx) => (
                        <div
                            key={cocktail.cocktail_id}
                            className={styles.cocktailItem}
                            onClick={() => {
                                if (cocktail.cocktail_homepage_url) {
                                    window.open(cocktail.cocktail_homepage_url, '_blank');
                                }
                            }}
                        >
                            <div className={styles.cocktailNumber}>{idx + 1}</div>
                            <div className={styles.cocktailName}>{cocktail.cocktail_title}</div>
                            <div className={styles.cocktailArrow}>→</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Middle: Award Winners */}
            <div className={styles.middleSection}>
                <h2 className={styles.sectionTitle}>
                    <span className={styles.titleIcon}>🏆</span>
                    우리술 품평회 수상작
                </h2>

                <div className={styles.awardList}>
                    {fairs.map((fair) => (
                        <div
                            key={fair.fair_id}
                            className={styles.awardItem}
                            onClick={() => {
                                if (fair.fair_homepage_url) {
                                    window.open(fair.fair_homepage_url, '_blank');
                                }
                            }}
                        >
                            <div className={styles.awardImageWrapper}>
                                <Image
                                    src={fair.fair_image_url}
                                    alt={`${fair.fair_year} 우리술 품평회`}
                                    fill
                                    sizes="400px"
                                    style={{ objectFit: 'contain' }}
                                />
                            </div>
                            <div className={styles.awardYear}>{fair.fair_year}</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Right: Brewery List */}
            <div className={styles.rightSection}>
                <h2 className={styles.sectionTitle}>
                    <span className={styles.titleIcon}>🏭</span>
                    전통 양조장
                </h2>

                <div className={styles.breweryList}>
                    {breweries.map((brewery, idx) => (
                        <div
                            key={idx}
                            className={styles.breweryItem}
                            onClick={() => {
                                if (brewery.homepage) {
                                    window.open(brewery.homepage, '_blank');
                                }
                            }}
                        >
                            <div className={styles.breweryNumber}>{idx + 1}</div>
                            <div className={styles.breweryInfo}>
                                <div className={styles.breweryName}>{brewery.name}</div>
                                <div className={styles.breweryRegion}>📍 {brewery.region}</div>
                            </div>
                            <div className={styles.breweryArrow}>→</div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
