"use client";

import { useSession, signIn } from "next-auth/react";
import { useState, useEffect, Suspense, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import styles from "./page.module.css";
import { api } from '@/lib/api';
import InteractiveTasteRadarChart from '@/app/components/InteractiveTasteRadarChart';

function WriteForm() {
    const { data: session, status } = useSession();
    const router = useRouter();
    const searchParams = useSearchParams();
    const editId = searchParams.get("edit");

    // Search State
    const [searchQuery, setSearchQuery] = useState("");
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [showDropdown, setShowDropdown] = useState(false);
    const searchTimeout = useRef<NodeJS.Timeout | null>(null);

    const [formData, setFormData] = useState({
        liquor_id: 999,
        liquor_name: "",
        image_url: "",
        content: "",
        rating: 5,
        sweet: 3,
        sour: 3,
        body: 3,
        scent: 3,
        throat: 3,
        drinking_temperature: "room" as "cold" | "room" | "warm",
        pairing_foods: [] as string[],
        atmosphere: "solo",
        seasons: [] as string[],
        purchase_location: ""
    });

    // Separate state for pairing foods input (to allow typing commas/spaces)
    const [pairingFoodsInput, setPairingFoodsInput] = useState("");

    // Auto-redirect removed
    /*
    useEffect(() => {
        if (status === "unauthenticated") {
            router.push("/board");
        }
    }, [status, router]);
    */

    // Fetch existing note if editing
    useEffect(() => {
        if (editId && session?.user) {
            const userId = (session.user as any).id || session.user.email;
            api.notes.getByUserId(userId)
                .then(notes => {
                    const note = notes.find((n: any) => n._id === editId);
                    if (note) {
                        setFormData({
                            liquor_id: note.liquor_id,
                            liquor_name: note.liquor_name,
                            image_url: note.images?.[0] || "",
                            content: note.content,
                            rating: note.rating,
                            sweet: note.flavor_profile.sweet,
                            sour: note.flavor_profile.sour,
                            body: note.flavor_profile.body,
                            scent: note.flavor_profile.scent,
                            throat: note.flavor_profile.throat,
                            drinking_temperature: (note as any).drinking_temperature || "room",
                            pairing_foods: (note as any).pairing_foods || [],
                            atmosphere: (note as any).atmosphere || "solo",
                            seasons: (note as any).seasons || [],
                            purchase_location: (note as any).purchase_location || ""
                        });
                        setSearchQuery(note.liquor_name);
                        setPairingFoodsInput((note as any).pairing_foods?.join(', ') || "");
                    }
                })
                .catch(err => console.error("Failed to load note:", err));
        }
    }, [editId, session]);

    // Search Logic
    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const query = e.target.value;
        setSearchQuery(query);
        setFormData(prev => ({ ...prev, liquor_name: query }));

        if (searchTimeout.current) clearTimeout(searchTimeout.current);

        if (query.length > 1) {
            searchTimeout.current = setTimeout(async () => {
                try {
                    const data = await api.search.search(query);
                    if (data && data.candidates) {
                        setSearchResults(data.candidates);
                        setShowDropdown(true);
                    } else if (data && data.name) {
                        setSearchResults([{
                            name: data.name,
                            id: 999,
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

    const selectLiquor = (liquor: any) => {
        setFormData(prev => ({
            ...prev,
            liquor_name: liquor.name,
            liquor_id: liquor.id || 999,
            image_url: liquor.image_url || ""
        }));
        setSearchQuery(liquor.name);
        setShowDropdown(false);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        // e.preventDefault();
        // if (!session?.user) return; // DISABLED

        const userId = (session?.user as any)?.id || session?.user?.email || "anonymous_user";
        const authorName = session?.user?.name || (session?.user as any)?.nickname || "익명 주모";

        // Auto-generate tags
        const autoTags: string[] = [];
        if (formData.drinking_temperature === 'cold') autoTags.push('#시원한');
        if (formData.drinking_temperature === 'warm') autoTags.push('#따뜻한');
        if (formData.sweet >= 4) autoTags.push('#달콤한');
        if (formData.sour >= 4) autoTags.push('#상큼한');
        if (formData.body >= 4) autoTags.push('#진한');
        formData.seasons.forEach(s => autoTags.push(`#${s}술`));
        if (formData.atmosphere === 'solo') autoTags.push('#혼술추천');
        if (formData.atmosphere === 'friends') autoTags.push('#모임용');

        const payload = {
            user_id: userId,
            author_name: authorName,
            liquor_id: formData.liquor_id,
            liquor_name: formData.liquor_name,
            rating: formData.rating,
            flavor_profile: {
                sweet: formData.sweet,
                sour: formData.sour,
                body: formData.body,
                scent: formData.scent,
                throat: formData.throat
            },
            content: formData.content,
            tags: autoTags,
            images: formData.image_url ? [formData.image_url] : [],
            is_public: true,
            drinking_temperature: formData.drinking_temperature,
            pairing_foods: formData.pairing_foods,
            atmosphere: formData.atmosphere,
            seasons: formData.seasons,
            purchase_location: formData.purchase_location
        };

        try {
            if (editId) {
                await api.notes.update(editId, payload);
            } else {
                await api.notes.create(payload);
            }
            router.push(editId ? "/mypage" : "/board");
        } catch (error) {
            console.error(error);
            alert("오류가 발생했습니다.");
        }
    };

    // Helper Components for Chips
    const Chip = ({ label, active, onClick, icon }: any) => (
        <div
            className={`${styles.chip} ${active ? styles.chipActive : ''}`}
            onClick={onClick}
        >
            {icon} {label}
        </div>
    );

    // Helper for Flavor Dots
    const FlavorSlider = ({ label, value, onChange }: any) => (
        <div className={styles.flavorItem}>
            <span className={styles.flavorLabel}>{label}</span>
            <div className={styles.dotContainer}>
                {[1, 2, 3, 4, 5].map(v => (
                    <div
                        key={v}
                        className={`${styles.dot} ${v <= value ? styles.dotActive : ''}`}
                        onClick={() => onChange(v)}
                        style={{ background: v <= value ? '#8d6e63' : '#ddd' }}
                    />
                ))}
            </div>
        </div>
    );

    if (status === "loading") return <div>Loading...</div>;

    return (
        <div className={styles.container}>
            <h1 className={styles.title}>{editId ? "노트 수정하기" : "시음 노트 기록"}</h1>

            {/* Auth check removed */}
            {false ? (
                <div className={styles.authCard} style={{ margin: '0 auto' }}>
                    <div className={styles.authIcon}>🔒</div>
                    <h2 className={styles.authTitle}>로그인이 필요합니다</h2>
                    <p className={styles.authDescription}>
                        시음 노트를 기록하려면<br />로그인이 필요합니다
                    </p>
                    <button
                        className={styles.authButton}
                        onClick={() => signIn("cognito", { callbackUrl: "/board/write" })}
                    >
                        로그인하기
                    </button>
                </div>
            ) : (
                <form onSubmit={handleSubmit} className={styles.formContainer}>

                    {/* Section 1: Basic Info */}
                    <div className={styles.section}>
                        <div className={styles.sectionHeader}>
                            <span>🍶</span> 기본 정보
                        </div>

                        <div className={styles.formGroup} style={{ position: 'relative' }}>
                            <label className={styles.label}>어떤 술을 드셨나요?</label>
                            <input
                                className={styles.input}
                                value={searchQuery}
                                onChange={handleSearchChange}
                                placeholder="술 이름을 검색해보세요..."
                                required
                            />
                            {showDropdown && searchResults.length > 0 && (
                                <ul className={styles.autocompleteDropdown}>
                                    {searchResults.map((item, idx) => (
                                        <li key={idx} onClick={() => selectLiquor(item)} className={styles.autocompleteItem}>
                                            {item.image_url ? (
                                                <img src={item.image_url} alt="" style={{ width: 30, height: 30, borderRadius: 4, objectFit: 'cover' }} />
                                            ) : (
                                                <div style={{ width: 30, height: 30, background: '#eee', borderRadius: 4 }} />
                                            )}
                                            <span>{item.name}</span>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>

                        {formData.image_url && (
                            <div className={styles.imagePreview}>
                                <img src={formData.image_url} alt="Preview" style={{ maxHeight: 180, borderRadius: 8, boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                            </div>
                        )}
                    </div>

                    {/* Section 2: Flavor & Rating */}
                    <div className={styles.section}>
                        <div className={styles.sectionHeader}>
                            <span>👅</span> 맛과 평가
                        </div>

                        <div className={styles.starRating}>
                            {[1, 2, 3, 4, 5].map((star) => (
                                <span
                                    key={star}
                                    className={`${styles.star} ${star <= formData.rating ? styles.active : ''}`}
                                    onClick={() => setFormData({ ...formData, rating: star })}
                                >
                                    ★
                                </span>
                            ))}
                        </div>

                        <InteractiveTasteRadarChart
                            data={{
                                sweet: formData.sweet,
                                sour: formData.sour,
                                body: formData.body,
                                scent: formData.scent,
                                throat: formData.throat
                            }}
                            onChange={(tasteData) => setFormData({
                                ...formData,
                                sweet: tasteData.sweet,
                                sour: tasteData.sour,
                                body: tasteData.body,
                                scent: tasteData.scent,
                                throat: tasteData.throat
                            })}
                        />
                    </div>

                    {/* Section 3: Details */}
                    <div className={styles.section}>
                        <div className={styles.sectionHeader}>
                            <span>📝</span> 상세 기록
                        </div>

                        <div className={styles.formGroup}>
                            <label className={styles.label}>음용 온도</label>
                            <div className={styles.chipContainer}>
                                <Chip
                                    label="시원하게" icon="❄️"
                                    active={formData.drinking_temperature === 'cold'}
                                    onClick={() => setFormData({ ...formData, drinking_temperature: 'cold' })}
                                />
                                <Chip
                                    label="상온에서" icon="🌡️"
                                    active={formData.drinking_temperature === 'room'}
                                    onClick={() => setFormData({ ...formData, drinking_temperature: 'room' })}
                                />
                                <Chip
                                    label="따뜻하게" icon="🔥"
                                    active={formData.drinking_temperature === 'warm'}
                                    onClick={() => setFormData({ ...formData, drinking_temperature: 'warm' })}
                                />
                            </div>
                        </div>

                        <div className={styles.formGroup}>
                            <label className={styles.label}>분위기</label>
                            <div className={styles.chipContainer}>
                                {/* Reusing Chip for Atmosphere */}
                                {[
                                    { v: 'solo', l: '혼술', i: '🧘' },
                                    { v: 'family', l: '가족과', i: '👨‍👩‍👧‍👦' },
                                    { v: 'friends', l: '친구와', i: '🍻' },
                                    { v: 'date', l: '연인과', i: '💕' }
                                ].map(opt => (
                                    <Chip
                                        key={opt.v}
                                        label={opt.l} icon={opt.i}
                                        active={formData.atmosphere === opt.v}
                                        onClick={() => setFormData({ ...formData, atmosphere: opt.v })}
                                    />
                                ))}
                            </div>
                        </div>

                        <div className={styles.formGroup}>
                            <label className={styles.label}>계절</label>
                            <div className={styles.chipContainer}>
                                {['봄', '여름', '가을', '겨울'].map(s => (
                                    <Chip
                                        key={s} label={s} icon="🍂"
                                        active={formData.seasons.includes(s)}
                                        onClick={() => {
                                            const newSeasons = formData.seasons.includes(s)
                                                ? formData.seasons.filter(i => i !== s)
                                                : [...formData.seasons, s];
                                            setFormData({ ...formData, seasons: newSeasons });
                                        }}
                                    />
                                ))}
                            </div>
                        </div>

                        <div className={styles.formGroup}>
                            <label className={styles.label}>같이 먹은 안주</label>
                            <input
                                className={styles.input}
                                placeholder="예: 파전, 삼겹살 (쉼표로 구분)"
                                value={pairingFoodsInput}
                                onChange={e => setPairingFoodsInput(e.target.value)}
                                onBlur={e => {
                                    const foods = e.target.value.split(',').map(s => s.trim()).filter(Boolean);
                                    setFormData({ ...formData, pairing_foods: foods });
                                }}
                            />
                        </div>
                    </div>

                    {/* Section 4: Content */}
                    <div className={styles.section}>
                        <div className={styles.sectionHeader}>
                            <span>💬</span> 한줄 평
                        </div>
                        <textarea
                            className={styles.textarea}
                            placeholder="이 술에 대한 나만의 감상을 자유롭게 남겨주세요."
                            value={formData.content}
                            onChange={e => setFormData({ ...formData, content: e.target.value })}
                            required
                        />
                    </div>

                    <button type="submit" className={styles.submitButton}>
                        {editId ? "수정 완료" : "기록 완료"}
                    </button>

                </form>
            )}
        </div>
    );
}

export default function WritePage() {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <WriteForm />
        </Suspense>
    );
}
