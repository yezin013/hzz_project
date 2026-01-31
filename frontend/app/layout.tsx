import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

import Header from "./components/Header";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "한잔酒 HZZ 전통주 갤러리",
  description: "전통주를 한 곳에 우리 술의 맛과 멋을 찾아서",
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

import AuthProvider from "./components/SessionProvider";
import { ChatProvider } from "./context/ChatContext"; // Imported ChatProvider

// ... imports

import Chatbot from "./components/Chatbot";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preload" href="/maploading.mp4" as="video" type="video/mp4" />
      </head>
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        <AuthProvider>
          <ChatProvider>
            <Header
              cognitoDomain={process.env.NEXT_PUBLIC_COGNITO_DOMAIN}
              clientId={process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID}
            />
            {children}
            <Chatbot />
          </ChatProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
