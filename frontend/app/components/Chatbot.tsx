'use client';

import { useState, useRef, useEffect } from 'react';
import { useSession, signIn } from 'next-auth/react';
import Image from 'next/image';
import { getApiUrl } from '@/lib/api';
import styles from './Chatbot.module.css';
import { Rnd } from 'react-rnd';
import { Lock, Unlock } from 'lucide-react';
import Link from 'next/link';
import { useChat, ChatMessage } from '@/app/context/ChatContext';
import CocktailRecipeCard from './CocktailRecipeCard';

type Drink = {
    id: number;
    name: string;
    image_url: string;
    description: string;
    abv: string;
    volume: string;
};

// Extend ChatMessage type for local usage if needed, but context provides formatted messages
// We'll use the Context's message type primarily.

type ViewState = 'menu' | 'chat';

export default function Chatbot() {
    // const { data: session } = useSession(); // DISABLED for anonymous access
    const {
        isOpen, setIsOpen, messages, addMessage,
        isLoading, setIsLoading, input, setInput, clearHistory
    } = useChat();

    const [view, setView] = useState<ViewState>('chat');

    // Local UI State
    const [isClassicMode, setIsClassicMode] = useState(false);
    const [isMounted, setIsMounted] = useState(false);
    const [isDraggable, setIsDraggable] = useState(false);
    const [userLocation, setUserLocation] = useState<{ lat: number, lon: number } | null>(null);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    const suggestions = [
        "오늘의 전통주 추천해줘",
        "전통주 칵테일 레시피",
        "오늘 날씨에 맞는 술 추천해줘",
        "고전 소설에 어울리는 술"
    ];

    // Fetch location
    useEffect(() => {
        if (isOpen && !userLocation && navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    setUserLocation({
                        lat: position.coords.latitude,
                        lon: position.coords.longitude
                    });
                },
                (error) => console.log("Location access denied or error:", error)
            );
        }
    }, [isOpen]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    };

    useEffect(() => {
        setIsMounted(true);
    }, []);

    // Scroll on new messages
    useEffect(() => {
        if (view === 'chat' && isOpen) {
            scrollToBottom();
        }
    }, [messages, isOpen, isLoading, view]);

    // Handle click outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            const target = event.target as HTMLElement;
            if (target.closest(`.${styles.button}`)) return;
            const isInsideRef = containerRef.current && containerRef.current.contains(target);
            const isInsideRnd = target.closest('.chatbot-main-window');
            if (isOpen && !isInsideRef && !isInsideRnd) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isOpen]);

    const handleSendMessage = async (text: string = input, coords?: { lat: number, lon: number }) => {
        if (!text.trim()) return;

        addMessage("user", text);
        setInput("");
        setIsLoading(true);

        try {
            const apiPath = isClassicMode
                ? getApiUrl('/chatbot/classic-chat')
                : getApiUrl('/chatbot/chat');

            const bodyPayload: any = { message: text };

            // Location Logic
            const weatherKeywords = ["날씨", "비", "눈", "춥", "덥", "기온", "따뜻", "시원", "맑", "흐림", "계절", "여름", "겨울", "가을", "봄"];
            const isWeatherQuery = weatherKeywords.some(k => text.includes(k));

            let finalLat = coords?.lat;
            let finalLon = coords?.lon;

            if (!finalLat && isWeatherQuery && userLocation) {
                finalLat = userLocation.lat;
                finalLon = userLocation.lon;
            }

            if (finalLat && finalLon) {
                bodyPayload.latitude = finalLat;
                bodyPayload.longitude = finalLon;
            }

            const response = await fetch(apiPath, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(bodyPayload),
            });

            if (response.ok) {
                const data = await response.json();

                // Robust parsing for JSON at the end of the message
                let cocktailData = null;
                let cleanAnswer = data.answer;

                // Regex 1: Try to find Markdown code block ```json ... ```
                const codeBlockRegex = /```json\s*(\{[\s\S]*?\})\s*```/;
                const codeMatch = cleanAnswer.match(codeBlockRegex);

                if (codeMatch) {
                    try {
                        const jsonStr = codeMatch[1];
                        const parsed = JSON.parse(jsonStr);
                        if (parsed.cocktail) {
                            cocktailData = parsed.cocktail;
                            // Remove the code block from the message
                            cleanAnswer = cleanAnswer.replace(codeMatch[0], "").trim();
                        }
                    } catch (e) {
                        console.error("Failed to parse JSON from code block", e);
                    }
                } else {
                    // Regex 2: Try to find raw JSON object at the end of the string
                    // This is risky if the message naturally ends with }, so we check specifically for "cocktail" key
                    const rawJsonRegex = /(\{[\s\S]*"cocktail"[\s\S]*\})\s*$/;
                    const rawMatch = cleanAnswer.match(rawJsonRegex);
                    if (rawMatch) {
                        try {
                            const jsonStr = rawMatch[1];
                            const parsed = JSON.parse(jsonStr);
                            if (parsed.cocktail) {
                                cocktailData = parsed.cocktail;
                                // Remove the JSON object from the message
                                cleanAnswer = cleanAnswer.replace(rawMatch[0], "").trim();
                            }
                        } catch (e) {
                            console.error("Failed to parse raw JSON from end", e);
                        }
                    }
                }

                const extraData = {
                    drinks: data.drinks,
                    cocktail: cocktailData
                };

                addMessage("assistant", cleanAnswer, extraData);

            } else {
                throw new Error("Failed to get response");
            }
        } catch (error) {
            addMessage("assistant", "아이고, 머리가 아파서 잠시 생각을 못하겠구만유. 다시 물어봐주시오.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleSuggestionClick = (suggestion: string) => {
        if (suggestion === "고전 소설에 어울리는 술") {
            setIsClassicMode(true);
            addMessage("assistant", `고전 시나 소설 속 한 줄을 적어주시면, 그 분위기와 작가의 삶, 시대상을 헤아려 전통주를 골라드리겠슈 🍶\n\n예: "죽는 날까지 하늘을 우러러 한 점 부끄러움이 없기를"`);
        } else if (suggestion === "오늘 날씨에 맞는 술 추천해줘") {
            setIsClassicMode(false);
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        handleSendMessage(suggestion, {
                            lat: position.coords.latitude,
                            lon: position.coords.longitude
                        });
                    },
                    (error) => {
                        addMessage("assistant", "위치 정보를 알 수 없어서, 오늘 날씨에 딱 맞는 술을 추천해드릴 수가 없구만유. 😢");
                    }
                );
            } else {
                handleSendMessage(suggestion);
            }
        } else {
            setIsClassicMode(false);
            handleSendMessage(suggestion);
        }
    };

    const toggleChat = () => setIsOpen(!isOpen);

    const renderContent = () => (
        <div className={`${styles.panel} ${styles.open}`} ref={containerRef} style={{ height: '100%' }}>
            <div className={styles.header}>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                    <span className={styles.title}>주모</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <button
                        className={styles.lockButton}
                        onClick={() => setIsDraggable(!isDraggable)}
                        title={isDraggable ? '위치 고정' : '이동 가능'}
                        onMouseDown={(e) => e.stopPropagation()}
                    >
                        {isDraggable ? <Unlock size={18} /> : <Lock size={18} />}
                    </button>
                    <button className={styles.closeBtn} onClick={() => setIsOpen(false)} onMouseDown={(e) => e.stopPropagation()}>
                        ✕
                    </button>
                </div>
            </div>

            <div className={styles.content} style={{ position: 'relative' }}>
                {/* Auth overlay removed for anonymous access */}

                <div className={''} style={{ height: '100%' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', padding: '12px' }}>
                            {messages.map((msg) => (
                                <div key={msg.id} className={`${styles.messageRow} ${msg.role === "assistant" ? styles.botRow : styles.userRow}`}>
                                    {msg.role === "assistant" && (
                                        <div className={styles.avatar}>
                                            <Image src="/이리오너라.png" alt="주모" width={32} height={32} style={{ borderRadius: '50%' }} />
                                        </div>
                                    )}
                                    <div className={`${styles.bubble} ${msg.role === "assistant" ? styles.botBubble : styles.userBubble}`}>
                                        {msg.content.split('\n').map((line, i) => (
                                            <span key={i}>{line}<br /></span>
                                        ))}

                                        {/* Render Cocktail Card */}
                                        {msg.cocktailData?.cocktail && (
                                            <CocktailRecipeCard data={msg.cocktailData.cocktail} />
                                        )}

                                        {/* Render Recommended Drinks */}
                                        {msg.cocktailData?.drinks && msg.cocktailData.drinks.length > 0 && (
                                            <div className={styles.recommendations}>
                                                {msg.cocktailData.drinks.map((drink: any, idx: number) => (
                                                    <Link href={`/drink/${drink.id}`} key={idx} style={{ textDecoration: 'none', color: 'inherit' }}>
                                                        <div className={styles.drinkCard}>
                                                            {drink.image_url && (
                                                                <div className={styles.drinkImageWrapper}>
                                                                    <img src={drink.image_url} alt={drink.name} className={styles.drinkImage} />
                                                                </div>
                                                            )}
                                                            <div className={styles.drinkInfo}>
                                                                <div className={styles.drinkName}>{drink.name}</div>
                                                                <div className={styles.drinkMeta}>{drink.abv}% | {drink.volume}</div>
                                                            </div>
                                                        </div>
                                                    </Link>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                            {isLoading && (
                                <div className={`${styles.messageRow} ${styles.botRow}`}>
                                    <div className={styles.avatar}>
                                        <Image src="/이리오너라.png" alt="주모" width={32} height={32} style={{ borderRadius: '50%' }} />
                                    </div>
                                    <div className={`${styles.bubble} ${styles.botBubble}`}>
                                        <div className={styles.loadingDots}><span></span><span></span><span></span></div>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        <div className={styles.quickReplies}>
                            {suggestions.map((suggestion, index) => (
                                <button key={index} className={styles.quickReplyButton} onClick={() => handleSuggestionClick(suggestion)}>
                                    {suggestion}
                                </button>
                            ))}
                        </div>

                        <div className={styles.inputArea}>
                            <input
                                type="text"
                                className={styles.input}
                                placeholder="궁금한 술이 있소?"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => { if (e.key === 'Enter') handleSendMessage(); }}
                            />
                            <button className={styles.sendButton} onClick={() => handleSendMessage()}>➤</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );

    return (
        <>
            {isOpen && isMounted && (
                isDraggable ? (
                    <Rnd
                        default={{
                            x: typeof window !== 'undefined' ? window.innerWidth - 420 : 0,
                            y: typeof window !== 'undefined' ? window.innerHeight - 600 : 0,
                            width: 380,
                            height: 550,
                        }}
                        minWidth={300}
                        minHeight={400}
                        bounds="window"
                        dragHandleClassName={styles.header}
                        style={{ zIndex: 9999, position: 'fixed' }}
                        className="chatbot-main-window"
                        enableUserSelectHack={false}
                    >
                        {renderContent()}
                    </Rnd>
                ) : (
                    <div className={styles.fixedContainer}>{renderContent()}</div>
                )
            )}

            {!isOpen && (
                <div className={styles.container}>
                    <button className={styles.button} onClick={toggleChat}>
                        <Image src="/이리오너라.png" alt="이리오너라" width={54} height={54} style={{ borderRadius: '50%' }} />
                        <span>이리오너라~</span>
                    </button>
                </div>
            )}
        </>
    );
}
