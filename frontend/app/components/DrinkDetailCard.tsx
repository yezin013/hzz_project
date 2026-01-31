"use client";

import Image from "next/image";
import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { getApiUrl, api } from "@/lib/api";
import styles from "./DrinkDetailCard.module.css";
import LoadingSpinner from "./LoadingSpinner";
import TasteRadarChart from "./TasteRadarChart";
import { Bookmark } from "lucide-react";

interface Cocktail {
    cocktail_title: string;
    cocktail_base: string;
    cocktail_garnish: string;
    cocktail_recipe: string;
    cocktail_image_url?: string;
    youtube_video_id?: string;
    youtube_video_title?: string;
    youtube_thumbnail_url?: string;
}

interface SimilarDrink {
    id: number;
    name: string;
    image_url?: string;
    score: number;
}

interface OnlineProduct {
    name: string;
    price: number;
    shop: string;
    url: string;
    image_url: string;
}

interface HansangItem {
    name: string;
    image_url?: string;
    reason: string;
    link_url?: string;
    specialty_used?: string;  // Which specialty product was used
}

export interface DrinkDetail {
    id?: number;
    name: string;
    description: string;
    intro?: string;
    image_url?: string;
    url?: string;
    abv?: string;
    volume?: string;
    type?: string;
    province?: string;
    city?: string;
    tags?: string[];
    foods?: string[];
    pairing_food?: string[];
    cocktails?: Cocktail[];
    encyclopedia?: {
        title: string;
        text: string;
        images?: { src: string; alt: string; }[];
    }[];
    selling_shops?: {
        shop_id: number;
        name: string;
        address: string;
        contact: string;
        url: string;
        price: number;
    }[];
    brewery?: {
        name?: string;
        address?: string;
        homepage?: string;
        contact?: string;
    };
    detail?: {
        알콜도수?: string;
        용량?: string;
        종류?: string;
        원재료?: string;
        수상내역?: string;
    };
    candidates?: any[];
    score?: number;
    // NEW: Encyclopedia price fields
    price_is_reference?: boolean;
    encyclopedia_price_text?: string;
    encyclopedia_url?: string;
    // NEW: Taste profile data
    taste?: {
        sweetness: number;
        sourness: number;
        freshness: number;
        body: number;
        balance: number;
        aroma: number;
    };
}

interface DrinkDetailCardProps {
    drink: DrinkDetail;
    isOCR?: boolean;
    onGenerateCocktail?: (name: string) => void;
    generatedFood?: { name: string, reason: string } | null;
    generatedCocktails?: Cocktail[];
    isGeneratingCocktail?: boolean;
    onGenerateHansang?: (province: string, city: string) => void;
    generatedHansang?: HansangItem[];
    isGeneratingHansang?: boolean;
}

type TabType = 'food' | 'cocktail' | 'hansang';

export default function DrinkDetailCard({
    drink,
    isOCR = false,
    onGenerateCocktail,
    generatedFood,
    generatedCocktails = [],
    isGeneratingCocktail = false,
    onGenerateHansang,
    generatedHansang = [],
    isGeneratingHansang = false
}: DrinkDetailCardProps) {

    // Normalize data
    const foods = drink.foods || drink.pairing_food || [];
    const intro = drink.intro || drink.description;
    const abv = drink.abv || drink.detail?.알콜도수;
    const volume = drink.volume || drink.detail?.용량;
    const type = drink.type || drink.detail?.종류;

    // Tab state
    const [activeTab, setActiveTab] = useState<TabType>('food');

    // Similar Drinks State
    const [similarDrinks, setSimilarDrinks] = useState<SimilarDrink[]>([]);

    // AI Recommendations State
    const [currentCocktailIndex, setCurrentCocktailIndex] = useState(0);

    const nextCocktail = () => {
        if (generatedCocktails.length > 0) {
            setCurrentCocktailIndex((prev) => (prev + 1) % generatedCocktails.length);
        }
    };

    const prevCocktail = () => {
        if (generatedCocktails.length > 0) {
            setCurrentCocktailIndex((prev) => (prev - 1 + generatedCocktails.length) % generatedCocktails.length);
        }
    };



    // Favorite State
    const { data: session } = useSession();
    const [isFavorited, setIsFavorited] = useState(false);
    const [isTogglingFavorite, setIsTogglingFavorite] = useState(false);

    // Check if drink is favorited on mount
    useEffect(() => {
        if (drink.id) {
            // const userId = (session?.user as any)?.id || session?.user?.email;
            const userId = (session?.user as any)?.id || session?.user?.email || "anonymous_user";
            if (userId) {
                api.favorites.check(userId, drink.id)
                    .then(data => setIsFavorited(data.is_favorited))
                    .catch(err => console.error("Failed to check favorite:", err));
            }
        }
    }, [session, drink.id]);

    // Toggle favorite handler
    const handleToggleFavorite = async () => {
        if (!drink.id) return;
        // if (!session?.user || !drink.id) return;

        // const userId = (session.user as any).id || session.user.email;
        const userId = (session?.user as any)?.id || session?.user?.email || "anonymous_user";
        if (!userId) return;

        setIsTogglingFavorite(true);
        try {
            const result = await api.favorites.toggle(
                userId,
                drink.id,
                drink.name,
                drink.image_url
            );
            setIsFavorited(result.is_favorited);
        } catch (err) {
            console.error("Failed to toggle favorite:", err);
        } finally {
            setIsTogglingFavorite(false);
        }
    };

    // Online Products State
    const [onlineData, setOnlineData] = useState<{ products: OnlineProduct[], count: number } | null>(null);

    // Fetch online products
    useEffect(() => {
        if (drink.name) {
            api.search.getProducts(drink.name)
                .then(data => setOnlineData(data))
                .catch(err => console.error("Failed to fetch products:", err));
        }
    }, [drink.name]);

    useEffect(() => {
        if (drink.name) {
            fetch(getApiUrl('/search/similar'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: drink.name,
                    exclude_id: drink.id || null  // Explicitly set null if undefined
                })
            })
                .then(res => res.json())
                .then(data => {
                    if (Array.isArray(data)) {
                        setSimilarDrinks(data);
                    }
                })
                .catch(err => console.error("Failed to fetch similar drinks:", err));
        }
    }, [drink.name, drink.id]);

    return (
        <div className={styles.card}>

            {/* BENTO GRID HERO SECTION */}
            <section className={styles.heroGrid}>

                {/* Left Column: Image Card (Transparent) */}
                {/* Left Column: Image Card */}
                <div className={styles.imageColumn}>
                    {/* Image Wrapper with CSS-controlled height for mobile consistency */}
                    {drink.image_url ? (
                        <div className={styles.imageWrapper}>
                            {isOCR && (
                                <div style={{
                                    position: 'absolute',
                                    top: '10px',
                                    left: '10px',
                                    background: 'rgba(0,0,0,0.6)',
                                    color: 'white',
                                    padding: '4px 8px',
                                    borderRadius: '4px',
                                    fontSize: '0.8rem',
                                    zIndex: 10
                                }}>
                                    🔍 OCR 인식됨
                                </div>
                            )}
                            <Image
                                src={`/api/image-proxy?url=${encodeURIComponent(drink.image_url)}`}
                                alt={drink.name}
                                fill
                                style={{ objectFit: 'contain' }}
                                sizes="(max-width: 768px) 100vw, 400px"
                                unoptimized={true}
                                priority
                            />
                        </div>
                    ) : (
                        <div className={styles.imageWrapper} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f8f9fa' }}>
                            <span style={{ fontSize: '2rem' }}>🍶</span>
                        </div>
                    )}

                    {drink.url && (
                        <a href={drink.url} target="_blank" rel="noopener noreferrer" className={styles.moreInfoButton} style={{ width: '100%', marginTop: '10px' }}>
                            더 자세한 정보 보기
                        </a>
                    )}
                </div>

                {/* Right Column: Content Stack */}
                <div className={styles.contentColumn}>

                    {/* Row 1: Header (Refactored for Cleaner Look) */}
                    <div style={{
                        padding: '10px 0',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        gap: '12px'
                    }}>
                        {/* 1. Top Badges (Type & Region) */}
                        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                            {type && (
                                <span style={{
                                    background: '#3e2723',
                                    color: '#fff',
                                    padding: '4px 10px',
                                    borderRadius: '6px',
                                    fontSize: '0.85rem',
                                    fontWeight: '600',
                                    letterSpacing: '0.5px'
                                }}>
                                    {type}
                                </span>
                            )}
                            {(drink.province || drink.city) && (
                                <span style={{
                                    background: '#f5f5f5',
                                    color: '#5d4037',
                                    padding: '4px 10px',
                                    borderRadius: '6px',
                                    fontSize: '0.85rem',
                                    fontWeight: '600',
                                    border: '1px solid #e0e0e0'
                                }}>
                                    📍 {drink.province}{drink.city ? ` ${drink.city}` : ''}
                                </span>
                            )}
                        </div>

                        {/* 2. Main Title & Favorite */}
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '10px' }}>
                            <h2 style={{
                                fontSize: '2.4rem',
                                fontWeight: '800',
                                margin: 0,
                                color: '#222',
                                lineHeight: '1.2',
                                wordBreak: 'keep-all'
                            }}>
                                {drink.name}
                            </h2>

                            {/* Favorite Button (Compact) */}
                            {drink.id && (
                                <button
                                    onClick={handleToggleFavorite}
                                    disabled={isTogglingFavorite}
                                    style={{
                                        background: isFavorited ? '#fff0f5' : '#f5f5f5',
                                        border: 'none',
                                        borderRadius: '50%',
                                        width: '44px',
                                        height: '44px',
                                        flexShrink: 0,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s ease'
                                    }}
                                >
                                    <Bookmark
                                        size={24}
                                        fill={isFavorited ? "#ff4081" : "none"}
                                        color={isFavorited ? "#ff4081" : "#aaa"}
                                    />
                                </button>
                            )}
                        </div>

                        {/* 3. Specs Row (ABV, Volume) */}
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '15px',
                            color: '#5d4037',
                            fontSize: '1rem',
                            fontWeight: '500',
                            marginTop: '5px'
                        }}>
                            {abv && (
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <span style={{ fontSize: '1.2rem' }}>💧</span>
                                    <span>{abv}</span>
                                </div>
                            )}
                            {abv && volume && <span style={{ color: '#ccc' }}>|</span>}
                            {volume && (
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <span style={{ fontSize: '1.2rem' }}>🧴</span>
                                    <span>{volume}</span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Row 2: Description & Brewery/Chart Grid */}
                    <div className={styles.descriptionGrid}>
                        {/* Left Column: Description Card */}
                        <div className={styles.descriptionCard}>
                            <h4 style={{ margin: '0 0 16px 0', color: '#1a1a1a', fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '800' }}>
                                📜 술 설명
                            </h4>
                            <p style={{ fontSize: '1rem', lineHeight: '1.7', color: '#4a4a4a', margin: 0, whiteSpace: 'pre-line' }}>
                                {intro}
                            </p>
                        </div>

                        {/* Right Column: Brewery & Taste Chart */}
                        <div className={styles.specsColumn}>

                            {/* Brewery Card */}
                            {drink.brewery && drink.brewery.name && (
                                <div style={{
                                    background: "#f8f9fa",
                                    borderRadius: '16px',
                                    padding: '24px',
                                    border: '1px solid #eee'
                                }}>
                                    <h4 style={{
                                        margin: '0 0 12px 0',
                                        color: '#2d3436',
                                        fontSize: '1rem',
                                        fontWeight: '800',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '8px'
                                    }}>
                                        🏭 양조장
                                    </h4>

                                    <div style={{ marginBottom: '10px' }}>
                                        <p style={{ margin: 0, fontWeight: '700', fontSize: '1.1rem', color: '#2d3436' }}>
                                            {drink.brewery.name}
                                        </p>
                                    </div>

                                    {drink.brewery.address && (
                                        <p style={{ margin: '0 0 8px 0', fontSize: '0.9rem', color: '#636e72', display: 'flex', gap: '6px' }}>
                                            <span>📍</span> {drink.brewery.address}
                                        </p>
                                    )}

                                    {drink.brewery.contact && (
                                        <p style={{ margin: '0 0 8px 0', fontSize: '0.9rem', color: '#636e72', display: 'flex', gap: '6px' }}>
                                            <span>📞</span> {drink.brewery.contact}
                                        </p>
                                    )}

                                    {drink.brewery.homepage && (
                                        <a href={drink.brewery.homepage} target="_blank" rel="noopener noreferrer" style={{ color: '#0984e3', textDecoration: 'none', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: '600', marginTop: '8px' }}>
                                            🌐 홈페이지 방문 →
                                        </a>
                                    )}
                                </div>
                            )}

                            {/* Taste Profile Radar Chart */}
                            {drink.taste && (
                                <div style={{
                                    background: "#ffffff",
                                    borderRadius: '16px',
                                    padding: '20px',
                                    border: '1px solid #ced4da',
                                    boxShadow: '0 4px 12px rgba(0,0,0,0.03)',
                                    height: '340px'
                                }}>
                                    <TasteRadarChart data={drink.taste} />
                                </div>
                            )}
                        </div>
                    </div>




                    {/* Details Grid */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
                        {drink.detail?.원재료 && (
                            <div style={{
                                background: "#fff",
                                border: '1px solid #f0f0f0',
                                padding: '24px',
                                borderRadius: '24px',
                                boxShadow: '0 10px 30px rgba(0,0,0,0.05)'
                            }}>
                                <h4 style={{ margin: '0 0 12px 0', color: '#5d4037', fontSize: '0.95rem', fontWeight: 'bold' }}>🌾 원재료</h4>
                                <p style={{ margin: 0, fontSize: '1rem', color: '#3e2723', lineHeight: '1.5' }}>{drink.detail.원재료}</p>
                            </div>
                        )}
                        {drink.detail?.수상내역 && (
                            <div style={{
                                background: "#fff",
                                border: '1px solid #f0f0f0',
                                padding: '24px',
                                borderRadius: '24px',
                                boxShadow: '0 10px 30px rgba(0,0,0,0.05)'
                            }}>
                                <h4 style={{ margin: '0 0 12px 0', color: '#5d4037', fontSize: '0.95rem', fontWeight: 'bold' }}>🏅 수상내역</h4>
                                <p style={{ margin: 0, fontSize: '0.95rem', color: '#3e2723', lineHeight: '1.5' }}>{drink.detail.수상내역}</p>
                            </div>
                        )}
                        {foods.length > 0 && (
                            <div style={{
                                background: "#fff",
                                border: '1px solid #f0f0f0',
                                padding: '24px',
                                borderRadius: '24px',
                                boxShadow: '0 10px 30px rgba(0,0,0,0.05)'
                            }}>
                                <h4 style={{ margin: '0 0 12px 0', color: '#5d4037', fontSize: '0.95rem', fontWeight: 'bold' }}>🥘 어울리는 음식</h4>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                                    {foods.map((food, idx) => (
                                        <span key={idx} style={{
                                            background: '#f5f5f5',
                                            border: 'none',
                                            color: '#5d4037',
                                            padding: '6px 12px',
                                            borderRadius: '20px',
                                            fontSize: '0.9rem',
                                            fontWeight: '600'
                                        }}>
                                            {food}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </section >

            {/* AI RECOMMENDATIONS TABS */}
            {
                (onGenerateCocktail || onGenerateHansang) && (
                    <section className={styles.aiTabs}>
                        <div className={styles.tabButtons}>
                            <button
                                className={activeTab === 'food' ? styles.active : ''}
                                onClick={() => setActiveTab('food')}
                            >
                                🍽️ AI 안주 추천
                            </button>
                            <button
                                className={activeTab === 'cocktail' ? styles.active : ''}
                                onClick={() => setActiveTab('cocktail')}
                            >
                                🍹 AI 칵테일
                            </button>
                            {drink.province && onGenerateHansang && (
                                <button
                                    className={activeTab === 'hansang' ? styles.active : ''}
                                    onClick={() => setActiveTab('hansang')}
                                >
                                    🍚 지역 한상차림
                                </button>
                            )}
                        </div>

                        <div className={styles.tabContent}>
                            {/* AI Food Tab */}
                            {activeTab === 'food' && (
                                <div className={styles.fadeInUp}>
                                    {isGeneratingCocktail ? (
                                        <LoadingSpinner theme="food" message="AI가 안주 추천 중" />
                                    ) : generatedFood ? (
                                        <div>
                                            <div className={styles.aiResultCard}>
                                                <h3 className={styles.sectionTitle}>
                                                    🍽️ AI 추천 안주
                                                </h3>
                                                <div className={styles.contentTitle}>{generatedFood.name}</div>
                                                <p className={styles.descriptionText}>{generatedFood.reason}</p>
                                            </div>
                                            {onGenerateCocktail && (
                                                <button
                                                    onClick={() => onGenerateCocktail(drink.name)}
                                                    className={styles.actionButton}
                                                    style={{ width: '100%', justifyContent: 'center' }}
                                                >
                                                    🔄 다시 추천받기
                                                </button>
                                            )}
                                        </div>
                                    ) : (
                                        <div className={styles.loadingContainer} style={{ background: 'rgba(255,255,255,0.7)' }}>
                                            <p style={{ color: '#5d4037', marginBottom: '20px', fontSize: '1.1rem', lineHeight: '1.6' }}>
                                                이 술과 잘 어울리는<br />안주를 AI가 추천해드려요!
                                            </p>
                                            {onGenerateCocktail && (
                                                <button
                                                    onClick={() => onGenerateCocktail(drink.name)}
                                                    className={styles.actionButton}
                                                >
                                                    🤖 AI 추천 받기
                                                </button>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}

                            {activeTab === 'cocktail' && (
                                <div className={styles.fadeInUp}>
                                    {isGeneratingCocktail ? (
                                        <LoadingSpinner theme="cocktail" message="AI가 칵테일 레시피 생성 중" />
                                    ) : generatedCocktails.length > 0 ? (
                                        <div>
                                            <div style={{ marginBottom: '20px' }}>
                                                {/* Navigation Arrows */}
                                                {generatedCocktails.length > 1 && (
                                                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '20px', marginBottom: '10px' }}>
                                                        <button onClick={prevCocktail} style={{
                                                            background: '#fff', border: '1px solid #ddd', borderRadius: '50%', width: '40px', height: '40px', cursor: 'pointer', fontSize: '1.2rem', boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                                                        }}>‹</button>
                                                        <span style={{ fontSize: '0.9rem', fontWeight: '600', color: '#555' }}>
                                                            {currentCocktailIndex + 1} / {generatedCocktails.length}
                                                        </span>
                                                        <button onClick={nextCocktail} style={{
                                                            background: '#fff', border: '1px solid #ddd', borderRadius: '50%', width: '40px', height: '40px', cursor: 'pointer', fontSize: '1.2rem', boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                                                        }}>›</button>
                                                    </div>
                                                )}

                                                {/* Single Cocktail Card (Carousel Item) */}
                                                {(() => {
                                                    const cocktail = generatedCocktails[currentCocktailIndex];
                                                    if (!cocktail) return null;
                                                    return (
                                                        <div className={`${styles.aiResultCard} ${styles.fadeInUp}`} key={currentCocktailIndex}>
                                                            {cocktail.cocktail_image_url && (
                                                                <div style={{ height: '220px', overflow: 'hidden', position: 'relative', borderRadius: '12px', marginBottom: '20px' }}>
                                                                    <Image src={`/api/image-proxy?url=${encodeURIComponent(cocktail.cocktail_image_url)}`} alt={cocktail.cocktail_title} fill style={{ objectFit: 'cover' }} />
                                                                </div>
                                                            )}

                                                            <h3 className={styles.sectionTitle} style={{ fontSize: '1.6rem', marginBottom: '15px', color: '#222' }}>
                                                                🍹 {cocktail.cocktail_title}
                                                            </h3>

                                                            <div className={styles.metaContainer}>
                                                                <div className={styles.ingredientBadge}>
                                                                    <strong style={{ color: '#e65100' }}>재료:</strong> <span style={{ color: '#333' }}>{cocktail.cocktail_base}</span>
                                                                </div>
                                                                {cocktail.cocktail_garnish && (
                                                                    <div className={styles.ingredientBadge}>
                                                                        <strong style={{ color: '#2e7d32' }}>가니쉬:</strong> <span style={{ color: '#333' }}>{cocktail.cocktail_garnish}</span>
                                                                    </div>
                                                                )}
                                                            </div>

                                                            <div className={styles.recipeList}>
                                                                <strong style={{ color: '#000', fontSize: '1.1rem', display: 'block', marginBottom: '15px' }}>📝 레시피</strong>
                                                                <div>
                                                                    {cocktail.cocktail_recipe.split(/\d+\./).filter(step => step.trim()).map((step, stepIndex) => (
                                                                        <div key={stepIndex} className={styles.recipeStep}>
                                                                            <div className={styles.stepNumber} style={{ color: '#fff', background: '#333' }}>{stepIndex + 1}</div>
                                                                            <div className={styles.stepText} style={{ color: '#111' }}>{step.trim()}</div>
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            </div>

                                                            {/* YouTube Video */}
                                                            {cocktail.youtube_video_id && (
                                                                <div style={{ marginTop: '25px' }}>
                                                                    <h4 style={{ color: '#000', fontSize: '1.1rem', marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                                        🎥 참고 영상
                                                                    </h4>
                                                                    <div style={{ position: 'relative', paddingBottom: '56.25%', height: 0, overflow: 'hidden', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
                                                                        <iframe
                                                                            src={`https://www.youtube.com/embed/${cocktail.youtube_video_id}`}
                                                                            title={cocktail.youtube_video_title || '칵테일 제조 영상'}
                                                                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                                                            allowFullScreen
                                                                            style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', border: 'none' }}
                                                                        />
                                                                    </div>
                                                                    {cocktail.youtube_video_title && (
                                                                        <p style={{ marginTop: '10px', fontSize: '0.9rem', color: '#333', fontStyle: 'italic', fontWeight: '500' }}>
                                                                            {cocktail.youtube_video_title}
                                                                        </p>
                                                                    )}
                                                                </div>
                                                            )}
                                                        </div>
                                                    );
                                                })()}

                                            </div>
                                            {onGenerateCocktail && (
                                                <button
                                                    onClick={() => onGenerateCocktail(drink.name)}
                                                    className={styles.actionButton}
                                                    style={{ width: '100%', justifyContent: 'center' }}
                                                >
                                                    🔄 더 추천받기
                                                </button>
                                            )}
                                        </div>
                                    ) : (
                                        <div className={styles.loadingContainer} style={{ background: 'rgba(255,255,255,0.7)' }}>
                                            <p style={{ color: '#333', marginBottom: '20px', fontSize: '1.1rem', lineHeight: '1.6', fontWeight: '600' }}>
                                                이 술로 만들 수 있는<br />창의적인 칵테일을 AI가 추천해드려요!
                                            </p>
                                            {onGenerateCocktail && (
                                                <button
                                                    onClick={() => onGenerateCocktail(drink.name)}
                                                    className={styles.actionButton}
                                                >
                                                    🤖 AI 추천 받기
                                                </button>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Hansang Tab */}
                            {activeTab === 'hansang' && drink.province && onGenerateHansang && (
                                <div className={styles.fadeInUp}>
                                    {isGeneratingHansang ? (
                                        <LoadingSpinner theme="hansang" message={`${drink.province} 특산물로 한상차림 준비 중`} />
                                    ) : generatedHansang.length > 0 ? (
                                        <div>
                                            <div className={styles.aiResultCard} style={{ borderColor: '#ffca28', background: 'rgba(255, 253, 231, 0.5)' }}>
                                                <h3 className={styles.sectionTitle} style={{ color: '#e65100' }}>
                                                    🍚 {drink.province} 특산물 한상차림
                                                </h3>
                                                <p className={styles.descriptionText}>
                                                    AI가 {drink.province}{drink.city ? ` ${drink.city}` : ''}의 특산물로 추천하는 안주입니다
                                                </p>
                                            </div>
                                            <div className={styles.hansangGrid}>
                                                {generatedHansang.map((item, index) => (
                                                    <div key={index} className={styles.aiResultCard} style={{
                                                        padding: '0',
                                                        border: item.specialty_used ? '2px solid #ffca28' : '1px solid rgba(141, 110, 99, 0.15)',
                                                        background: '#fff'
                                                    }}>
                                                        {item.image_url && (
                                                            <div style={{ height: '180px', position: 'relative', background: '#f8f9fa' }}>
                                                                <Image
                                                                    src={`/api/image-proxy?url=${encodeURIComponent(item.image_url)}`}
                                                                    alt={item.name}
                                                                    fill
                                                                    style={{ objectFit: 'cover' }}
                                                                    sizes="250px"
                                                                    onError={(e) => {
                                                                        const target = e.target as HTMLImageElement;
                                                                        target.style.display = 'none';
                                                                        const parent = target.parentElement;
                                                                        if (parent && !parent.querySelector('.placeholder')) {
                                                                            const placeholder = document.createElement('div');
                                                                            placeholder.className = 'placeholder';
                                                                            placeholder.style.cssText = 'width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 4rem; background: linear-gradient(135deg, #fff3e0, #ffecb3)';
                                                                            placeholder.textContent = '🍽️';
                                                                            parent.appendChild(placeholder);
                                                                        }
                                                                    }}
                                                                />
                                                            </div>
                                                        )}
                                                        <div style={{ padding: '20px' }}>
                                                            {item.specialty_used && (
                                                                <div className={styles.ingredientBadge} style={{ color: '#e65100', background: '#fff8e1', border: '1px solid #ffe0b2', marginBottom: '10px', display: 'inline-flex' }}>
                                                                    🌾 {item.specialty_used}
                                                                </div>
                                                            )}
                                                            {!item.specialty_used && (
                                                                <div className={styles.ingredientBadge} style={{ background: '#f5f5f5', color: '#757575', marginBottom: '10px', display: 'inline-flex' }}>
                                                                    🍽️ AI 추천
                                                                </div>
                                                            )}
                                                            <h4 style={{ margin: '0 0 10px 0', fontSize: '1.2rem', fontWeight: '800', color: '#3e2723' }}>
                                                                {item.name}
                                                            </h4>
                                                            <p className={styles.descriptionText} style={{ fontSize: '0.95rem', lineHeight: '1.5' }}>
                                                                {item.reason}
                                                            </p>
                                                            {item.link_url && (
                                                                <a href={item.link_url} target="_blank" rel="noopener noreferrer" className={styles.link} style={{ color: '#ff6f00', fontWeight: 'bold' }}>
                                                                    🛒 특산물 구매하기 →
                                                                </a>
                                                            )}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                            <button
                                                onClick={() => onGenerateHansang(drink.province || '', drink.city || '')}
                                                className={styles.actionButton}
                                                style={{ width: '100%', justifyContent: 'center' }}
                                            >
                                                🔄 한상차림 다시 추천받기
                                            </button>
                                        </div>
                                    ) : (
                                        <div className={styles.loadingContainer} style={{ background: 'rgba(255,255,255,0.7)' }}>
                                            <div style={{ fontSize: '3rem', marginBottom: '15px' }}>🍚</div>
                                            <h4 style={{ fontSize: '1.3rem', color: '#333', marginBottom: '10px' }}>
                                                {drink.province} 특산물 한상차림
                                            </h4>
                                            <p style={{ color: '#666', marginBottom: '20px', fontSize: '1rem', lineHeight: '1.6' }}>
                                                {drink.province}{drink.city ? ` ${drink.city}` : ''}의 특산물로<br />
                                                이 술과 어울리는 한상차림을 AI가 추천해드려요!
                                            </p>
                                            <button
                                                onClick={() => onGenerateHansang(drink.province || '', drink.city || '')}
                                                className={styles.actionButton}
                                            >
                                                🤖 한상차림 추천받기
                                            </button>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </section>
                )
            }

            {/* DB COCKTAILS SECTION */}
            {
                drink.cocktails && drink.cocktails.length > 0 && (
                    <section style={{ borderTop: '2px solid #f0f0f0', paddingTop: '40px', marginTop: '40px' }}>
                        <h3 style={{ margin: '0 0 20px 0', color: '#d32f2f', fontSize: '1.6rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
                            🏆 추천 칵테일
                        </h3>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '25px' }}>
                            {drink.cocktails.map((cocktail: any, index) => {
                                // Support both API formats: {name, recipe} and {cocktail_title, cocktail_recipe}
                                const title = cocktail.cocktail_title || cocktail.name || '칵테일';
                                const recipe = cocktail.cocktail_recipe || cocktail.recipe || '';
                                const imageUrl = cocktail.cocktail_image_url;
                                const homepageUrl = cocktail.cocktail_homepage_url;

                                return (
                                    <div key={index} style={{
                                        background: '#fff',
                                        borderRadius: '16px',
                                        overflow: 'hidden',
                                        border: '1px solid #eee',
                                        boxShadow: '0 8px 24px rgba(0,0,0,0.06)',
                                        transition: 'transform 0.2s, box-shadow 0.2s',
                                        display: 'flex',
                                        flexDirection: 'column'
                                    }}
                                        onMouseOver={(e) => {
                                            e.currentTarget.style.transform = 'translateY(-5px)';
                                            e.currentTarget.style.boxShadow = '0 12px 32px rgba(0,0,0,0.1)';
                                        }}
                                        onMouseOut={(e) => {
                                            e.currentTarget.style.transform = 'translateY(0)';
                                            e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.06)';
                                        }}
                                    >
                                        {imageUrl ? (
                                            <div style={{ height: '200px', width: '100%', position: 'relative' }}>
                                                <Image
                                                    src={`/api/image-proxy?url=${encodeURIComponent(imageUrl)}`}
                                                    alt={title}
                                                    fill
                                                    style={{ objectFit: 'cover' }}
                                                />
                                            </div>
                                        ) : (
                                            <div style={{ height: '140px', background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '3rem' }}>
                                                🍸
                                            </div>
                                        )}
                                        <div style={{ padding: '20px', flex: 1, display: 'flex', flexDirection: 'column' }}>
                                            <h5 style={{ margin: '0 0 10px 0', fontSize: '1.25rem', fontWeight: '800', color: '#333' }}>
                                                {title}
                                            </h5>
                                            <div style={{ width: '40px', height: '3px', background: '#ffca28', marginBottom: '15px', borderRadius: '2px' }}></div>
                                            <p style={{ fontSize: '0.95rem', color: '#555', margin: '0 0 15px 0', lineHeight: '1.6', whiteSpace: 'pre-line', flex: 1 }}>
                                                {recipe}
                                            </p>
                                            {homepageUrl && (
                                                <a
                                                    href={homepageUrl}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    style={{
                                                        display: 'inline-flex',
                                                        alignItems: 'center',
                                                        gap: '6px',
                                                        padding: '10px 18px',
                                                        background: 'linear-gradient(135deg, #8d6e63 0%, #5d4037 100%)',
                                                        color: '#fff',
                                                        borderRadius: '20px',
                                                        fontSize: '0.9rem',
                                                        fontWeight: '600',
                                                        textDecoration: 'none',
                                                        transition: 'all 0.3s',
                                                        alignSelf: 'flex-start',
                                                        boxShadow: '0 2px 8px rgba(93, 64, 55, 0.3)'
                                                    }}
                                                    onMouseOver={(e) => {
                                                        (e.currentTarget as HTMLElement).style.transform = 'translateY(-2px)';
                                                        (e.currentTarget as HTMLElement).style.boxShadow = '0 4px 12px rgba(93, 64, 55, 0.4)';
                                                    }}
                                                    onMouseOut={(e) => {
                                                        (e.currentTarget as HTMLElement).style.transform = 'translateY(0)';
                                                        (e.currentTarget as HTMLElement).style.boxShadow = '0 2px 8px rgba(93, 64, 55, 0.3)';
                                                    }}
                                                >
                                                    📖 자세히 보기 →
                                                </a>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </section>
                )
            }

            {/* 1. ONLINE SHOPS SECTION (Crawling Data) */}
            {
                (onlineData && onlineData.products.length > 0) ? (
                    <section style={{ borderTop: '2px solid #f0f0f0', paddingTop: '40px', marginTop: '40px' }}>
                        <h3 style={{ fontSize: '1.6rem', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                            🛒 <span style={{ fontWeight: '800', color: '#333' }}>온라인 최저가</span>
                            <span style={{ fontSize: '1rem', color: '#666', fontWeight: 'normal', marginLeft: 'auto' }}>
                                쇼핑몰 데이터
                            </span>
                        </h3>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '15px' }}>
                            {onlineData.products.map((product, index) => {
                                // CHECK: Is this a placeholder item? (Price 0 and special text)
                                const isPlaceholder = product.price === 0;

                                if (isPlaceholder) {
                                    return (
                                        <div key={index} style={{
                                            background: "#f9f9f9",
                                            border: '1px dashed #ccc',
                                            borderRadius: '12px',
                                            padding: '30px',
                                            textAlign: 'center',
                                            gridColumn: '1 / -1', // Take full width
                                            display: 'flex',
                                            flexDirection: 'column',
                                            alignItems: 'center',
                                            justifyContent: 'center'
                                        }}>
                                            <div style={{ fontSize: '2rem', marginBottom: '10px', color: '#aaa' }}>🏷️</div>
                                            <h4 style={{ margin: '0 0 5px 0', fontSize: '1.1rem', fontWeight: '700', color: '#555' }}>최저가 정보가 없습니다</h4>
                                            <p style={{ margin: '0 0 15px 0', fontSize: '0.9rem', color: '#888' }}>온라인 판매처를 찾을 수 없습니다.</p>
                                            <a href={product.url} target="_blank" rel="noopener noreferrer" style={{
                                                background: '#555',
                                                color: '#fff',
                                                padding: '8px 16px',
                                                borderRadius: '8px',
                                                fontSize: '0.9rem',
                                                textDecoration: 'none',
                                                fontWeight: '600',
                                                display: 'inline-flex',
                                                alignItems: 'center',
                                                gap: '6px'
                                            }}>
                                                🔍 네이버 쇼핑 검색결과 보기
                                            </a>
                                        </div>
                                    );
                                }

                                // Normal Product Item
                                const isReference = product.shop === "지식백과 기준 가격";

                                return (
                                    <div key={index} className={styles.productCard} style={{
                                        background: isReference ? '#fff8e1' : '#fff',
                                        border: isReference ? '1px solid #ffcc80' : '1px solid #eee',
                                        borderRadius: '12px',
                                        padding: '16px',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        justifyContent: 'space-between',
                                        boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
                                        position: 'relative',
                                        overflow: 'hidden'
                                    }}>
                                        <div>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                                                <span style={{
                                                    fontSize: '0.8rem',
                                                    color: '#fff',
                                                    background: isReference ? '#ffa726' : (index === 0 ? '#ff5252' : '#757575'),
                                                    padding: '3px 8px',
                                                    borderRadius: '6px',
                                                    fontWeight: 'bold'
                                                }}>
                                                    {isReference ? '참고가격' : (index === 0 ? '최저가 추천' : '판매처')}
                                                </span>
                                                <span style={{ fontSize: '0.85rem', color: '#888', fontWeight: '500' }}>
                                                    {product.shop}
                                                </span>
                                            </div>
                                            <h4 style={{
                                                margin: '0 0 12px 0',
                                                fontSize: '1.05rem',
                                                fontWeight: '700',
                                                color: '#333',
                                                lineHeight: '1.4',
                                                height: '44px',
                                                overflow: 'hidden',
                                                textOverflow: 'ellipsis',
                                                display: '-webkit-box',
                                                WebkitLineClamp: 2,
                                                WebkitBoxOrient: 'vertical'
                                            }}>
                                                {product.name}
                                            </h4>
                                        </div>

                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px', borderTop: '1px solid #f0f0f0', paddingTop: '10px' }}>
                                            <span style={{ fontSize: '1.1rem', fontWeight: '800', color: '#1a1a1a' }}>
                                                {product.price.toLocaleString()}원
                                            </span>

                                            <a href={product.url} target="_blank" rel="noopener noreferrer" style={{
                                                background: isReference ? '#fb8c00' : '#222',
                                                color: '#fff',
                                                padding: '8px 14px',
                                                borderRadius: '8px',
                                                fontSize: '0.85rem',
                                                textDecoration: 'none',
                                                fontWeight: '600'
                                            }}>
                                                {isReference ? '검색하기' : '구매하기'}
                                            </a>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </section>
                ) : (
                    <section style={{ borderTop: '2px solid #f0f0f0', paddingTop: '40px', marginTop: '40px' }}>
                        <div style={{
                            background: "#fff",
                            border: '1px solid #eee',
                            borderRadius: '16px',
                            padding: '30px',
                            textAlign: 'center'
                        }}>
                            <div style={{ fontSize: '3rem', marginBottom: '15px' }}>🍶</div>
                            <h3 style={{ margin: '0 0 10px 0', color: '#333', fontSize: '1.4rem', fontWeight: '800' }}>
                                온라인 판매처 정보가 없습니다
                            </h3>
                            <p style={{ fontSize: '1rem', color: '#666', marginBottom: '20px' }}>
                                근처 주류 백화점이나 아래 오프라인 판매점을 확인해주세요.
                            </p>

                            {drink.encyclopedia_price_text && (
                                <div style={{
                                    background: 'rgba(255,255,255,0.7)',
                                    borderRadius: '8px',
                                    padding: '15px',
                                    display: 'inline-block',
                                    marginTop: '10px'
                                }}>
                                    <span style={{ fontWeight: 'bold', color: '#e65100', marginRight: '8px' }}>참고 가격</span>
                                    <span style={{ color: '#3e2723' }}>{drink.encyclopedia_price_text}</span>
                                </div>
                            )}
                        </div>
                    </section>
                )
            }

            {/* 2. OFFLINE SHOPS SECTION (Map Data from ES selling_shops) */}
            {
                (drink.selling_shops && drink.selling_shops.length > 0) && (
                    <section style={{ borderTop: '2px solid #f0f0f0', paddingTop: '40px', marginTop: '40px' }}>
                        <h3 style={{ fontSize: '1.6rem', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                            📌 <span style={{ fontWeight: '800', color: '#333' }}>주변 오프라인 판매점</span>
                        </h3>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '15px' }}>
                            {drink.selling_shops.map((shop, index) => (
                                <div key={index} style={{ background: "#fff", border: '1px solid #eee', borderRadius: '12px', padding: '15px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
                                    <h4 style={{ margin: '0 0 10px 0', fontSize: '1.1rem', fontWeight: '700', color: '#222' }}>{shop.name}</h4>
                                    <p style={{ margin: '0 0 5px 0', fontSize: '0.9rem', color: '#555' }}>📍 {shop.address}</p>
                                    <p style={{ margin: '0 0 10px 0', fontSize: '0.9rem', color: '#555' }}>📞 {shop.contact}</p>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
                                        <span style={{ fontSize: '1.05rem', fontWeight: '700', color: '#d32f2f' }}>
                                            {shop.price ? `${shop.price.toLocaleString()}원` : '-'}
                                        </span>
                                        <a href={`https://map.naver.com/v5/search/${encodeURIComponent(shop.name)}`} target="_blank" rel="noopener noreferrer" style={{ background: '#03C75A', color: '#fff', padding: '5px 10px', borderRadius: '6px', fontSize: '0.85rem', textDecoration: 'none', fontWeight: 'bold' }}>
                                            지도보기
                                        </a>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </section>
                )
            }

            {/* SIMILAR DRINKS */}
            {
                similarDrinks.length > 0 && (
                    <section style={{ borderTop: '2px solid #f0f0f0', paddingTop: '40px', marginTop: '40px' }}>
                        <h3 style={{ fontSize: '1.6rem', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                            🔍 <span style={{ fontWeight: '800', color: '#333' }}>이런 술은 어떠오?</span>
                        </h3>
                        <div className={styles.similarDrinksGrid} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: '15px' }}>
                            {similarDrinks.filter(simDrink => simDrink.id).map((simDrink, index) => (
                                <a key={index} href={`/drink/${simDrink.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                                    <div style={{ background: "#fff", borderRadius: '12px', overflow: 'hidden', border: '1px solid #eee', boxShadow: '0 2px 8px rgba(0,0,0,0.05)', transition: 'transform 0.2s' }}
                                        onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-5px)'}
                                        onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
                                    >
                                        <div style={{ height: '160px', position: 'relative', background: '#f8f9fa' }}>
                                            {simDrink.image_url ? (
                                                <Image
                                                    src={`/api/image-proxy?url=${encodeURIComponent(simDrink.image_url)}`}
                                                    alt={simDrink.name}
                                                    fill
                                                    style={{ objectFit: 'contain', padding: '10px' }}
                                                    sizes="160px"
                                                    unoptimized={true}
                                                />
                                            ) : (
                                                <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>🍶</div>
                                            )}
                                        </div>
                                        <div style={{ padding: '10px', textAlign: 'center' }}>
                                            <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: '700', color: '#333' }}>{simDrink.name}</h4>
                                        </div>
                                    </div>
                                </a>
                            ))}
                        </div>
                    </section>
                )
            }

            {/* ENCYCLOPEDIA */}
            {
                drink.encyclopedia && Array.isArray(drink.encyclopedia) && drink.encyclopedia.length > 0 && (
                    <section style={{ borderTop: '2px solid #f0f0f0', paddingTop: '40px', marginTop: '40px' }}>
                        <details style={{ background: '#fff3e0', borderRadius: '12px', border: '1px solid #ffe0b2', overflow: 'hidden' }}>
                            <summary style={{ padding: '15px 20px', cursor: 'pointer', fontWeight: '700', color: '#e65100', fontSize: '1.1rem', listStyle: 'none', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <span>📖 전통주 지식백과 (더보기)</span>
                                <span style={{ fontSize: '0.9rem' }}>▼</span>
                            </summary>
                            <div style={{ padding: '20px', borderTop: '1px solid #ffe0b2', background: '#fff' }}>
                                {drink.encyclopedia.map((section, idx) => (
                                    <div key={idx} style={{ marginBottom: '25px' }}>
                                        <h4 style={{ fontSize: '1.1rem', color: '#333', marginBottom: '10px', borderLeft: '4px solid #ff9800', paddingLeft: '10px' }}>{section.title}</h4>
                                        <p style={{ fontSize: '1rem', lineHeight: '1.7', color: '#555', whiteSpace: 'pre-line' }}>{section.text}</p>
                                        {section.images && section.images.length > 0 && (
                                            <div style={{ display: 'flex', gap: '10px', overflowX: 'auto', marginTop: '10px', paddingBottom: '10px' }}>
                                                {section.images.map((img, imgIdx) => (
                                                    <div key={imgIdx} style={{ height: '150px', width: '200px', position: 'relative', flexShrink: 0 }}>
                                                        <Image
                                                            src={`/api/image-proxy?url=${encodeURIComponent(img.src)}`}
                                                            alt={img.alt}
                                                            fill
                                                            style={{ borderRadius: '8px', objectFit: 'cover' }}
                                                        />
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </details>
                    </section>
                )
            }
        </div >
    );
}
