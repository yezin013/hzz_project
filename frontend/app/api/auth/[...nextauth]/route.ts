import NextAuth from "next-auth";
import CognitoProvider from "next-auth/providers/cognito";

// Amplify SSR에서 환경변수가 런타임에 전달되지 않는 문제 대응
// 여러 환경변수명을 시도하고, 없으면 에러 방지용 기본값 사용
const getSecret = () => {
    const secret = process.env.NEXTAUTH_SECRET
        || process.env.AUTH_SECRET
        || process.env.SECRET;

    if (!secret) {
        console.error("[NextAuth] WARNING: No secret found in environment variables");
        return "temporary-secret-for-amplify-ssr-debugging";
    }
    return secret;
};

// 🛡️ [CRITICAL FIX] Amplify SSR에서 환경변수 유실시 localhost로 잡히는 문제 강제 수정
// 🛡️ [SECURE FIX] Force HTTPS for the main domain to prevent "Not Secure" warnings
if (process.env.NODE_ENV === 'production' && !process.env.NEXTAUTH_URL) {
    console.log("[NextAuth] NEXTAUTH_URL missing. Forcing SECURE default:");
    process.env.NEXTAUTH_URL = "https://hanzanzu.cloud";
}

// Debug: Log environment variables at startup
console.log("[NextAuth] Environment check:", {
    hasSecret: !!process.env.NEXTAUTH_SECRET,
    hasAuthSecret: !!process.env.AUTH_SECRET,
    secretLength: process.env.NEXTAUTH_SECRET?.length || 0,
    hasClientId: !!(process.env.COGNITO_CLIENT_ID || process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID),
    hasIssuer: !!process.env.COGNITO_ISSUER,
    nodeEnv: process.env.NODE_ENV,
});

const handler = NextAuth({
    secret: getSecret(),
    providers: [
        CognitoProvider({
            clientId: process.env.COGNITO_CLIENT_ID ?? process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID ?? "",
            clientSecret: "", // Required by type, but empty for Public Client
            client: {
                token_endpoint_auth_method: "none",
            },
            issuer: process.env.COGNITO_ISSUER ?? "",
            checks: ["state", "nonce"],
            authorization: {
                params: {
                    // Show both Google and Cognito User Pool login options
                    // 빈 값으로 두면 Cognito가 설정된 모든 IdP를 보여줌
                    identity_provider: undefined,
                    // 또는 명시적으로: "COGNITO,Google"
                }
            },
        }),
    ],
    session: {
        strategy: "jwt",
        maxAge: 30 * 24 * 60 * 60, // 30 days
    },
    callbacks: {
        async jwt({ token, account, profile }) {
            // Save user info from profile to token
            if (account && profile) {
                token.sub = profile.sub;
                token.email = profile.email;
                token.name = profile.name || profile.email?.split('@')[0];
            }
            return token;
        },
        async session({ session, token }) {
            // Pass user info from token to session
            if (token) {
                session.user = {
                    ...session.user,
                    email: token.email as string,
                    name: token.name as string,
                };
            }
            return session;
        },
        async redirect({ url, baseUrl }) {
            // Redirect to home page after successful login
            // If url starts with baseUrl, use it (allows callbackUrl to work)
            if (url.startsWith(baseUrl)) return url;
            // If url is a relative path, prepend baseUrl
            if (url.startsWith("/")) return baseUrl + url;
            // Default to home page
            return baseUrl;
        },
    },
    events: {
        async signOut({ token }) {
            // Session cleared, Cognito logout handled in redirect callback
            console.log("User signed out:", token?.email);
        },
    },
    debug: true,
    // @ts-ignore: NextAuth v4 타입 정의에 trustHost가 누락될 수 있으나 실제로는 지원됨
    trustHost: true, // Amplify/Vercel 환경에서 필수: 요청 헤더의 Host를 신뢰하여 URL 구성
});

export { handler as GET, handler as POST };
