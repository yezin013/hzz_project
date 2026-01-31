"use client";

import React, { createContext, useContext, useState, ReactNode, useEffect } from "react";

// Define message type
export interface ChatMessage {
    id: string; // Unique ID for key
    role: "user" | "assistant";
    content: string;
    timestamp: Date;
    isCocktail?: boolean; // Flag to render cocktail card
    cocktailData?: any;   // Data for cocktail card
}

interface ChatContextType {
    isOpen: boolean;
    setIsOpen: (open: boolean) => void;
    toggleChat: () => void;
    messages: ChatMessage[];
    addMessage: (role: "user" | "assistant", content: string, cocktailData?: any) => void;
    isLoading: boolean;
    setIsLoading: (loading: boolean) => void;
    input: string;
    setInput: (input: string) => void;
    clearHistory: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

const LOCAL_STORAGE_KEY = "jumak_chat_history";

export const ChatProvider = ({ children }: { children: ReactNode }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [input, setInput] = useState("");
    const [isInitialized, setIsInitialized] = useState(false);

    // Load history from localStorage on mount
    useEffect(() => {
        try {
            const saved = localStorage.getItem(LOCAL_STORAGE_KEY);
            if (saved) {
                const parsed = JSON.parse(saved);
                // Convert timestamp strings back to Date objects
                const hydrated = parsed.map((msg: any) => ({
                    ...msg,
                    timestamp: new Date(msg.timestamp),
                }));
                setMessages(hydrated);
            } else {
                // Initial greeting if no history
                setMessages([
                    {
                        id: "init-1",
                        role: "assistant",
                        content: "어서오시오! 주모 챗봇이오. 오늘 기분이나 날씨에 맞는 술을 추천해 드리리다.",
                        timestamp: new Date(),
                    },
                ]);
            }
        } catch (e) {
            console.error("Failed to load chat history", e);
        }
        setIsInitialized(true);
    }, []);

    // Save to localStorage whenever messages change
    useEffect(() => {
        if (isInitialized) {
            localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(messages));
        }
    }, [messages, isInitialized]);

    const toggleChat = () => setIsOpen((prev) => !prev);

    const addMessage = (role: "user" | "assistant", content: string, cocktailData?: any) => {
        const newMessage: ChatMessage = {
            id: Date.now().toString(),
            role,
            content,
            timestamp: new Date(),
            isCocktail: !!cocktailData,
            cocktailData,
        };
        setMessages((prev) => [...prev, newMessage]);
    };

    const clearHistory = () => {
        setMessages([
            {
                id: Date.now().toString(),
                role: "assistant",
                content: "대화 내역을 비웠소. 다시 말씀해 주시오.",
                timestamp: new Date(),
            },
        ]);
        localStorage.removeItem(LOCAL_STORAGE_KEY);
    };

    return (
        <ChatContext.Provider
            value={{
                isOpen,
                setIsOpen,
                toggleChat,
                messages,
                addMessage,
                isLoading,
                setIsLoading,
                input,
                setInput,
                clearHistory,
            }}
        >
            {children}
        </ChatContext.Provider>
    );
};

export const useChat = () => {
    const context = useContext(ChatContext);
    if (context === undefined) {
        throw new Error("useChat must be used within a ChatProvider");
    }
    return context;
};
