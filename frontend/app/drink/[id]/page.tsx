"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getApiUrl } from "@/lib/api";
import styles from "./page.module.css";
import Link from "next/link";
import DrinkDetailCard, { DrinkDetail } from "../../components/DrinkDetailCard";

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

interface HansangItem {
    name: string;
    image_url?: string;
    reason: string;
    link_url?: string;
}

export default function DrinkDetailPage() {
    const params = useParams();
    const router = useRouter();
    const [drink, setDrink] = useState<DrinkDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [isGeneratingCocktail, setIsGeneratingCocktail] = useState<boolean>(false);
    const [generatedFood, setGeneratedFood] = useState<{ name: string, reason: string } | null>(null);
    const [generatedCocktails, setGeneratedCocktails] = useState<Cocktail[]>([]);
    const [isGeneratingHansang, setIsGeneratingHansang] = useState<boolean>(false);
    const [generatedHansang, setGeneratedHansang] = useState<HansangItem[]>([]);

    const generateCocktail = async (drinkName: string) => {
        setIsGeneratingCocktail(true);
        try {
            const response = await fetch(getApiUrl('/cocktail/generate'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ drink_name: drinkName }),
            });
            if (response.ok) {
                const data = await response.json();

                const newCocktail = {
                    cocktail_title: data.cocktail_title,
                    cocktail_base: data.cocktail_base,
                    cocktail_garnish: data.cocktail_garnish,
                    cocktail_recipe: data.cocktail_recipe,
                    cocktail_image_url: data.cocktail_image_url,
                    youtube_video_id: data.youtube_video_id,
                    youtube_video_title: data.youtube_video_title,
                    youtube_thumbnail_url: data.youtube_thumbnail_url
                };

                if (data.food_pairing_name) {
                    setGeneratedFood({
                        name: data.food_pairing_name,
                        reason: data.food_pairing_reason || ""
                    });
                }

                setGeneratedCocktails(prev => [...prev, newCocktail]);
            }
        } catch (error) {
            console.error("Failed to generate cocktail", error);
        } finally {
            setIsGeneratingCocktail(false);
        }
    };

    const generateHansang = async (province: string, city: string) => {
        setIsGeneratingHansang(true);
        try {
            const response = await fetch(getApiUrl('/hansang/recommend'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    drink_name: drink?.name || '',
                    province,
                    city,
                    drink_description: drink?.description || drink?.intro || ''
                }),
            });
            if (response.ok) {
                const data = await response.json();
                setGeneratedHansang(data.items || []);
            } else {
                console.error("Failed to generate hansang:", await response.text());
            }
        } catch (error) {
            console.error("Failed to generate hansang", error);
        } finally {
            setIsGeneratingHansang(false);
        }
    };

    useEffect(() => {
        const fetchDrink = async () => {
            try {
                const response = await fetch(getApiUrl(`/search/detail/${params.id}`));
                if (!response.ok) {
                    throw new Error("Failed to fetch drink details");
                }
                const data = await response.json();
                setDrink(data);
            } catch (error) {
                console.error(error);
            } finally {
                setLoading(false);
            }
        };

        if (params.id) {
            fetchDrink();
        }
    }, [params.id, router]);

    if (loading) {
        return (
            <div className={styles.container} style={{
                backgroundImage: "linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url('/background.png')",
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                backgroundAttachment: 'fixed',
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
            }}>
                <div className={styles.loading}>술 항아리를 열어보는 중... 🍶</div>
            </div>
        );
    }

    if (!drink) {
        return (
            <div className={styles.container} style={{
                backgroundImage: "linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url('/background.png')",
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                backgroundAttachment: 'fixed',
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
            }}>
                <div className={styles.loading}>해당 술을 찾을 수 없습니다.</div>
            </div>
        );
    }

    return (
        <div className={styles.container} style={{
            backgroundImage: "linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url('/background.png')",
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            backgroundAttachment: 'fixed',
            minHeight: '100vh'
        }}>
            <div className={styles.resultContainer}>
                <div style={{ textAlign: 'left', marginBottom: '20px' }}>
                    <Link href="/" className={styles.backButton}>← 메인으로 돌아가기</Link>
                </div>

                <DrinkDetailCard
                    drink={drink}
                    onGenerateCocktail={generateCocktail}
                    generatedFood={generatedFood}
                    generatedCocktails={generatedCocktails}
                    isGeneratingCocktail={isGeneratingCocktail}
                    onGenerateHansang={generateHansang}
                    generatedHansang={generatedHansang}
                    isGeneratingHansang={isGeneratingHansang}
                />
            </div>
        </div>
    );
}
